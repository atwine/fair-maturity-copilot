"""The mentor conversation engine (Checkpoint 9). Standard-agnostic: an
adapter supplies the system prompt (grounding + tone); this module owns how
a turn actually runs and how a confirmed-fix line in the model's reply gets
parsed out and turned into a real action.

Deliberately NOT built on the OpenAI-compatible "tools"/function-calling API
-- a self-hosted vLLM deployment isn't guaranteed to be launched with tool-
call support enabled for a given model, and this codebase already has a
proven, simpler pattern for exactly this kind of structured LLM output: a
defensively-parsed marker line (see plan.py's GOAL:/STEP:/ADDRESSES: and
parse-remediation.ts's SUMMARY:/STEPS:). Reusing that pattern here keeps the
mentor's one real capability -- confirming a fix live in chat re-scores the
assessment via the existing answer-update path -- reliable without a new,
unverified infra dependency.
"""

import re

from app.engine.llm_client import generate_chat
from app.engine.models import MentorMessage

_VALID_UPDATE_VALUES = {"yes", "partial", "no"}

# Line-anchored, not a bare substring search -- a bare `"UPDATE_ANSWER:" in
# text` could misfire if the model's own conversational reply happened to
# echo that phrase (the exact class of bug parse-remediation.ts hit with
# "STEPS:", see docs/HANDOFF.md's 2026-08-25 report-guided-remediation entry).
_ACTION_LINE = re.compile(r"^\s*UPDATE_ANSWER:\s*(yes|partial|no)\s*$", re.IGNORECASE | re.MULTILINE)
_NOTE_LINE = re.compile(r"^\s*NOTE:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


class MentorAction:
    def __init__(self, value: str, note: str) -> None:
        self.value = value
        self.note = note


def _extract_action(text: str) -> tuple[str, MentorAction | None]:
    """Splits the model's raw reply into (display_text, action). The
    UPDATE_ANSWER:/NOTE: lines are a signal to the engine, not part of the
    conversation -- stripped from what's actually shown to the user."""
    match = _ACTION_LINE.search(text)
    if not match:
        return text.strip(), None

    value = match.group(1).lower()
    if value not in _VALID_UPDATE_VALUES:
        return text.strip(), None

    note_match = _NOTE_LINE.search(text)
    note = note_match.group(1).strip() if note_match else ""
    display_text = text[: match.start()].strip()
    return display_text, MentorAction(value=value, note=note)


def run_mentor_turn(
    *, system_prompt: str, history: list[MentorMessage], user_text: str
) -> tuple[str, MentorAction | None]:
    """Runs one turn: system prompt + prior history + the new user message,
    one LLM call, returns the text to show the user plus any action it
    should trigger. No database access here -- callers own persisting the
    MentorMessage rows and actually applying the action (calling into the
    existing answer-update/rescore machinery), mirroring how
    remediation.py/plan.py stay pure functions of their inputs."""
    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        role = "assistant" if m.role == "mentor" else "user"
        messages.append({"role": role, "content": m.content})
    messages.append({"role": "user", "content": user_text})

    raw_reply = generate_chat(messages)
    return _extract_action(raw_reply)
