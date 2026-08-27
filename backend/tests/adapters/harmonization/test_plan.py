"""Tests build_harmonization_plan's short-circuit and failure-propagation
behavior -- no LLM call needed for either case. See
tests/adapters/fair/test_plan.py for the identical pattern; the generic
parsing logic itself is tested once, adapter-independently, in
tests/engine/test_plan.py.
"""

from uuid import uuid4

from unittest.mock import patch

import pytest

from app.adapters.harmonization.plan import build_harmonization_plan
from app.engine.models import Finding, Indicator
from app.engine.plan import PlanGenerationFailed


def _indicator(id_: str) -> Indicator:
    return Indicator(
        id=id_,
        adapter_id="harmonization-v0",
        external_code="FAKE-1",
        principle_group="Consistent Naming",
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
    findings = [_finding("harmonization.h1-field-names", "pass"), _finding("harmonization.h3-data-dictionary", "pass")]
    indicators_by_id = {
        "harmonization.h1-field-names": _indicator("harmonization.h1-field-names"),
        "harmonization.h3-data-dictionary": _indicator("harmonization.h3-data-dictionary"),
    }
    plan = build_harmonization_plan(findings=findings, indicators_by_id=indicators_by_id, subject_label="Test Consortium")
    assert plan.steps == []
    assert "clean" in plan.goal.lower()


def test_a_not_started_finding_alone_does_not_short_circuit():
    # Issue #16: unlike "pass", a not_started finding has no score impact
    # but IS still something to plan a first step for -- it must reach the
    # LLM call, not be treated as "nothing to do."
    findings = [_finding("harmonization.h4-linkage-key", "not_started")]
    indicators_by_id = {"harmonization.h4-linkage-key": _indicator("harmonization.h4-linkage-key")}
    with patch("app.engine.plan.generate", return_value="this is not the expected format at all"):
        with pytest.raises(PlanGenerationFailed):
            build_harmonization_plan(findings=findings, indicators_by_id=indicators_by_id, subject_label="Test Consortium")


def test_open_findings_with_unparseable_llm_response_raises_instead_of_looking_clean():
    findings = [_finding("harmonization.h1-field-names", "major_gap")]
    indicators_by_id = {"harmonization.h1-field-names": _indicator("harmonization.h1-field-names")}
    with patch("app.engine.plan.generate", return_value="this is not the expected format at all"):
        with pytest.raises(PlanGenerationFailed):
            build_harmonization_plan(findings=findings, indicators_by_id=indicators_by_id, subject_label="Test Consortium")
