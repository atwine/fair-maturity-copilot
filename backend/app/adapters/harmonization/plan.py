"""Synthesizes a single ordered harmonization-readiness plan from all of a
run's open findings, in one LLM call. See app/adapters/fair/plan.py for the
identical pattern -- adapter-owned only for its own prompt template
(natural ordering specific to this content); everything generic (parsing,
the open-findings filter, the Plan/PlanStep/PlanGenerationFailed shapes)
lives in app/engine/plan.py.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.engine.models import Finding, Indicator
from app.engine.plan import Plan, generate_plan, open_findings

_PROMPT_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(_PROMPT_DIR)), trim_blocks=True, lstrip_blocks=True)
_template = _env.get_template("harmonization_plan.jinja")


def build_harmonization_plan(*, findings: list[Finding], indicators_by_id: dict[str, Indicator], subject_label: str) -> Plan:
    findings_to_plan = open_findings(findings)
    if not findings_to_plan:
        return Plan(goal="Every indicator already checked out clean -- nothing left to plan for.", steps=[])

    prompt = _template.render(
        subject_label=subject_label,
        findings=[
            {
                "indicator_id": f.indicator_id,
                "title": indicators_by_id[f.indicator_id].title,
                "severity_label": f.severity.replace("_", " "),
            }
            for f in findings_to_plan
        ],
    )
    valid_ids = {f.indicator_id for f in findings_to_plan}
    return generate_plan(prompt, valid_ids, max_tokens=1800)
