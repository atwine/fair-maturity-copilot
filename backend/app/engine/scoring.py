"""Generic severity normalization. Operates only on Indicator.priority and
the Finding shape an adapter already produced — never on indicator-specific
content. If this file ever needs to know what "FAIR" or "OMOP" means,
something has leaked across the adapter boundary.
"""

from app.engine.models import Finding

_PRIORITY_WEIGHT = {"essential": 3, "important": 2, "useful": 1}

_SEVERITY_RANK = {"pass": 0, "minor_gap": 1, "unknown": 2, "major_gap": 3}


def priority_weight_for(priority: str) -> int:
    return _PRIORITY_WEIGHT.get(priority, 1)


def composite_score(findings: list[Finding]) -> float:
    """0-100 composite: pass = full credit, minor_gap = half, unknown/major_gap
    = no credit, weighted by each finding's priority_weight."""
    if not findings:
        return 0.0
    credit = {"pass": 1.0, "minor_gap": 0.5, "unknown": 0.0, "major_gap": 0.0}
    total_weight = sum(f.priority_weight for f in findings)
    if total_weight == 0:
        return 0.0
    earned = sum(credit.get(f.severity, 0.0) * f.priority_weight for f in findings)
    return round(100 * earned / total_weight, 1)


def rank(findings: list[Finding]) -> list[Finding]:
    """Worst-first ordering for the report — major gaps on essential
    indicators surface before minor gaps on useful ones."""
    return sorted(
        findings,
        key=lambda f: (-_SEVERITY_RANK.get(f.severity, 0), -f.priority_weight),
    )
