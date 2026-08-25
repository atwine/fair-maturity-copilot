"""Validates the synthetic demo dataset fixtures are well-formed — every
indicator answered, no stray indicator ids, valid answer values. No LLM or
database needed; this just guards fixtures/synthetic_datasets.py against
silent drift as indicators.yaml changes."""

from app.adapters.fair.adapter import FairAdapter
from fixtures.synthetic_datasets import SYNTHETIC_DATASETS

_VALID_VALUES = {"yes", "partial", "no", "dont_know"}


def _all_indicator_ids() -> set[str]:
    adapter = FairAdapter()
    return {q.indicator.id for q in adapter.question_set()}


def test_every_dataset_answers_every_indicator_exactly_once():
    all_ids = _all_indicator_ids()
    for dataset in SYNTHETIC_DATASETS:
        answered_ids = set(dataset["answers"].keys())
        assert answered_ids == all_ids, f"{dataset['slug']} answers don't match the current indicator set"


def test_every_answer_has_a_valid_value_and_a_real_note():
    for dataset in SYNTHETIC_DATASETS:
        for indicator_id, answer in dataset["answers"].items():
            assert answer["value"] in _VALID_VALUES, f"{dataset['slug']}/{indicator_id}: bad value {answer['value']!r}"
            assert answer["note"].strip(), f"{dataset['slug']}/{indicator_id}: empty note"
            assert answer["note"].strip() not in {"yes", "no", "partial", "dont_know"}, (
                f"{dataset['slug']}/{indicator_id}: note just restates the value, not useful for grounding"
            )


def test_dataset_slugs_are_unique():
    slugs = [d["slug"] for d in SYNTHETIC_DATASETS]
    assert len(slugs) == len(set(slugs))


def test_at_least_one_dataset_has_meaningfully_different_maturity_than_another():
    """The whole point of having multiple fixtures is to show the tool's
    range in a demo — guard against them accidentally converging."""
    from app.engine.models import Answer
    from app.engine.scoring import composite_score
    from uuid import uuid4

    adapter = FairAdapter()
    indicators_by_id = {q.indicator.id: q.indicator for q in adapter.question_set()}

    scores = []
    for dataset in SYNTHETIC_DATASETS:
        findings = []
        for indicator_id, raw in dataset["answers"].items():
            indicator = indicators_by_id[indicator_id]
            answer = Answer(
                run_id=uuid4(),
                indicator_id=indicator_id,
                raw_answer={"value": raw["value"], "label": raw["label"]},
                is_dont_know=(raw["value"] == "dont_know"),
            )
            findings.append(adapter.score(indicator, answer))
        scores.append(composite_score(findings))

    assert max(scores) - min(scores) > 20, f"synthetic dataset scores too similar: {scores}"
