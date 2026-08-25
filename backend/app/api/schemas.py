"""Pydantic request/response models — the actual contract between the
backend and whatever frontend (Next.js, or a script) calls it."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class QuestionOut(BaseModel):
    indicator_id: str
    title: str
    plain_language_question: str
    help_text: str
    example: str
    priority: str
    principle_group: str  # "Findable" | "Accessible" | "Interoperable" | "Reusable"
    display_order: int
    options: list[dict]


class CreateAssessmentRequest(BaseModel):
    adapter_id: str
    subject_label: str
    created_by_email: str | None = None


class AnswerIn(BaseModel):
    value: str  # "yes" | "partial" | "no" | "dont_know"
    label: str
    note: str | None = None


class AnswerOut(BaseModel):
    indicator_id: str
    value: str
    label: str
    note: str | None
    is_dont_know: bool


class AssessmentOut(BaseModel):
    id: UUID
    adapter_id: str
    subject_label: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    answered_indicator_ids: list[str]
    answers: list[AnswerOut]


class FindingOut(BaseModel):
    indicator_id: str
    title: str
    severity: str
    principle_group: str  # "Findable" | "Accessible" | "Interoperable" | "Reusable"
    remediation_text: str | None


class ReportOut(BaseModel):
    run_id: UUID
    score: float
    generated_at: datetime
    findings: list[FindingOut]
    markdown: str


class PlanIndicatorRefOut(BaseModel):
    indicator_id: str
    title: str
    principle_group: str  # "Findable" | "Accessible" | "Interoperable" | "Reusable"


class PlanStepOut(BaseModel):
    title: str
    detail: str
    indicators: list[PlanIndicatorRefOut]


class PlanOut(BaseModel):
    run_id: UUID
    goal: str
    steps: list[PlanStepOut]


class MentorStartRequest(BaseModel):
    skill_level: str  # "new_to_this" | "done_this_before" -- explicit, never inferred


class MentorMessageIn(BaseModel):
    content: str


class MentorMessageOut(BaseModel):
    role: str  # "user" | "mentor"
    content: str
    created_at: datetime


class MentorConversationOut(BaseModel):
    indicator_id: str
    skill_level: str
    messages: list[MentorMessageOut]


class MentorActionOut(BaseModel):
    indicator_id: str
    new_value: str  # "yes" | "partial" | "no"
    new_severity: str
    new_score: float


class MentorReplyOut(BaseModel):
    mentor_message: MentorMessageOut
    action_taken: MentorActionOut | None
