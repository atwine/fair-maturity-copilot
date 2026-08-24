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


class Adapter(Protocol):
    """Every standard-specific adapter (fair, later omop) implements this."""

    adapter_id: str

    def question_set(self) -> list[Question]:
        """Return the ordered questions this adapter asks."""
        ...

    def score(self, indicator: Indicator, answer: Answer) -> Finding:
        """Turn one answer into a Finding with a severity + priority_weight.
        Must not mutate global state; pure function of (indicator, answer)."""
        ...
