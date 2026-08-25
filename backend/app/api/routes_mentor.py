"""Checkpoint 9 POC: an over-the-shoulder mentor, scoped to one plan step's
indicator at a time. Capability is deliberately "tool-using, not verifying"
(docs/DECISIONS.md v19) -- confirming a fix in chat calls straight into the
existing answer-update/rescore path (routes_answers.upsert_answer), the same
machinery the report's "Update your answer" action already uses, rather than
duplicating it or reaching out to check anything externally.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.adapters.registry import get_adapter
from app.api.routes_answers import upsert_answer
from app.api.schemas import (
    AnswerIn,
    MentorActionOut,
    MentorConversationOut,
    MentorMessageIn,
    MentorMessageOut,
    MentorReplyOut,
    MentorStartRequest,
)
from app.db import get_session
from app.engine.mentor import run_mentor_turn
from app.engine.models import AssessmentRun, Answer, Finding, Indicator, MentorConversation, MentorMessage, Report

router = APIRouter(prefix="/assessments", tags=["mentor"])

_VALID_SKILL_LEVELS = {"new_to_this", "done_this_before"}


def _get_run_and_indicator(session: Session, run_id: UUID, indicator_id: str) -> tuple[AssessmentRun, Indicator]:
    run = session.get(AssessmentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if run.status != "completed":
        raise HTTPException(
            status_code=400, detail="The mentor is only available once an assessment is completed and reported."
        )
    indicator = session.get(Indicator, indicator_id)
    if indicator is None:
        raise HTTPException(status_code=404, detail=f"Unknown indicator: {indicator_id!r}")
    return run, indicator


def _get_conversation(session: Session, run_id: UUID, indicator_id: str) -> MentorConversation | None:
    return session.exec(
        select(MentorConversation).where(
            MentorConversation.run_id == run_id, MentorConversation.indicator_id == indicator_id
        )
    ).first()


def _current_severity(session: Session, run_id: UUID, indicator_id: str) -> str:
    finding = session.exec(
        select(Finding).where(Finding.run_id == run_id, Finding.indicator_id == indicator_id)
    ).first()
    return finding.severity if finding is not None else "unknown"


def _current_answer(session: Session, run_id: UUID, indicator_id: str) -> Answer | None:
    """The user's existing answer for this indicator, if any -- passed into
    the mentor's system prompt so it knows where they currently stand (value
    + their own note), not just the derived severity label."""
    return session.exec(
        select(Answer).where(Answer.run_id == run_id, Answer.indicator_id == indicator_id)
    ).first()


def _label_for_value(run: AssessmentRun, indicator_id: str, value: str) -> str:
    adapter = get_adapter(run.adapter_id)
    for question in adapter.question_set():
        if question.indicator.id == indicator_id:
            for option in question.options:
                if option["value"] == value:
                    return str(option["label"])
    return value.replace("_", " ").capitalize()


@router.post("/{run_id}/mentor/{indicator_id}/start", response_model=MentorConversationOut)
def start_conversation(
    run_id: UUID, indicator_id: str, body: MentorStartRequest, session: Session = Depends(get_session)
) -> MentorConversationOut:
    run, indicator = _get_run_and_indicator(session, run_id, indicator_id)

    existing = _get_conversation(session, run_id, indicator_id)
    if existing is not None:
        messages = session.exec(
            select(MentorMessage)
            .where(MentorMessage.conversation_id == existing.id)
            .order_by(MentorMessage.created_at)
        ).all()
        return MentorConversationOut(
            indicator_id=indicator_id,
            skill_level=existing.skill_level,
            messages=[MentorMessageOut(role=m.role, content=m.content, created_at=m.created_at) for m in messages],
        )

    if body.skill_level not in _VALID_SKILL_LEVELS:
        raise HTTPException(status_code=422, detail=f"skill_level must be one of {sorted(_VALID_SKILL_LEVELS)}")

    conversation = MentorConversation(run_id=run_id, indicator_id=indicator_id, skill_level=body.skill_level)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    adapter = get_adapter(run.adapter_id)
    severity = _current_severity(session, run_id, indicator_id)
    current_answer = _current_answer(session, run_id, indicator_id)
    system_prompt = adapter.render_mentor_system_prompt(
        indicator=indicator,
        subject_label=run.subject_label,
        skill_level=body.skill_level,
        severity=severity,
        current_answer=current_answer,
    )
    opening_text, _ = run_mentor_turn(
        system_prompt=system_prompt,
        history=[],
        user_text="(The person just opened this chat. Greet them briefly and invite them to describe where they are with this indicator.)",
    )
    opening_message = MentorMessage(conversation_id=conversation.id, role="mentor", content=opening_text)
    session.add(opening_message)
    session.commit()

    return MentorConversationOut(
        indicator_id=indicator_id,
        skill_level=conversation.skill_level,
        messages=[MentorMessageOut(role="mentor", content=opening_text, created_at=opening_message.created_at)],
    )


@router.get("/{run_id}/mentor/{indicator_id}", response_model=MentorConversationOut)
def get_conversation(run_id: UUID, indicator_id: str, session: Session = Depends(get_session)) -> MentorConversationOut:
    _get_run_and_indicator(session, run_id, indicator_id)
    conversation = _get_conversation(session, run_id, indicator_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="No mentor conversation started yet for this indicator")

    messages = session.exec(
        select(MentorMessage).where(MentorMessage.conversation_id == conversation.id).order_by(MentorMessage.created_at)
    ).all()
    return MentorConversationOut(
        indicator_id=indicator_id,
        skill_level=conversation.skill_level,
        messages=[MentorMessageOut(role=m.role, content=m.content, created_at=m.created_at) for m in messages],
    )


@router.post("/{run_id}/mentor/{indicator_id}/messages", response_model=MentorReplyOut)
def send_message(
    run_id: UUID, indicator_id: str, body: MentorMessageIn, session: Session = Depends(get_session)
) -> MentorReplyOut:
    run, indicator = _get_run_and_indicator(session, run_id, indicator_id)
    conversation = _get_conversation(session, run_id, indicator_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Start a mentor conversation before sending messages")

    history = session.exec(
        select(MentorMessage).where(MentorMessage.conversation_id == conversation.id).order_by(MentorMessage.created_at)
    ).all()

    user_message = MentorMessage(conversation_id=conversation.id, role="user", content=body.content)
    session.add(user_message)
    session.commit()

    adapter = get_adapter(run.adapter_id)
    severity = _current_severity(session, run_id, indicator_id)
    current_answer = _current_answer(session, run_id, indicator_id)
    system_prompt = adapter.render_mentor_system_prompt(
        indicator=indicator,
        subject_label=run.subject_label,
        skill_level=conversation.skill_level,
        severity=severity,
        current_answer=current_answer,
    )
    display_text, action = run_mentor_turn(system_prompt=system_prompt, history=history, user_text=body.content)

    mentor_message = MentorMessage(conversation_id=conversation.id, role="mentor", content=display_text)
    session.add(mentor_message)
    conversation.updated_at = mentor_message.created_at
    session.add(conversation)
    session.commit()
    session.refresh(mentor_message)

    action_out: MentorActionOut | None = None
    if action is not None:
        label = _label_for_value(run, indicator_id, action.value)
        # Reuses the exact machinery routes_answers.py's PUT endpoint already
        # uses for a revisit from the report -- this is the "tool-using"
        # capability from docs/DECISIONS.md v19, not a duplicated code path.
        upsert_answer(run_id, indicator_id, AnswerIn(value=action.value, label=label, note=action.note), session)

        new_finding = session.exec(
            select(Finding).where(Finding.run_id == run_id, Finding.indicator_id == indicator_id)
        ).first()
        report = session.exec(select(Report).where(Report.run_id == run_id)).first()
        if new_finding is not None and report is not None:
            action_out = MentorActionOut(
                indicator_id=indicator_id,
                new_value=action.value,
                new_severity=new_finding.severity,
                new_score=report.summary_score,
            )

    return MentorReplyOut(
        mentor_message=MentorMessageOut(
            role="mentor", content=mentor_message.content, created_at=mentor_message.created_at
        ),
        action_taken=action_out,
    )
