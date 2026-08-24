from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.adapters.registry import get_adapter
from app.api.schemas import AssessmentOut, CreateAssessmentRequest
from app.db import get_session
from app.engine.models import Answer, AssessmentRun

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _to_out(run: AssessmentRun, answered_indicator_ids: list[str]) -> AssessmentOut:
    return AssessmentOut(
        id=run.id,
        adapter_id=run.adapter_id,
        subject_label=run.subject_label,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        answered_indicator_ids=answered_indicator_ids,
    )


@router.post("", response_model=AssessmentOut, status_code=201)
def create_assessment(body: CreateAssessmentRequest, session: Session = Depends(get_session)) -> AssessmentOut:
    try:
        get_adapter(body.adapter_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown adapter: {body.adapter_id!r}")

    run = AssessmentRun(
        adapter_id=body.adapter_id,
        subject_label=body.subject_label,
        created_by_email=body.created_by_email,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return _to_out(run, [])


@router.get("/{run_id}", response_model=AssessmentOut)
def get_assessment(run_id: UUID, session: Session = Depends(get_session)) -> AssessmentOut:
    run = session.get(AssessmentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    answers = session.exec(select(Answer).where(Answer.run_id == run_id)).all()
    return _to_out(run, [a.indicator_id for a in answers])


@router.post("/{run_id}/complete", response_model=AssessmentOut)
def complete_assessment(run_id: UUID, session: Session = Depends(get_session)) -> AssessmentOut:
    run = session.get(AssessmentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if run.status == "completed":
        raise HTTPException(status_code=400, detail="Assessment is already completed")

    adapter = get_adapter(run.adapter_id)
    required_ids = {q.indicator.id for q in adapter.question_set()}
    answers = session.exec(select(Answer).where(Answer.run_id == run_id)).all()
    answered_ids = {a.indicator_id for a in answers}

    missing = sorted(required_ids - answered_ids)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing answers for: {missing}")

    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    session.add(run)
    session.commit()
    session.refresh(run)
    return _to_out(run, sorted(answered_ids))
