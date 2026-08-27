"""Tests engine/plan.py's parsing and open-findings filter directly -- no
LLM call needed, both are pure functions of already-produced text/Finding
objects. Moved here from tests/adapters/fair/test_plan.py (issue #16):
this logic isn't FAIR-specific, so it shouldn't only be tested against
FAIR's own test file -- see app/engine/plan.py's module docstring.
"""

from uuid import uuid4

from app.engine.models import Finding
from app.engine.plan import open_findings, parse_plan


def _finding(indicator_id: str, severity: str) -> Finding:
    return Finding(run_id=uuid4(), indicator_id=indicator_id, answer_id=uuid4(), severity=severity, priority_weight=3)


def test_parse_plan_extracts_goal_and_steps():
    text = (
        "GOAL: Get your dataset ready for others to find and reuse.\n"
        "STEP: Give your dataset a permanent identifier\n"
        "ADDRESSES: fair.f1-identifier, fair.f3-metadata-links-to-data\n"
        "DETAIL: Register it with a free repository to get a permanent web ID.\n"
        "STEP: Write a short data dictionary\n"
        "ADDRESSES: fair.r1-data-dictionary\n"
        "DETAIL: List what each column means in a short README.\n"
    )
    plan = parse_plan(text, {"fair.f1-identifier", "fair.f3-metadata-links-to-data", "fair.r1-data-dictionary"})
    assert plan.goal == "Get your dataset ready for others to find and reuse."
    assert len(plan.steps) == 2
    assert plan.steps[0].indicator_ids == ["fair.f1-identifier", "fair.f3-metadata-links-to-data"]
    assert plan.steps[1].title == "Write a short data dictionary"


def test_parse_plan_drops_hallucinated_indicator_ids():
    text = (
        "GOAL: Fix your dataset.\n"
        "STEP: Do a thing\n"
        "ADDRESSES: fair.f1-identifier, fair.made-up-indicator\n"
        "DETAIL: Something.\n"
    )
    plan = parse_plan(text, {"fair.f1-identifier"})
    assert plan.steps[0].indicator_ids == ["fair.f1-identifier"]


def test_parse_plan_drops_steps_left_with_no_valid_ids():
    # A step whose only ADDRESSES id was hallucinated has nothing real to
    # point at -- showing it would silently look actionable when it isn't.
    text = (
        "GOAL: Fix your dataset.\n"
        "STEP: A step about nothing real\n"
        "ADDRESSES: fair.made-up-indicator\n"
        "DETAIL: Something.\n"
        "STEP: A real step\n"
        "ADDRESSES: fair.f1-identifier\n"
        "DETAIL: Something else.\n"
    )
    plan = parse_plan(text, {"fair.f1-identifier"})
    assert len(plan.steps) == 1
    assert plan.steps[0].title == "A real step"


def test_open_findings_excludes_only_pass():
    # A not_started finding must NOT be excluded here even though it's
    # excluded from the composite score (app/engine/scoring.py) -- it has
    # no score impact, but there's still a real "how to begin" step worth
    # planning, unlike a passing finding which has nothing to plan for.
    findings = [
        _finding("a.1", "pass"),
        _finding("a.2", "not_started"),
        _finding("a.3", "minor_gap"),
        _finding("a.4", "major_gap"),
        _finding("a.5", "unknown"),
    ]
    remaining_ids = {f.indicator_id for f in open_findings(findings)}
    assert remaining_ids == {"a.2", "a.3", "a.4", "a.5"}
