"""Renders the harmonization adapter's remediation-writer prompt. See
app/adapters/fair/prompt.py for the identical pattern -- everything generic
about *how* a remediation gets generated and grounding-checked lives in
app/engine/remediation.py; this module owns only *what* goes into the
prompt for this standard's own content."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.engine.models import Answer, Indicator

_PROMPT_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(_PROMPT_DIR)), trim_blocks=True, lstrip_blocks=True)
_template = _env.get_template("remediation.jinja")

PROMPT_VERSION = "harmonization-remediation-v1"


def render_remediation_prompt(*, indicator: Indicator, answer: Answer, subject_label: str, severity: str) -> str:
    return _template.render(
        subject_label=subject_label,
        indicator=indicator,
        answer_label=answer.raw_answer.get("label", answer.raw_answer.get("value", "")),
        free_text_note=answer.free_text_note,
        is_dont_know=answer.is_dont_know,
        severity=severity,
    )
