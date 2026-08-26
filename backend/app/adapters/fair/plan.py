"""Synthesizes a single ordered FAIRification plan from all of a run's open
findings, in one LLM call — a different artifact from remediation.py's
per-finding write-up. Adapter-owned (like prompt.py) since the "natural
FAIRification order" categories in the prompt are FAIR-specific; the engine
has no opinion on this.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.engine.llm_client import generate
from app.engine.models import Finding, Indicator

_PROMPT_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(_PROMPT_DIR)), trim_blocks=True, lstrip_blocks=True)
_template = _env.get_template("fairification_plan.jinja")


class PlanStep:
    def __init__(self, title: str, detail: str, indicator_ids: list[str]) -> None:
        self.title = title
        self.detail = detail
        self.indicator_ids = indicator_ids


class Plan:
    def __init__(self, goal: str, steps: list[PlanStep]) -> None:
        self.goal = goal
        self.steps = steps


def _parse_plan(text: str, valid_indicator_ids: set[str]) -> Plan:
    """Defensive line-based parser for the GOAL:/STEP:/ADDRESSES:/DETAIL:
    contract in fairification_plan.jinja -- an LLM won't always follow a
    format instruction exactly, so unrecognized lines are just skipped
    rather than raising, and any id in ADDRESSES not in valid_indicator_ids
    (a hallucinated or mistyped id) is silently dropped rather than shown."""
    goal = ""
    steps: list[PlanStep] = []
    current: dict[str, str | list[str]] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.upper().startswith("GOAL:"):
            goal = line[len("GOAL:") :].strip()
        elif line.upper().startswith("STEP:"):
            if current is not None:
                steps.append(
                    PlanStep(
                        title=str(current.get("title", "")),
                        detail=str(current.get("detail", "")),
                        indicator_ids=list(current.get("indicator_ids", [])),  # type: ignore[arg-type]
                    )
                )
            current = {"title": line[len("STEP:") :].strip(), "indicator_ids": []}
        elif line.upper().startswith("ADDRESSES:") and current is not None:
            ids = [i.strip() for i in line[len("ADDRESSES:") :].split(",")]
            current["indicator_ids"] = [i for i in ids if i in valid_indicator_ids]
        elif line.upper().startswith("DETAIL:") and current is not None:
            current["detail"] = line[len("DETAIL:") :].strip()

    if current is not None:
        steps.append(
            PlanStep(
                title=str(current.get("title", "")),
                detail=str(current.get("detail", "")),
                indicator_ids=list(current.get("indicator_ids", [])),  # type: ignore[arg-type]
            )
        )

    return Plan(goal=goal, steps=[s for s in steps if s.indicator_ids])


class PlanGenerationFailed(Exception):
    """Raised when there ARE open findings but the model's response didn't
    parse into any usable steps (total format failure, or every ADDRESSES
    line came back hallucinated). Deliberately distinct from "no open
    findings" -- an empty Plan.steps means two very different things, and
    the caller must not treat a parse failure as "you're all clean"."""


def build_fairification_plan(*, findings: list[Finding], indicators_by_id: dict[str, Indicator], subject_label: str) -> Plan:
    open_findings = [f for f in findings if f.severity != "pass"]
    if not open_findings:
        return Plan(goal="Every indicator already checked out clean -- nothing left to plan for.", steps=[])

    prompt = _template.render(
        subject_label=subject_label,
        findings=[
            {
                "indicator_id": f.indicator_id,
                "title": indicators_by_id[f.indicator_id].title,
                "severity_label": f.severity.replace("_", " "),
            }
            for f in open_findings
        ],
    )
    # A plan can cover up to 12 findings across several steps, so it's the
    # longest single generation in this app -- given generously (see
    # llm_client.py's module docstring for why: a reasoning model spends
    # tokens "thinking" before writing anything visible, and a tight
    # budget here would risk a truncated plan mid-step).
    text = generate(prompt, max_tokens=1800)
    valid_ids = {f.indicator_id for f in open_findings}
    plan = _parse_plan(text, valid_ids)
    if not plan.steps:
        raise PlanGenerationFailed("The model's response didn't produce any usable plan steps.")
    return plan
