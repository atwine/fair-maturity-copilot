"""Turns a raw answer value into a severity, using the rubric attached to
the Indicator itself (loaded from indicators.yaml) — never a hardcoded
if/else chain. This is what keeps the rubric editable without a code
change, per the "not a FAIR domain expert who can safely bury judgment
calls in code" constraint in docs/PLANNING_PROMPT.md."""

from app.engine.models import Indicator


def severity_for_answer(indicator: Indicator, answer_value: str) -> str:
    severity = indicator.scoring_rubric.get(answer_value)
    if severity is None:
        # Unrecognized answer value is a data problem, not a silent "unknown"
        # — fail loudly rather than mis-scoring it.
        raise ValueError(
            f"No rubric entry for answer value {answer_value!r} on indicator {indicator.id!r}"
        )
    return severity
