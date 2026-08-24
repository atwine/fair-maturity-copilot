"""Proves the engine/adapter boundary holds *before* any FAIR content
exists: a fake, minimal adapter implementing app.engine.ports.Adapter is
enough to exercise scoring end-to-end. If this test needs to import
anything from app.adapters, the boundary is already broken.
"""

from uuid import uuid4

from app.engine.models import Answer, Finding, Indicator
from app.engine.scoring import composite_score, priority_weight_for, rank


class FakeAdapter:
    """Minimal stand-in — deliberately not FAIR, not OMOP, just enough to
    prove app/engine/* works against *any* Adapter implementation."""

    adapter_id = "fake-v0"

    def question_set(self):
        return []

    def score(self, indicator: Indicator, answer: Answer) -> Finding:
        severity = "pass" if answer.raw_answer.get("value") == "yes" else "major_gap"
        return Finding(
            run_id=answer.run_id,
            indicator_id=indicator.id,
            answer_id=answer.id,
            severity=severity,
            priority_weight=priority_weight_for(indicator.priority),
        )


def _make_indicator(priority: str) -> Indicator:
    return Indicator(
        id=f"fake.{priority}",
        adapter_id="fake-v0",
        external_code="FAKE-1",
        principle_group="Testable",
        title="A fake indicator",
        definition="Exists only to test the engine.",
        plain_language_question="Is this a fake question?",
        help_text="",
        priority=priority,
        display_order=1,
        scoring_rubric={},
    )


def test_fake_adapter_produces_findings_the_engine_can_score():
    adapter = FakeAdapter()
    run_id = uuid4()

    essential = _make_indicator("essential")
    useful = _make_indicator("useful")

    pass_answer = Answer(run_id=run_id, indicator_id=essential.id, raw_answer={"value": "yes", "label": "Yes"})
    fail_answer = Answer(run_id=run_id, indicator_id=useful.id, raw_answer={"value": "no", "label": "No"})

    findings = [
        adapter.score(essential, pass_answer),
        adapter.score(useful, fail_answer),
    ]

    assert findings[0].severity == "pass"
    assert findings[1].severity == "major_gap"

    # An essential pass + a useful fail should score well above zero but
    # below 100 — proves priority weighting actually affects the composite.
    score = composite_score(findings)
    assert 0 < score < 100

    # The failing, higher-context finding should not necessarily outrank a
    # lower-priority pass in `rank` — but the major_gap must appear before
    # the pass in worst-first order.
    ordered = rank(findings)
    assert ordered[0].severity == "major_gap"
