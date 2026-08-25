"""Renders the FAIR mentor's system prompt (Checkpoint 9). Adapter-owned per
the same engine/adapter split as prompt.py/plan.py: the engine
(app/engine/mentor.py) owns *how* a conversation turn runs and how a
confirmed-fix line gets parsed; this module owns *what* grounds the mentor
for the FAIR standard specifically -- deliberately no RAG, no external
document ingestion, per docs/DECISIONS.md v19. The grounding content here is
a static distillation of docs/WHY-THIS-TOOL.md's synthesis plus the
indicator's own already-loaded content, not a live read of that file."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.engine.ports import MentorIndicatorContext

_PROMPT_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(_PROMPT_DIR)), trim_blocks=True, lstrip_blocks=True)
_template = _env.get_template("mentor_system.jinja")

MENTOR_PROMPT_VERSION = "fair-mentor-v2"  # v2: scoped to a plan step (issue #9), not a single indicator

_VALID_SKILL_LEVELS = {"new_to_this", "done_this_before"}


def render_mentor_system_prompt(
    *,
    step_title: str,
    step_detail: str,
    indicators: list[MentorIndicatorContext],
    subject_label: str,
    skill_level: str,
) -> str:
    if skill_level not in _VALID_SKILL_LEVELS:
        raise ValueError(f"skill_level must be one of {sorted(_VALID_SKILL_LEVELS)}, got {skill_level!r}")
    return _template.render(
        subject_label=subject_label,
        step_title=step_title,
        step_detail=step_detail,
        indicators=[
            {
                "indicator": ctx.indicator,
                "severity_label": ctx.severity.replace("_", " "),
                "current_answer": ctx.current_answer,
            }
            for ctx in indicators
        ],
        skill_level=skill_level,
    )
