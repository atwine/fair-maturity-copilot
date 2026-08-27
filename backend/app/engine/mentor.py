"""The mentor conversation engine (Checkpoint 9). Standard-agnostic: an
adapter supplies the system prompt (grounding + tone); this module owns how
a turn actually runs and how a confirmed fix gets turned into a real action.

Built on the OpenAI-compatible "tools"/function-calling API (issue #15) --
this used to be a defensively-parsed marker line instead (like plan.py's
GOAL:/STEP:/ADDRESSES: and parse-remediation.ts's SUMMARY:/STEPS: still are),
deliberately avoided at the time because a self-hosted vLLM deployment isn't
guaranteed to be launched with tool-call support enabled for a given model.
That concern was real but no longer speculative: both this project's actual
vLLM endpoint and its OpenRouter fallback were confirmed live to return
correct structured tool calls before this switch was made (see
docs/DECISIONS.md). The marker-line approach had already broken twice in
production use (see git history on this file) from small formatting drift --
a real model-shaped a note onto the action line with an extra "|" once, and
could in principle drift in some other way again; a declared tool's argument
shape is enforced by the provider, not hoped for from a regex."""

import json

from app.engine.llm_client import generate_chat, generate_chat_with_tools
from app.engine.models import MentorMessage

# The model's whole conversational reply is carried as this tool's own
# reply_to_user argument, not as separate free-text content -- most
# providers stop writing plain content the moment they decide to call a
# tool, so asking for both in the same turn (one call, not a multi-step
# tool-result round trip) means the "thing to say back" has to live inside
# the structured call itself when a fix is being confirmed.
_CONFIRM_FIX_TOOL = {
    "type": "function",
    "function": {
        "name": "confirm_indicator_fix",
        "description": (
            "Call this only when the person's latest message clearly describes "
            "having already completed a real fix for one of this step's "
            "indicators -- not for general conversation, questions, or something "
            "they're still planning to do. Never call this if you are unsure "
            "which indicator they mean."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "indicator_id": {
                    "type": "string",
                    "description": "The exact id of the indicator being confirmed, from the '(id: ...)' tag given for it in the system prompt.",
                },
                "new_value": {
                    "type": "string",
                    "enum": ["yes", "partial", "no"],
                    "description": "How completely this indicator is now satisfied: 'yes' if fully resolved, 'partial' if genuinely improved but incomplete.",
                },
                "note": {
                    "type": "string",
                    "description": "A short, plain paraphrase (under 15 words) of what the person said they did, for the record.",
                },
                "reply_to_user": {
                    "type": "string",
                    "description": (
                        "Your normal, warm conversational reply acknowledging this -- exactly what "
                        "you would otherwise have written directly. This is the only thing the person "
                        "will actually see, so it must read like a real reply, not a status message."
                    ),
                },
            },
            "required": ["indicator_id", "new_value", "reply_to_user"],
        },
    },
}


class MentorAction:
    def __init__(self, indicator_id: str, value: str, note: str) -> None:
        self.indicator_id = indicator_id
        self.value = value
        self.note = note


def _parse_tool_call(tool_call, valid_indicator_ids: set[str] | None) -> tuple[str, MentorAction | None]:
    """Turns one confirm_indicator_fix call into (display_text, action).
    display_text always comes from reply_to_user when it's present, even if
    the action itself gets dropped below -- a hallucinated or malformed
    indicator_id/new_value shouldn't also hide a perfectly good reply, same
    defensive spirit as plan.py's ADDRESSES: parsing dropping only the
    invalid id, not the whole step."""
    try:
        args = json.loads(tool_call.function.arguments)
    except (TypeError, ValueError):
        return "", None
    if not isinstance(args, dict):
        return "", None

    display_text = str(args.get("reply_to_user") or "").strip()
    indicator_id = args.get("indicator_id")
    value = args.get("new_value")
    if (
        not isinstance(indicator_id, str)
        or value not in {"yes", "partial", "no"}
        or (valid_indicator_ids is not None and indicator_id not in valid_indicator_ids)
    ):
        return display_text, None

    note = str(args.get("note") or "").strip()
    return display_text, MentorAction(indicator_id=indicator_id, value=value, note=note)


def run_mentor_turn(
    *,
    system_prompt: str,
    history: list[MentorMessage],
    user_text: str,
    valid_indicator_ids: set[str],
    allow_tool_call: bool = True,
) -> tuple[str, MentorAction | None]:
    """Runs one turn: system prompt + prior history + the new user message,
    one LLM call, returns the text to show the user plus any action it
    should trigger. No database access here -- callers own persisting the
    MentorMessage rows and actually applying the action (calling into the
    existing answer-update/rescore machinery), mirroring how
    remediation.py/plan.py stay pure functions of their inputs.

    allow_tool_call=False skips offering confirm_indicator_fix at all --
    for the opening greeting (empty history, a synthetic "say hi" user_text),
    not a real conversation turn a fix could have been confirmed in. Without
    this, live testing against real vLLM showed the model reliably calls the
    tool anyway on that very first turn (nothing to confirm yet), and its
    reply_to_user argument came back genuinely empty often enough to produce
    a blank opening chat bubble -- the routes_mentor.py /start handler
    already discards any action from this call, so offering the tool there
    bought nothing but that failure mode."""
    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        role = "assistant" if m.role == "mentor" else "user"
        messages.append({"role": role, "content": m.content})
    messages.append({"role": "user", "content": user_text})

    if not allow_tool_call:
        return generate_chat(messages), None

    content, tool_calls = generate_chat_with_tools(messages, tools=[_CONFIRM_FIX_TOOL])
    if tool_calls:
        # This conversation can only usefully confirm one fix per turn (see
        # docs/DECISIONS.md v22) -- if the model somehow returns more than
        # one call, take the first and ignore the rest rather than guessing
        # which one is "the" real answer.
        return _parse_tool_call(tool_calls[0], valid_indicator_ids)
    return content, None
