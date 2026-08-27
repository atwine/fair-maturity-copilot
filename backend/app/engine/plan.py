"""Generic FAIRification-plan machinery, shared by every adapter. An
adapter owns its own prompt wording (the "natural order" of its own
content) and calls generate_plan() with that rendered prompt; everything
about parsing the model's response and turning it into a Plan is standard-
agnostic and lives here exactly once.

Moved out of app/adapters/fair/plan.py (issue #16): none of this — the
GOAL:/STEP:/ADDRESSES:/DETAIL: parsing contract, the open-findings filter,
the PlanGenerationFailed distinction — was ever actually FAIR-specific. It
stayed adapter-owned only because there was a single adapter to write it
against; a second adapter surfaced that it belonged here instead.
"""

from app.engine.llm_client import generate
from app.engine.models import Finding


class PlanStep:
    def __init__(self, title: str, detail: str, indicator_ids: list[str]) -> None:
        self.title = title
        self.detail = detail
        self.indicator_ids = indicator_ids


class Plan:
    def __init__(self, goal: str, steps: list[PlanStep]) -> None:
        self.goal = goal
        self.steps = steps


class PlanGenerationFailed(Exception):
    """Raised when there ARE open findings but the model's response didn't
    parse into any usable steps (total format failure, or every ADDRESSES
    line came back hallucinated). Deliberately distinct from "no open
    findings" -- an empty Plan.steps means two very different things, and
    the caller must not treat a parse failure as "you're all clean"."""


def open_findings(findings: list[Finding]) -> list[Finding]:
    """Findings a plan should actually cover. Only "pass" is excluded here
    -- a passing finding has nothing to plan for. A non-penalized-but-still-
    actionable severity (e.g. not_started) is deliberately NOT excluded: it
    has no score impact, but there's still a real, useful "how to begin"
    step to write for it."""
    return [f for f in findings if f.severity != "pass"]


def parse_plan(text: str, valid_indicator_ids: set[str]) -> Plan:
    """Defensive line-based parser for the GOAL:/STEP:/ADDRESSES:/DETAIL:
    contract every adapter's plan-prompt template follows -- an LLM won't
    always follow a format instruction exactly, so unrecognized lines are
    just skipped rather than raising, and any id in ADDRESSES not in
    valid_indicator_ids (a hallucinated or mistyped id) is silently dropped
    rather than shown."""
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


def generate_plan(prompt: str, valid_indicator_ids: set[str], *, max_tokens: int = 1800) -> Plan:
    """Sends an already-rendered plan prompt to the model and parses the
    response. Raises PlanGenerationFailed if nothing usable came back --
    the caller must already have checked there ARE open findings before
    calling this (see open_findings()); this function has no opinion on
    that, only on what to do with the model's response."""
    text = generate(prompt, max_tokens=max_tokens)
    plan = parse_plan(text, valid_indicator_ids)
    if not plan.steps:
        raise PlanGenerationFailed("The model's response didn't produce any usable plan steps.")
    return plan
