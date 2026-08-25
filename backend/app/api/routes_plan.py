"""The FAIRification plan: a single ordered walkthrough synthesized from all
of a run's open findings, distinct from the per-finding remediation on the
report. Cached (issue #9 / docs/DECISIONS.md): a Plan is saved the first
time it's built, and every later GET returns the saved version -- no LLM
call -- until AssessmentRun.plan_stale flips back to True (set wherever an
answer changes on a completed run, see routes_answers.py). A step's id is
what a mentor chat is scoped to (routes_mentor.py), so it has to survive
between visits; regenerating never deletes an older Plan's steps, it just
saves a new version alongside it, so an existing mentor conversation is
never left pointing at a row that's gone.
"""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.adapters.fair.plan import Plan as BuiltPlan
from app.adapters.fair.plan import PlanGenerationFailed, build_fairification_plan
from app.api.schemas import PlanIndicatorRefOut, PlanOut, PlanStepOut
from app.db import get_session
from app.engine.models import AssessmentRun, Finding, Indicator
from app.engine.models import Plan as PlanRow
from app.engine.models import PlanStep, PlanStepIndicator

router = APIRouter(prefix="/assessments", tags=["plan"])


def _latest_plan(session: Session, run_id: UUID) -> PlanRow | None:
    return session.exec(
        select(PlanRow).where(PlanRow.run_id == run_id).order_by(PlanRow.generated_at.desc())
    ).first()


def _load_plan_out(session: Session, run_id: UUID, plan: PlanRow) -> PlanOut:
    steps = session.exec(
        select(PlanStep).where(PlanStep.plan_id == plan.id).order_by(PlanStep.display_order)
    ).all()
    step_ids = [s.id for s in steps]
    links = (
        session.exec(select(PlanStepIndicator).where(PlanStepIndicator.plan_step_id.in_(step_ids))).all()
        if step_ids
        else []
    )
    # Ordered by the indicator's own canonical display_order (not left to
    # whatever order Postgres happens to return) so a step's indicator list
    # renders in a stable order across visits, matching what the mentor
    # prompt numbers them in (routes_mentor.py).
    indicators_by_id = {
        i.id: i
        for i in (
            session.exec(
                select(Indicator).where(Indicator.id.in_({link.indicator_id for link in links})).order_by(Indicator.display_order)
            ).all()
            if links
            else []
        )
    }
    links_by_step: dict[UUID, list[PlanStepIndicator]] = {}
    for link in links:
        links_by_step.setdefault(link.plan_step_id, []).append(link)

    steps_out = []
    for step in steps:
        indicator_refs = []
        for link in links_by_step.get(step.id, []):
            indicator = indicators_by_id.get(link.indicator_id)
            if indicator is None:
                # A saved plan can outlive the Indicator content it was
                # built from (e.g. indicators.yaml drops or renames an id
                # after this version was saved) -- surface a clear error
                # naming the cause rather than an opaque KeyError, same
                # spirit as routes_report.py's missing-indicator guard.
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Saved plan step {step.id} references indicator {link.indicator_id!r}, which no longer "
                        "exists. Has indicators.yaml changed since this plan was generated?"
                    ),
                )
            indicator_refs.append(
                PlanIndicatorRefOut(
                    indicator_id=link.indicator_id, title=indicator.title, principle_group=indicator.principle_group
                )
            )
        steps_out.append(PlanStepOut(id=step.id, title=step.title, detail=step.detail, indicators=indicator_refs))

    return PlanOut(run_id=run_id, goal=plan.goal, steps=steps_out)


def _save_new_plan(session: Session, run_id: UUID, built_plan: BuiltPlan) -> PlanRow:
    """Always inserts a new Plan version -- never overwrites or deletes an
    older one. See the module docstring for why: an existing mentor
    conversation's plan_step_id has to keep resolving to a real row.

    Ids are generated client-side (uuid4, same default the models already
    use) so every row for this version can be built and added in memory and
    committed exactly once -- not once per step, which meant a real plan
    (several steps) cost several extra round trips to a Postgres instance
    this project's own notes already flag as latency-sensitive (Neon
    scale-to-zero), on the exact request this caching feature exists to
    make fast."""
    plan_row = PlanRow(id=uuid4(), run_id=run_id, goal=built_plan.goal)
    session.add(plan_row)

    for order, step in enumerate(built_plan.steps):
        step_row = PlanStep(id=uuid4(), plan_id=plan_row.id, display_order=order, title=step.title, detail=step.detail)
        session.add(step_row)
        for indicator_id in step.indicator_ids:
            session.add(PlanStepIndicator(plan_step_id=step_row.id, indicator_id=indicator_id))
    session.commit()
    session.refresh(plan_row)
    return plan_row


@router.get("/{run_id}/plan", response_model=PlanOut)
def get_plan(run_id: UUID, session: Session = Depends(get_session)) -> PlanOut:
    run = session.get(AssessmentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if run.status != "completed":
        raise HTTPException(status_code=400, detail="Assessment must be completed before a plan can be generated")

    existing = _latest_plan(session, run_id)
    if existing is not None and not run.plan_stale:
        return _load_plan_out(session, run_id, existing)

    findings = session.exec(select(Finding).where(Finding.run_id == run_id)).all()
    if not findings:
        raise HTTPException(
            status_code=400,
            detail="No findings yet for this assessment -- view the report first to generate them.",
        )

    indicators = session.exec(
        select(Indicator).where(Indicator.id.in_({f.indicator_id for f in findings}))
    ).all()
    indicators_by_id = {i.id: i for i in indicators}

    try:
        built_plan = build_fairification_plan(
            findings=findings, indicators_by_id=indicators_by_id, subject_label=run.subject_label
        )
    except PlanGenerationFailed:
        raise HTTPException(
            status_code=503,
            detail="Couldn't build a plan from the model's response this time -- try again in a moment.",
        )

    if not built_plan.steps:
        # This branch never calls the LLM (build_fairification_plan
        # short-circuits when there are no open findings), so there's
        # nothing worth persisting -- just hand back the "all clean"
        # response. plan_stale is deliberately left as-is: if it flips back
        # to True later (a revisit reopens a gap), this same cheap check
        # runs again rather than needing its own cache entry.
        return PlanOut(run_id=run_id, goal=built_plan.goal, steps=[])

    saved = _save_new_plan(session, run_id, built_plan)
    run.plan_stale = False
    session.add(run)
    session.commit()

    return _load_plan_out(session, run_id, saved)
