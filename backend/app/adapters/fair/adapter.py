"""Implements app.engine.ports.Adapter for the FAIR standard. Everything
FAIR-specific (indicator content, the scoring rubric) is delegated to
content.py/scoring_rubric.py — this class is just the glue that satisfies
the engine's Adapter Protocol."""

from app.adapters.fair.content import load_indicators, load_options_by_indicator_id
from app.adapters.fair.scoring_rubric import severity_for_answer
from app.engine.models import Answer, Finding, Indicator
from app.engine.ports import Question
from app.engine.scoring import priority_weight_for


class FairAdapter:
    adapter_id = "fair-v0"

    def __init__(self) -> None:
        self._indicators = load_indicators()
        self._options_by_id = load_options_by_indicator_id()

    def question_set(self) -> list[Question]:
        return [
            Question(indicator=indicator, options=self._options_by_id[indicator.id])
            for indicator in self._indicators
        ]

    def score(self, indicator: Indicator, answer: Answer) -> Finding:
        answer_value = answer.raw_answer.get("value")
        severity = severity_for_answer(indicator, answer_value)
        return Finding(
            run_id=answer.run_id,
            indicator_id=indicator.id,
            answer_id=answer.id,
            severity=severity,
            priority_weight=priority_weight_for(indicator.priority),
        )
