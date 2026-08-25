"""Tests plan.py's parsing and short-circuit logic directly -- no LLM call
needed for either case: _parse_plan is pure text-in/Plan-out, and the
all-pass short-circuit in build_fairification_plan returns before ever
calling the LLM. The live end-to-end generation path (a real prompt against
a real model) is tested in tests/api/test_plan_live.py instead.
"""

from uuid import uuid4

from unittest.mock import patch

import pytest

from app.adapters.fair.plan import PlanGenerationFailed, _parse_plan, build_fairification_plan
from app.engine.models import Finding, Indicator


def _indicator(id_: str) -> Indicator:
    return Indicator(
        id=id_,
        adapter_id="fair-v0",
        external_code="FAKE-1",
        principle_group="Findable",
        title=f"Title for {id_}",
        definition="",
        plain_language_question="",
        help_text="",
        example="",
        priority="essential",
        display_order=1,
        scoring_rubric={},
    )


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
    plan = _parse_plan(text, {"fair.f1-identifier", "fair.f3-metadata-links-to-data", "fair.r1-data-dictionary"})
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
    plan = _parse_plan(text, {"fair.f1-identifier"})
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
    plan = _parse_plan(text, {"fair.f1-identifier"})
    assert len(plan.steps) == 1
    assert plan.steps[0].title == "A real step"


def test_all_passing_findings_short_circuits_without_calling_the_llm():
    findings = [_finding("fair.f1-identifier", "pass"), _finding("fair.r1-1-license", "pass")]
    indicators_by_id = {"fair.f1-identifier": _indicator("fair.f1-identifier"), "fair.r1-1-license": _indicator("fair.r1-1-license")}
    plan = build_fairification_plan(findings=findings, indicators_by_id=indicators_by_id, subject_label="Test Dataset")
    assert plan.steps == []
    assert "clean" in plan.goal.lower()


def test_open_findings_with_unparseable_llm_response_raises_instead_of_looking_clean():
    # Regression test: an empty Plan.steps must never be confused between
    # "nothing to fix" (the short-circuit above) and "the model's response
    # didn't parse" -- the latter must be a loud failure, not a silent
    # false "you're all set."
    findings = [_finding("fair.f1-identifier", "major_gap")]
    indicators_by_id = {"fair.f1-identifier": _indicator("fair.f1-identifier")}
    with patch("app.adapters.fair.plan.generate", return_value="this is not the expected format at all"):
        with pytest.raises(PlanGenerationFailed):
            build_fairification_plan(findings=findings, indicators_by_id=indicators_by_id, subject_label="Test Dataset")
