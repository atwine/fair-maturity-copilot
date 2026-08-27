"""Tests engine/mentor.py's tool-call parsing directly — no LLM call
needed, these test the parsing logic against synthetic
confirm_indicator_fix tool calls (issue #15 -- this used to test a
marker-line regex instead; see git history on this file and on
mentor.py for the text-based version this replaced).

_FakeToolCall below mimics just enough of an OpenAI ChatCompletionMessage-
ToolCall shape (a `.function.arguments` JSON string) for _parse_tool_call
to consume, without depending on the real SDK's classes.
"""

import json
from types import SimpleNamespace

from app.engine.mentor import _parse_tool_call


_LICENSE_ID = "fair.r1-1-license"
_PROVENANCE_ID = "fair.r1-2-provenance"
_VALID_IDS = {_LICENSE_ID, _PROVENANCE_ID}


def _fake_tool_call(arguments) -> SimpleNamespace:
    """arguments can be a dict (JSON-encoded here) or a raw string, to also
    cover the "arguments isn't valid JSON" case."""
    raw = arguments if isinstance(arguments, str) else json.dumps(arguments)
    return SimpleNamespace(function=SimpleNamespace(arguments=raw))


def test_a_valid_call_is_parsed_into_display_text_and_action():
    call = _fake_tool_call(
        {
            "indicator_id": _LICENSE_ID,
            "new_value": "yes",
            "note": "Registered a DOI on Zenodo and added it to the README.",
            "reply_to_user": "Great, that resolves this one!",
        }
    )
    display_text, action = _parse_tool_call(call, _VALID_IDS)
    assert display_text == "Great, that resolves this one!"
    assert action is not None
    assert action.indicator_id == _LICENSE_ID
    assert action.value == "yes"
    assert action.note == "Registered a DOI on Zenodo and added it to the README."


def test_partial_value_is_accepted():
    call = _fake_tool_call(
        {
            "indicator_id": _PROVENANCE_ID,
            "new_value": "partial",
            "note": "Drafted a license but not yet published it.",
            "reply_to_user": "That's real progress -- let's finish it.",
        }
    )
    _, action = _parse_tool_call(call, _VALID_IDS)
    assert action is not None
    assert action.indicator_id == _PROVENANCE_ID
    assert action.value == "partial"


def test_missing_note_is_treated_as_an_empty_note_not_an_error():
    call = _fake_tool_call({"indicator_id": _LICENSE_ID, "new_value": "yes", "reply_to_user": "Nice work."})
    display_text, action = _parse_tool_call(call, _VALID_IDS)
    assert action is not None
    assert action.note == ""
    assert display_text == "Nice work."


def test_invalid_value_is_ignored_not_crashed_on():
    call = _fake_tool_call(
        {"indicator_id": _LICENSE_ID, "new_value": "maybe", "reply_to_user": "Let me make sure I understand."}
    )
    display_text, action = _parse_tool_call(call, _VALID_IDS)
    assert action is None
    # The reply is still shown -- a malformed value shouldn't also hide a
    # perfectly good, independent piece of text meant for the user.
    assert display_text == "Let me make sure I understand."


def test_unknown_indicator_id_drops_the_action_but_keeps_the_reply():
    # Defensive against a hallucinated or mistyped id -- same spirit as
    # plan.py's ADDRESSES: parsing dropping ids outside the valid set.
    call = _fake_tool_call(
        {"indicator_id": "fair.not-a-real-indicator", "new_value": "yes", "reply_to_user": "Sounds good!"}
    )
    display_text, action = _parse_tool_call(call, _VALID_IDS)
    assert action is None
    assert display_text == "Sounds good!"


def test_malformed_arguments_json_does_not_crash():
    # Regression-shaped for the same class of real-world model deviation
    # the old marker-line parser had to tolerate -- here, defends against a
    # model emitting arguments that don't even parse as JSON.
    call = _fake_tool_call("{not valid json")
    display_text, action = _parse_tool_call(call, _VALID_IDS)
    assert action is None
    assert display_text == ""


def test_arguments_that_parse_but_are_not_an_object_does_not_crash():
    call = _fake_tool_call("[]")
    display_text, action = _parse_tool_call(call, _VALID_IDS)
    assert action is None
    assert display_text == ""


def test_no_valid_indicator_ids_filter_means_any_known_shaped_id_is_accepted():
    # valid_indicator_ids=None (the parameter's documented default) skips
    # the membership check entirely -- used nowhere in this codebase today,
    # but exercised directly since _extract_action's predecessor supported
    # the same default and a caller could reasonably rely on it.
    call = _fake_tool_call({"indicator_id": "fair.anything", "new_value": "yes", "reply_to_user": "Great!"})
    _, action = _parse_tool_call(call, None)
    assert action is not None
    assert action.indicator_id == "fair.anything"
