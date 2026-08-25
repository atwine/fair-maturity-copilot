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

# Line-anchored, not a bare substring search -- a bare `"UPDATE_ANSWER:" in
# text` could misfire if the model's own conversational reply happened to
# echo that phrase (the exact class of bug parse-remediation.ts hit with
# "STEPS:", see docs/HANDOFF.md's 2026-08-25 report-guided-remediation entry).
# Format is `UPDATE_ANSWER: <indicator_id>|<value>` (issue #9) -- a mentor
# conversation is now scoped to a whole plan step, which can bundle several
# indicators, so a confirmed fix has to say which one it resolved. The id
# itself (e.g. "fair.f1-identifier") is dot/hyphen/alnum; matches the ids
# indicators.yaml actually uses. The trailing `(?:\|(.*))?` tolerates a real
# model deviation caught live: instead of a separate NOTE: line, vLLM
# sometimes tacks the note onto the same line with one more `|` --
# `UPDATE_ANSWER: fair.r1-1-license|yes|Added a CC-BY license`. Without this
# the whole line simply failed to match and the raw marker leaked straight
# into what the user sees -- captured here as a fallback note instead.
_ACTION_LINE = re.compile(
    r"^\s*UPDATE_ANSWER:\s*([\w.\-]+)\|(yes|partial|no)(?:\|(.*))?\s*$", re.IGNORECASE | re.MULTILINE
)
_NOTE_LINE = re.compile(r"^\s*NOTE:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


class MentorAction:
    def __init__(self, indicator_id: str, value: str, note: str) -> None:
        self.indicator_id = indicator_id
        self.value = value
        self.note = note


def _extract_action(text: str, valid_indicator_ids: set[str] | None = None) -> tuple[str, MentorAction | None]:
    """Splits the model's raw reply into (display_text, action). The
    UPDATE_ANSWER:/NOTE: lines are a signal to the engine, not part of the
    conversation -- stripped from what's actually shown to the user.
    valid_indicator_ids, when given, silently drops a hallucinated or
    mistyped id rather than trying to apply an update to something that
    isn't part of this step -- same defensive spirit as plan.py's ADDRESSES:
    parsing."""
    match = _ACTION_LINE.search(text)
    if not match:
        return text.strip(), None

    # The marker line is stripped from display_text on every path below,
    # matched or not -- a hallucinated/mistyped indicator id must not leave
    # the raw UPDATE_ANSWER:/NOTE: lines visible to the user just because
    # the *action* itself gets dropped. (An earlier version of this function
    # only stripped it on the success path, which was the same "raw marker
    # leaks into the chat" bug this whole regex's design is meant to avoid,
    # just triggered by an unknown id instead of a note-format deviation.)
    display_text = text[: match.start()].strip()

    indicator_id = match.group(1)
    value = match.group(2).lower()  # already constrained to yes|partial|no by the regex itself
    if valid_indicator_ids is not None and indicator_id not in valid_indicator_ids:
        return display_text, None

    note_match = _NOTE_LINE.search(text)
    inline_note = match.group(3)
    if note_match:
        note = note_match.group(1).strip()
    elif inline_note:
        note = inline_note.strip()
    else:
        note = ""
    display_text = text[: match.start()].strip()
    return display_text, MentorAction(indicator_id=indicator_id, value=value, note=note)


def run_mentor_turn(
    *, system_prompt: str, history: list[MentorMessage], user_text: str, valid_indicator_ids: set[str]
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
    return _extract_action(raw_reply, valid_indicator_ids)
