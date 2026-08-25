"""Tests engine/mentor.py's action-line parsing directly — no LLM call
needed, these test the parsing logic against synthetic model output.

The line-anchoring case here is a deliberate regression test for the same
class of bug parse-remediation.ts hit with a bare "STEPS:" substring search
(see docs/HANDOFF.md's 2026-08-25 report-guided-remediation entry): a
conversational reply that happens to mention the phrase "update answer"
mid-sentence must not be misread as the structured action line.
"""

from app.engine.mentor import _extract_action


def test_no_action_line_returns_plain_text_and_no_action():
    text = "That sounds like a good first step -- have you registered a DOI yet?"
    display_text, action = _extract_action(text)
    assert display_text == text
    assert action is None


def test_action_line_is_parsed_and_stripped_from_display_text():
    text = (
        "Great, that resolves this one!\n\n"
        "UPDATE_ANSWER: yes\n"
        "NOTE: Registered a DOI on Zenodo and added it to the README."
    )
    display_text, action = _extract_action(text)
    assert display_text == "Great, that resolves this one!"
    assert action is not None
    assert action.value == "yes"
    assert action.note == "Registered a DOI on Zenodo and added it to the README."


def test_partial_value_is_accepted():
    text = "UPDATE_ANSWER: partial\nNOTE: Drafted a license but not yet published it."
    _, action = _extract_action(text)
    assert action is not None
    assert action.value == "partial"


def test_invalid_value_is_ignored_not_crashed_on():
    text = "UPDATE_ANSWER: maybe\nNOTE: Not sure yet."
    display_text, action = _extract_action(text)
    assert action is None
    assert display_text == text.strip()


def test_mid_sentence_mention_of_the_marker_phrase_is_not_misread_as_an_action():
    # Regression case: only a line-start match on the exact marker counts.
    text = "Once you're ready, I can help you update answer details -- just let me know when you're done."
    display_text, action = _extract_action(text)
    assert action is None
    assert display_text == text.strip()


def test_missing_note_line_still_parses_the_action_with_an_empty_note():
    text = "Nice work.\n\nUPDATE_ANSWER: yes"
    display_text, action = _extract_action(text)
    assert action is not None
    assert action.value == "yes"
    assert action.note == ""
    assert display_text == "Nice work."
