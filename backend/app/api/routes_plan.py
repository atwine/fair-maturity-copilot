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

from uuid import UUID

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
    indicators_by_id = {
        i.id: i
        for i in (
            session.exec(select(Indicator).where(Indicator.id.in_({link.indicator_id for link in links}))).all()
            if links
            else []
        )
    }
    links_by_step: dict[UUID, list[PlanStepIndicator]] = {}
    for link in links:
        links_by_step.setdefault(link.plan_step_id, []).append(link)

    return PlanOut(
        run_id=run_id,
        goal=plan.goal,
        steps=[
            PlanStepOut(
                id=step.id,
                title=step.title,
                detail=step.detail,
                indicators=[
                    PlanIndicatorRefOut(
                        indicator_id=link.indicator_id,
                        title=indicators_by_id[link.indicator_id].title,
                        principle_group=indicators_by_id[link.indicator_id].principle_group,
                    )
                    for link in links_by_step.get(step.id, [])
                ],
            )
            for step in steps
        ],
    )


def _save_new_plan(session: Session, run_id: UUID, built_plan: BuiltPlan) -> PlanRow:
    """Always inserts a new Plan version -- never overwrites or deletes an
    older one. See the module docstring for why: an existing mentor
    conversation's plan_step_id has to keep resolving to a real row."""
    plan_row = PlanRow(run_id=run_id, goal=built_plan.goal)
    session.add(plan_row)
    session.commit()
    session.refresh(plan_row)

    for order, step in enumerate(built_plan.steps):
        step_row = PlanStep(plan_id=plan_row.id, display_order=order, title=step.title, detail=step.detail)
        session.add(step_row)
        session.commit()
        session.refresh(step_row)
        for indicator_id in step.indicator_ids:
            session.add(PlanStepIndicator(plan_step_id=step_row.id, indicator_id=indicator_id))
    session.commit()
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
