from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.adapters.registry import get_adapter
from app.api.routes_report import _rescore_finding_and_refresh_report
from app.api.schemas import AnswerIn, AnswerOut
from app.db import get_session
from app.engine.models import Answer, AssessmentRun

router = APIRouter(prefix="/assessments", tags=["answers"])

_VALID_VALUES = {"yes", "partial", "no", "dont_know"}


@router.put("/{run_id}/answers/{indicator_id}", response_model=AnswerOut)
def upsert_answer(
    run_id: UUID, indicator_id: str, body: AnswerIn, session: Session = Depends(get_session)
) -> AnswerOut:
    run = session.get(AssessmentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    # Editing an answer after completion is how revisiting a finding from
    # the report works (see _rescore_finding_and_refresh_report below) --
    # no longer blocked. What used to be a one-shot linear flow is now one
    # a person can come back to.
    if body.value not in _VALID_VALUES:
        raise HTTPException(status_code=422, detail=f"value must be one of {sorted(_VALID_VALUES)}")

    adapter = get_adapter(run.adapter_id)
    valid_indicator_ids = {q.indicator.id for q in adapter.question_set()}
    if indicator_id not in valid_indicator_ids:
        raise HTTPException(status_code=404, detail=f"Unknown indicator for this adapter: {indicator_id!r}")

    is_dont_know = body.value == "dont_know"
    existing = session.exec(
        select(Answer).where(Answer.run_id == run_id, Answer.indicator_id == indicator_id)
    ).first()

    if existing is not None:
        existing.raw_answer = {"value": body.value, "label": body.label}
        existing.free_text_note = body.note
        existing.is_dont_know = is_dont_know
        session.add(existing)
        session.commit()
        session.refresh(existing)
        saved_answer = existing
    else:
        # Two concurrent PUTs for the same (run_id, indicator_id) can both
        # reach here having seen "no existing answer" — the unique
        # constraint on Answer lets only one INSERT win. The loser rolls
        # back and updates the winner's row instead of erroring, so a
        # double-fired submit (a slow network + an impatient double-click,
        # or React re-invoking an effect) still ends up with one consistent
        # answer rather than a 500 or a duplicate row.
        new_answer = Answer(
            run_id=run_id,
            indicator_id=indicator_id,
            raw_answer={"value": body.value, "label": body.label},
            free_text_note=body.note,
            is_dont_know=is_dont_know,
        )
        try:
            session.add(new_answer)
            session.commit()
            session.refresh(new_answer)
            saved_answer = new_answer
        except IntegrityError:
            session.rollback()
            winner = session.exec(
                select(Answer).where(Answer.run_id == run_id, Answer.indicator_id == indicator_id)
            ).one()
            winner.raw_answer = {"value": body.value, "label": body.label}
            winner.free_text_note = body.note
            winner.is_dont_know = is_dont_know
            session.add(winner)
            session.commit()
            session.refresh(winner)
            saved_answer = winner

    if run.status == "completed":
        # A revisit -- the run already has a report, so keep it honest
        # instead of leaving it showing a stale severity/remediation for
        # the indicator that just changed.
        _rescore_finding_and_refresh_report(session, run, indicator_id, saved_answer)

    return AnswerOut(
        indicator_id=indicator_id, value=body.value, label=body.label, note=body.note, is_dont_know=is_dont_know
    )
