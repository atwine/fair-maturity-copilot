"""Tests build_fairification_plan's FAIR-specific short-circuit and
failure-propagation behavior -- no LLM call needed for either case: the
all-pass short-circuit returns before ever calling the LLM, and the
unparseable-response case patches app.engine.plan.generate (where the LLM
call actually happens now, see app/engine/plan.py) to force a bad response
without a real one.

The generic parsing logic itself (GOAL:/STEP:/ADDRESSES:/DETAIL:) is tested
once, adapter-independently, in tests/engine/test_plan.py. The live
end-to-end generation path (a real prompt against a real model) is tested
in tests/api/test_plan_live.py.
"""

from uuid import uuid4

from unittest.mock import patch

import pytest

from app.adapters.fair.plan import build_fairification_plan
from app.engine.models import Finding, Indicator
from app.engine.plan import PlanGenerationFailed


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
    with patch("app.engine.plan.generate", return_value="this is not the expected format at all"):
        with pytest.raises(PlanGenerationFailed):
            build_fairification_plan(findings=findings, indicators_by_id=indicators_by_id, subject_label="Test Dataset")
