"""The FAIRification plan: a single ordered walkthrough synthesized from all
of a run's open findings, distinct from the per-finding remediation on the
report. Not cached (unlike the report) -- it's one LLM call regardless of
how many findings are open, so regenerating on every GET is simple and cheap
enough that the report's generate-once-cache-forever complexity isn't worth
carrying over here.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.adapters.fair.plan import PlanGenerationFailed, build_fairification_plan
from app.api.schemas import PlanIndicatorRefOut, PlanOut, PlanStepOut
from app.db import get_session
from app.engine.models import AssessmentRun, Finding, Indicator

router = APIRouter(prefix="/assessments", tags=["plan"])


@router.get("/{run_id}/plan", response_model=PlanOut)
def get_plan(run_id: UUID, session: Session = Depends(get_session)) -> PlanOut:
    run = session.get(AssessmentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if run.status != "completed":
        raise HTTPException(status_code=400, detail="Assessment must be completed before a plan can be generated")

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
        plan = build_fairification_plan(findings=findings, indicators_by_id=indicators_by_id, subject_label=run.subject_label)
    except PlanGenerationFailed:
        raise HTTPException(
            status_code=503,
            detail="Couldn't build a plan from the model's response this time -- try again in a moment.",
        )

    return PlanOut(
        run_id=run_id,
        goal=plan.goal,
        steps=[
            PlanStepOut(
                title=s.title,
                detail=s.detail,
                indicators=[
                    PlanIndicatorRefOut(
                        indicator_id=iid,
                        title=indicators_by_id[iid].title,
                        principle_group=indicators_by_id[iid].principle_group,
                    )
                    for iid in s.indicator_ids
                ],
            )
            for s in plan.steps
        ],
    )
