"""Renders the FAIR remediation prompt. Adapter-owned per the engine/adapter
split: the engine (app/engine/remediation.py) owns *how* a remediation gets
generated and grounding-checked; this module owns *what* goes into the
prompt for the FAIR standard specifically."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.engine.models import Answer, Indicator

_PROMPT_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(_PROMPT_DIR)), trim_blocks=True, lstrip_blocks=True)
_template = _env.get_template("remediation.jinja")

PROMPT_VERSION = "fair-remediation-v3"  # v3: repository decision rule (Zenodo/OSF/Dataverse/Vivli) replaces hardcoded Zenodo-only mention (issue #6) -- v2: SUMMARY/STEPS contract + plain-language term-explanation rule (docs/DECISIONS.md v13)


def render_remediation_prompt(*, indicator: Indicator, answer: Answer, subject_label: str, severity: str) -> str:
    return _template.render(
        subject_label=subject_label,
        indicator=indicator,
        answer_label=answer.raw_answer.get("label", answer.raw_answer.get("value", "")),
        free_text_note=answer.free_text_note,
        is_dont_know=answer.is_dont_know,
        severity=severity,
    )
