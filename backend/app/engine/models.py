"""Standard-agnostic data model.

Nothing in this file may reference "FAIR", "RDA", "OMOP", or any other
standard by name. An Indicator is just an indicator, scoped to whichever
Adapter loaded it — that's what lets a second adapter (e.g. OMOP) plug in
later without touching this file. See docs/DECISIONS.md and
app/engine/ports.py for the boundary this enforces.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Adapter(SQLModel, table=True):
    id: str = Field(primary_key=True)  # e.g. "fair-v0"
    name: str
    version: str


class Indicator(SQLModel, table=True):
    id: str = Field(primary_key=True)  # adapter-scoped, e.g. "fair.f1-identifier"
    adapter_id: str = Field(foreign_key="adapter.id")
    external_code: str  # e.g. "RDA-F1-01M / RDA-F1-01D" — adapter's own citation, opaque to the engine
    principle_group: str  # adapter-defined grouping label, opaque to the engine
    title: str
    definition: str
    plain_language_question: str
    help_text: str
    example: str  # a concrete worked example grounding the question in a real scenario
    priority: str  # "essential" | "important" | "useful" — adapter-defined vocabulary
    display_order: int
    scoring_rubric: dict = Field(sa_column=Column(JSON))


class AssessmentRun(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    adapter_id: str = Field(foreign_key="adapter.id")
    subject_label: str
    created_by_email: str | None = None
    status: str = Field(default="in_progress")  # "in_progress" | "completed"
    created_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = None


class Answer(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("run_id", "indicator_id", name="uq_answer_run_indicator"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="assessmentrun.id")
    indicator_id: str = Field(foreign_key="indicator.id")
    raw_answer: dict = Field(sa_column=Column(JSON))  # {"value": "yes"|"partial"|"no"|"dont_know", "label": "..."}
    free_text_note: str | None = None
    is_dont_know: bool = False
    answered_at: datetime = Field(default_factory=_utcnow)


class Finding(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("run_id", "indicator_id", name="uq_finding_run_indicator"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="assessmentrun.id")
    indicator_id: str = Field(foreign_key="indicator.id")
    answer_id: UUID = Field(foreign_key="answer.id")
    severity: str  # "pass" | "minor_gap" | "major_gap" | "unknown"
    priority_weight: int
    computed_at: datetime = Field(default_factory=_utcnow)


class RemediationDraft(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    finding_id: UUID = Field(foreign_key="finding.id")
    llm_model_id: str
    prompt_version: str
    remediation_text: str
    grounding_check_passed: bool
    grounding_check_notes: str | None = None
    generated_at: datetime = Field(default_factory=_utcnow)
    shown_to_user_at: datetime | None = None


class Report(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="assessmentrun.id", unique=True)
    generated_at: datetime = Field(default_factory=_utcnow)
    summary_score: float
    rendered_markdown: str


class MentorConversation(SQLModel, table=True):
    """One chat session, scoped to a single (run, indicator) pair -- e.g.
    one FAIRification plan step's indicator, not the whole assessment. Reuses
    the same (run_id, indicator_id) scoping Answer/Finding already use, so
    a conversation is addressable the same way a revisit link already is.
    skill_level is a one-time, explicit toggle (never inferred) set when the
    conversation starts -- see Checkpoint 9 scoping in docs/DECISIONS.md v19."""

    __table_args__ = (UniqueConstraint("run_id", "indicator_id", name="uq_mentorconversation_run_indicator"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="assessmentrun.id")
    indicator_id: str = Field(foreign_key="indicator.id")
    skill_level: str  # "new_to_this" | "done_this_before"
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class MentorMessage(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="mentorconversation.id")
    role: str  # "user" | "mentor"
    content: str
    created_at: datetime = Field(default_factory=_utcnow)
