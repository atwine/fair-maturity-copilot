"""Implements app.engine.ports.Adapter for the multi-site harmonization
check (issue #16). Everything specific to this standard (indicator content,
prompt wording) is delegated to content.py/prompt.py/plan.py/mentor_prompt.py
-- this class is just the glue that satisfies the engine's Adapter Protocol,
same shape as app/adapters/fair/adapter.py."""

from app.adapters.harmonization.content import load_indicators, load_options_by_indicator_id
from app.adapters.harmonization.mentor_prompt import render_mentor_system_prompt as _render_mentor_system_prompt
from app.adapters.harmonization.plan import build_harmonization_plan
from app.adapters.harmonization.prompt import PROMPT_VERSION
from app.adapters.harmonization.prompt import render_remediation_prompt as _render_remediation_prompt
from app.engine.models import Answer, Finding, Indicator
from app.engine.plan import Plan
from app.engine.ports import MentorIndicatorContext, Question
from app.engine.scoring import priority_weight_for, severity_for_answer


class HarmonizationAdapter:
    adapter_id = "harmonization-v0"
    prompt_version = PROMPT_VERSION

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

    def render_remediation_prompt(
        self, indicator: Indicator, answer: Answer, subject_label: str, severity: str
    ) -> str:
        return _render_remediation_prompt(
            indicator=indicator, answer=answer, subject_label=subject_label, severity=severity
        )

    def render_mentor_system_prompt(
        self,
        step_title: str,
        step_detail: str,
        indicators: list[MentorIndicatorContext],
        subject_label: str,
        skill_level: str,
    ) -> str:
        return _render_mentor_system_prompt(
            step_title=step_title,
            step_detail=step_detail,
            indicators=indicators,
            subject_label=subject_label,
            skill_level=skill_level,
        )

    def build_plan(
        self, *, findings: list[Finding], indicators_by_id: dict[str, Indicator], subject_label: str
    ) -> Plan:
        return build_harmonization_plan(
            findings=findings, indicators_by_id=indicators_by_id, subject_label=subject_label
        )
