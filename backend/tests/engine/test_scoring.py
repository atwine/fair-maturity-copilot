"""Tests engine/scoring.py directly — no adapter or LLM needed, since
severity_for_answer/composite_score/rank all operate on plain Finding/
Indicator objects built by hand.
"""

from uuid import uuid4

import pytest

from app.engine.models import Finding, Indicator
from app.engine.scoring import composite_score, rank, severity_for_answer


def _indicator(*, priority="essential", scoring_rubric=None) -> Indicator:
    return Indicator(
        id="test.indicator",
        adapter_id="test-v0",
        external_code="TEST-1",
        principle_group="Testable",
        title="A test indicator",
        definition="",
        plain_language_question="",
        help_text="",
        example="",
        priority=priority,
        display_order=1,
        scoring_rubric=scoring_rubric or {},
    )


def _finding(severity: str, *, priority_weight=3) -> Finding:
    return Finding(run_id=uuid4(), indicator_id="test.indicator", answer_id=uuid4(), severity=severity, priority_weight=priority_weight)


def test_severity_for_answer_reads_the_indicators_own_rubric():
    indicator = _indicator(scoring_rubric={"yes": "pass", "not_started": "not_started"})
    assert severity_for_answer(indicator, "yes") == "pass"
    assert severity_for_answer(indicator, "not_started") == "not_started"


def test_severity_for_answer_raises_on_unrecognized_value():
    indicator = _indicator(scoring_rubric={"yes": "pass"})
    with pytest.raises(ValueError):
        severity_for_answer(indicator, "not_a_real_value")


def test_not_started_findings_are_excluded_from_the_composite_score():
    # Issue #16: a not_started finding must be genuinely neutral -- neither
    # helping nor hurting the score -- not silently scored as a fail (which
    # is what an unrecognized severity used to do before this fix: it got
    # zero credit but was still counted in the denominator).
    all_pass = [_finding("pass"), _finding("pass")]
    pass_plus_not_started = [_finding("pass"), _finding("pass"), _finding("not_started")]
    assert composite_score(all_pass) == composite_score(pass_plus_not_started) == 100.0


def test_a_run_of_only_not_started_findings_scores_zero_not_a_crash():
    # No real "scored" findings at all -- must not divide by zero.
    assert composite_score([_finding("not_started"), _finding("not_started")]) == 0.0


def test_composite_score_still_penalizes_real_gaps_as_before():
    # Regression guard: the not_started exclusion must not have changed
    # scoring for the 4 severities that existed before issue #16.
    findings = [_finding("pass", priority_weight=3), _finding("major_gap", priority_weight=3)]
    assert composite_score(findings) == 50.0


def test_rank_orders_not_started_ahead_of_pass_but_behind_real_gaps():
    findings = [_finding("pass"), _finding("not_started"), _finding("major_gap"), _finding("minor_gap")]
    ordered = rank(findings)
    assert [f.severity for f in ordered] == ["major_gap", "minor_gap", "not_started", "pass"]
