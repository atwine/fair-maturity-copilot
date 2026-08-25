"""The actual engine/adapter seam.

Any standard (FAIR today, OMOP data-quality later) plugs in by implementing
this Protocol. Nothing in app/engine/* may import a concrete adapter —
adapters depend on the engine, never the reverse.
"""

from dataclasses import dataclass
from typing import Protocol

from app.engine.models import Answer, Finding, Indicator


@dataclass
class Question:
    """What the frontend renders for one indicator. Adapter-supplied,
    engine-agnostic shape."""

    indicator: Indicator
    options: list[dict]  # e.g. [{"value": "yes", "label": "Yes, clearly true"}, ...]


@dataclass
class MentorIndicatorContext:
    """One indicator's worth of context for a mentor system prompt -- a plan
    step can bundle several of these (issue #9), where a single-indicator
    mentor prompt used to take just one."""

    indicator: Indicator
    severity: str
    current_answer: Answer | None


class Adapter(Protocol):
    """Every standard-specific adapter (fair, later omop) implements this.
    The API layer (app/api/*) is only allowed to depend on this Protocol and
    the registry in app/adapters/registry.py — never on a concrete adapter
    module directly. That's what lets it generate reports for any adapter
    without knowing FAIR (or OMOP, later) exists."""

    adapter_id: str
    prompt_version: str

    def question_set(self) -> list[Question]:
        """Return the ordered questions this adapter asks."""
        ...

    def score(self, indicator: Indicator, answer: Answer) -> Finding:
        """Turn one answer into a Finding with a severity + priority_weight.
        Must not mutate global state; pure function of (indicator, answer)."""
        ...

    def render_remediation_prompt(
        self, indicator: Indicator, answer: Answer, subject_label: str, severity: str
    ) -> str:
        """Build the remediation-writer prompt for one finding — including a
        passing one, which gets a short "why this is fine" note instead of a
        fix. The engine (app/engine/remediation.py) owns *how* the prompt
        gets sent to the LLM and grounding-checked; the adapter owns *what*
        goes into it, and severity is what lets it pick the right framing."""
        ...

    def render_mentor_system_prompt(
        self,
        step_title: str,
        step_detail: str,
        indicators: list[MentorIndicatorContext],
        subject_label: str,
        skill_level: str,
    ) -> str:
        """Build the system prompt for a mentor chat scoped to one
        FAIRification plan step (Checkpoint 9 / issue #9) -- a step can
        bundle several indicators, so the mentor is briefed on all of them
        at once, not just one. The engine (app/engine/mentor.py) owns *how*
        the conversation loop runs and how a confirmed-fix line in the
        model's reply (naming which indicator it resolved) gets parsed and
        turned into a real answer update; the adapter owns *what* grounds
        the mentor (this standard's own content/tone) and how skill_level
        changes its explanations."""
        ...
