"""Generic severity normalization and scoring. Operates only on
Indicator.priority/scoring_rubric and the Finding shape an adapter already
produced — never on indicator-specific content. If this file ever needs to
know what "FAIR" or "OMOP" means, something has leaked across the adapter
boundary.
"""

from app.engine.models import Finding, Indicator

_PRIORITY_WEIGHT = {"essential": 3, "important": 2, "useful": 1}

_SEVERITY_RANK = {"pass": 0, "not_started": 1, "minor_gap": 2, "unknown": 3, "major_gap": 4}

# Severities that must never move the composite score in either direction.
# "not_started" is the first one of these: an initiative that hasn't begun a
# harmonization practice yet isn't failing it, so a not_started finding is
# excluded from both the numerator and the denominator entirely, rather than
# scored as a partial or zero credit.
_EXCLUDED_FROM_COMPOSITE = {"not_started"}


def priority_weight_for(priority: str) -> int:
    return _PRIORITY_WEIGHT.get(priority, 1)


def severity_for_answer(indicator: Indicator, answer_value: str) -> str:
    """Turns a raw answer value into a severity, using the rubric attached
    to the Indicator itself (loaded from its adapter's indicators.yaml) --
    never a hardcoded if/else chain. This is what keeps the rubric editable
    without a code change, per the "not a domain expert who can safely bury
    judgment calls in code" constraint in docs/PLANNING_PROMPT.md.

    Lives here, not on a per-adapter module, because the lookup itself is
    already fully generic -- it only ever reads indicator.scoring_rubric, a
    plain dict every adapter's content loader populates the same way."""
    severity = indicator.scoring_rubric.get(answer_value)
    if severity is None:
        # Unrecognized answer value is a data problem, not a silent "unknown"
        # — fail loudly rather than mis-scoring it.
        raise ValueError(
            f"No rubric entry for answer value {answer_value!r} on indicator {indicator.id!r}"
        )
    return severity


def composite_score(findings: list[Finding]) -> float:
    """0-100 composite: pass = full credit, minor_gap = half, unknown/major_gap
    = no credit, weighted by each finding's priority_weight. A finding whose
    severity is in _EXCLUDED_FROM_COMPOSITE (e.g. not_started) doesn't count
    toward the score at all -- neither the numerator nor the denominator."""
    scored = [f for f in findings if f.severity not in _EXCLUDED_FROM_COMPOSITE]
    if not scored:
        return 0.0
    credit = {"pass": 1.0, "minor_gap": 0.5, "unknown": 0.0, "major_gap": 0.0}
    total_weight = sum(f.priority_weight for f in scored)
    if total_weight == 0:
        return 0.0
    earned = sum(credit.get(f.severity, 0.0) * f.priority_weight for f in scored)
    return round(100 * earned / total_weight, 1)


def rank(findings: list[Finding]) -> list[Finding]:
    """Worst-first ordering for the report — major gaps on essential
    indicators surface before minor gaps on useful ones."""
    return sorted(
        findings,
        key=lambda f: (-_SEVERITY_RANK.get(f.severity, 0), -f.priority_weight),
    )
