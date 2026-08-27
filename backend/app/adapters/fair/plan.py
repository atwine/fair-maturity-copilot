"""Synthesizes a single ordered FAIRification plan from all of a run's open
findings, in one LLM call — a different artifact from remediation.py's
per-finding write-up. Adapter-owned since the "natural FAIRification order"
categories in the prompt are FAIR-specific; the engine (app/engine/plan.py)
owns everything generic -- parsing, the open-findings filter, the
Plan/PlanStep/PlanGenerationFailed shapes -- so this file is just the
template + the one call that renders it.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.engine.models import Finding, Indicator
from app.engine.plan import Plan, generate_plan, open_findings

_PROMPT_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(_PROMPT_DIR)), trim_blocks=True, lstrip_blocks=True)
_template = _env.get_template("fairification_plan.jinja")


def build_fairification_plan(*, findings: list[Finding], indicators_by_id: dict[str, Indicator], subject_label: str) -> Plan:
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
    # A plan can cover up to 12 findings across several steps, so it's the
    # longest single generation in this app -- given generously (see
    # llm_client.py's module docstring for why: a reasoning model spends
    # tokens "thinking" before writing anything visible, and a tight
    # budget here would risk a truncated plan mid-step).
    valid_ids = {f.indicator_id for f in findings_to_plan}
    return generate_plan(prompt, valid_ids, max_tokens=1800)
