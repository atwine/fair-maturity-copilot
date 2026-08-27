"""Checkpoint 9 / issue #9: an over-the-shoulder mentor, scoped to one
FAIRification plan step -- which can bundle several indicators -- rather
than one indicator at a time. Capability is deliberately "tool-using, not
verifying" (docs/DECISIONS.md v19) -- confirming a fix in chat calls
straight into the existing answer-update/rescore path
(routes_answers.upsert_answer), the same machinery the report's "Update
your answer" action already uses, rather than duplicating it or reaching
out to check anything externally.
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
    PlanIndicatorRefOut,
)
from app.db import get_session
from app.engine.mentor import run_mentor_turn
from app.engine.models import (
    Answer,
    AssessmentRun,
    Finding,
    Indicator,
    MentorConversation,
    MentorMessage,
    Plan,
    PlanStep,
    PlanStepIndicator,
    Report,
)
from app.engine.ports import MentorIndicatorContext

router = APIRouter(prefix="/assessments", tags=["mentor"])

_VALID_SKILL_LEVELS = {"new_to_this", "done_this_before"}


def _get_run_and_step(session: Session, run_id: UUID, step_id: UUID) -> tuple[AssessmentRun, PlanStep, list[Indicator]]:
    run = session.get(AssessmentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if run.status != "completed":
        raise HTTPException(
            status_code=400, detail="The mentor is only available once an assessment is completed and reported."
        )

    step = session.get(PlanStep, step_id)
    if step is None:
        raise HTTPException(status_code=404, detail=f"Unknown plan step: {step_id}")
    plan = session.get(Plan, step.plan_id)
    if plan is None or plan.run_id != run_id:
        raise HTTPException(status_code=404, detail="That plan step doesn't belong to this assessment")

    links = session.exec(select(PlanStepIndicator).where(PlanStepIndicator.plan_step_id == step_id)).all()
    # Ordered by the indicator's own canonical display_order, not left to
    # whatever order Postgres happens to return -- the mentor prompt numbers
    # these ("1. ... 2. ...") and that numbering has to be stable across
    # requests, not shuffle between the opening turn and a later one.
    indicators = session.exec(
        select(Indicator).where(Indicator.id.in_({link.indicator_id for link in links})).order_by(Indicator.display_order)
    ).all()
    if not indicators:
        raise HTTPException(status_code=500, detail="This plan step has no indicators attached")
    if len(indicators) != len(links):
        # A saved step can outlive the Indicator content it references (see
        # the matching guard in routes_plan.py's _load_plan_out) -- fail
        # loudly instead of silently briefing the mentor on fewer
        # indicators than the step actually covers.
        missing = {link.indicator_id for link in links} - {i.id for i in indicators}
        raise HTTPException(
            status_code=500,
            detail=f"This plan step references indicators that no longer exist: {sorted(missing)}",
        )

    return run, step, list(indicators)


def _get_conversation(session: Session, run_id: UUID, step_id: UUID) -> MentorConversation | None:
    return session.exec(
        select(MentorConversation).where(
            MentorConversation.run_id == run_id, MentorConversation.plan_step_id == step_id
        )
    ).first()


def _severity_by_indicator_id(session: Session, run_id: UUID, indicator_ids: set[str]) -> dict[str, str]:
    findings = session.exec(
        select(Finding).where(Finding.run_id == run_id, Finding.indicator_id.in_(indicator_ids))
    ).all()
    by_id = {f.indicator_id: f.severity for f in findings}
    return {iid: by_id.get(iid, "unknown") for iid in indicator_ids}


def _answers_by_indicator_id(session: Session, run_id: UUID, indicator_ids: set[str]) -> dict[str, Answer]:
    answers = session.exec(
        select(Answer).where(Answer.run_id == run_id, Answer.indicator_id.in_(indicator_ids))
    ).all()
    return {a.indicator_id: a for a in answers}


def _build_indicator_contexts(session: Session, run_id: UUID, indicators: list[Indicator]) -> list[MentorIndicatorContext]:
    ids = {i.id for i in indicators}
    severities = _severity_by_indicator_id(session, run_id, ids)
    answers = _answers_by_indicator_id(session, run_id, ids)
    return [
        MentorIndicatorContext(indicator=i, severity=severities[i.id], current_answer=answers.get(i.id))
        for i in indicators
    ]


def _label_for_value(run: AssessmentRun, indicator_id: str, value: str) -> str:
    adapter = get_adapter(run.adapter_id)
    for question in adapter.question_set():
        if question.indicator.id == indicator_id:
            for option in question.options:
                if option["value"] == value:
                    return str(option["label"])
    return value.replace("_", " ").capitalize()


def _indicator_refs_out(indicators: list[Indicator]) -> list[PlanIndicatorRefOut]:
    return [
        PlanIndicatorRefOut(indicator_id=i.id, title=i.title, principle_group=i.principle_group) for i in indicators
    ]


@router.post("/{run_id}/mentor/step/{step_id}/start", response_model=MentorConversationOut)
def start_conversation(
    run_id: UUID, step_id: UUID, body: MentorStartRequest, session: Session = Depends(get_session)
) -> MentorConversationOut:
    run, step, indicators = _get_run_and_step(session, run_id, step_id)
    indicator_refs = _indicator_refs_out(indicators)

    existing = _get_conversation(session, run_id, step_id)
    if existing is not None:
        messages = session.exec(
            select(MentorMessage)
            .where(MentorMessage.conversation_id == existing.id)
            .order_by(MentorMessage.created_at)
        ).all()
        return MentorConversationOut(
            step_id=step_id,
            skill_level=existing.skill_level,
            indicators=indicator_refs,
            messages=[MentorMessageOut(role=m.role, content=m.content, created_at=m.created_at) for m in messages],
        )

    if body.skill_level not in _VALID_SKILL_LEVELS:
        raise HTTPException(status_code=422, detail=f"skill_level must be one of {sorted(_VALID_SKILL_LEVELS)}")

    conversation = MentorConversation(run_id=run_id, plan_step_id=step_id, skill_level=body.skill_level)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    adapter = get_adapter(run.adapter_id)
    contexts = _build_indicator_contexts(session, run_id, indicators)
    system_prompt = adapter.render_mentor_system_prompt(
        step_title=step.title,
        step_detail=step.detail,
        indicators=contexts,
        subject_label=run.subject_label,
        skill_level=body.skill_level,
    )
    opening_text, _ = run_mentor_turn(
        system_prompt=system_prompt,
        history=[],
        user_text="(The person just opened this chat. Greet them briefly and invite them to describe where they are.)",
        valid_indicator_ids={i.id for i in indicators},
        allow_tool_call=False,
    )
    opening_message = MentorMessage(conversation_id=conversation.id, role="mentor", content=opening_text)
    session.add(opening_message)
    session.commit()

    return MentorConversationOut(
        step_id=step_id,
        skill_level=conversation.skill_level,
        indicators=indicator_refs,
        messages=[MentorMessageOut(role="mentor", content=opening_text, created_at=opening_message.created_at)],
    )


@router.get("/{run_id}/mentor/step/{step_id}", response_model=MentorConversationOut)
def get_conversation(run_id: UUID, step_id: UUID, session: Session = Depends(get_session)) -> MentorConversationOut:
    _, _, indicators = _get_run_and_step(session, run_id, step_id)
    conversation = _get_conversation(session, run_id, step_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="No mentor conversation started yet for this step")

    messages = session.exec(
        select(MentorMessage).where(MentorMessage.conversation_id == conversation.id).order_by(MentorMessage.created_at)
    ).all()
    return MentorConversationOut(
        step_id=step_id,
        skill_level=conversation.skill_level,
        indicators=_indicator_refs_out(indicators),
        messages=[MentorMessageOut(role=m.role, content=m.content, created_at=m.created_at) for m in messages],
    )


@router.post("/{run_id}/mentor/step/{step_id}/messages", response_model=MentorReplyOut)
def send_message(
    run_id: UUID, step_id: UUID, body: MentorMessageIn, session: Session = Depends(get_session)
) -> MentorReplyOut:
    run, step, indicators = _get_run_and_step(session, run_id, step_id)
    conversation = _get_conversation(session, run_id, step_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Start a mentor conversation before sending messages")

    history = session.exec(
        select(MentorMessage).where(MentorMessage.conversation_id == conversation.id).order_by(MentorMessage.created_at)
    ).all()

    user_message = MentorMessage(conversation_id=conversation.id, role="user", content=body.content)
    session.add(user_message)
    session.commit()

    adapter = get_adapter(run.adapter_id)
    contexts = _build_indicator_contexts(session, run_id, indicators)
    system_prompt = adapter.render_mentor_system_prompt(
        step_title=step.title,
        step_detail=step.detail,
        indicators=contexts,
        subject_label=run.subject_label,
        skill_level=conversation.skill_level,
    )
    display_text, action = run_mentor_turn(
        system_prompt=system_prompt,
        history=history,
        user_text=body.content,
        valid_indicator_ids={i.id for i in indicators},
    )

    mentor_message = MentorMessage(conversation_id=conversation.id, role="mentor", content=display_text)
    session.add(mentor_message)
    conversation.updated_at = mentor_message.created_at
    session.add(conversation)
    session.commit()
    session.refresh(mentor_message)

    action_out: MentorActionOut | None = None
    if action is not None:
        label = _label_for_value(run, action.indicator_id, action.value)
        # Reuses the exact machinery routes_answers.py's PUT endpoint already
        # uses for a revisit from the report -- this is the "tool-using"
        # capability from docs/DECISIONS.md v19, not a duplicated code path.
        # This also flips AssessmentRun.plan_stale back to True (see
        # routes_report.py's _rescore_finding_and_refresh_report), so the
        # plan regenerates on its next visit -- this chat's own step_id
        # stays valid regardless, since old plan versions are never deleted.
        upsert_answer(run_id, action.indicator_id, AnswerIn(value=action.value, label=label, note=action.note), session)

        new_finding = session.exec(
            select(Finding).where(Finding.run_id == run_id, Finding.indicator_id == action.indicator_id)
        ).first()
        report = session.exec(select(Report).where(Report.run_id == run_id)).first()
        if new_finding is not None and report is not None:
            action_out = MentorActionOut(
                indicator_id=action.indicator_id,
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
