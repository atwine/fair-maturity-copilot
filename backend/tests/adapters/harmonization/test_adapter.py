"""Tests the harmonization adapter's content and scoring — no database
needed, since content.py parses indicators.yaml directly into in-memory
objects. See tests/adapters/fair/test_adapter.py for the identical
pattern."""

from uuid import uuid4

import pytest

from app.adapters.harmonization.adapter import HarmonizationAdapter
from app.engine.models import Answer
from app.engine.scoring import severity_for_answer


def test_question_set_has_all_six_indicators_in_display_order():
    adapter = HarmonizationAdapter()
    questions = adapter.question_set()

    assert len(questions) == 6
    orders = [q.indicator.display_order for q in questions]
    assert orders == sorted(orders)

    # every question must have exactly the 5 harmonization answer options
    # (the 4 standard ones plus "not_started" -- issue #16)
    for q in questions:
        values = {opt["value"] for opt in q.options}
        assert values == {"yes", "partial", "no", "dont_know", "not_started"}


def test_every_indicator_has_a_unique_id_and_nonempty_content():
    adapter = HarmonizationAdapter()
    indicators = [q.indicator for q in adapter.question_set()]

    ids = [i.id for i in indicators]
    assert len(ids) == len(set(ids)), "duplicate indicator ids in indicators.yaml"

    for indicator in indicators:
        assert indicator.plain_language_question.strip()
        assert indicator.definition.strip()
        assert indicator.priority in {"essential", "important", "useful"}


def test_score_maps_answers_to_expected_severity_including_not_started():
    adapter = HarmonizationAdapter()
    indicator = adapter.question_set()[0].indicator
    run_id = uuid4()

    yes_answer = Answer(run_id=run_id, indicator_id=indicator.id, raw_answer={"value": "yes"})
    no_answer = Answer(run_id=run_id, indicator_id=indicator.id, raw_answer={"value": "no"})
    dont_know_answer = Answer(
        run_id=run_id, indicator_id=indicator.id, raw_answer={"value": "dont_know"}, is_dont_know=True
    )
    not_started_answer = Answer(run_id=run_id, indicator_id=indicator.id, raw_answer={"value": "not_started"})

    assert adapter.score(indicator, yes_answer).severity == "pass"
    assert adapter.score(indicator, no_answer).severity == "major_gap"
    assert adapter.score(indicator, dont_know_answer).severity == "unknown"
    assert adapter.score(indicator, not_started_answer).severity == "not_started"


def test_severity_for_answer_raises_on_unrecognized_value():
    adapter = HarmonizationAdapter()
    indicator = adapter.question_set()[0].indicator

    with pytest.raises(ValueError):
        severity_for_answer(indicator, "not_a_real_option")
