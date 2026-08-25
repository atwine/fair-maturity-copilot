"""Tests engine/mentor.py's action-line parsing directly — no LLM call
needed, these test the parsing logic against synthetic model output.

The line-anchoring case here is a deliberate regression test for the same
class of bug parse-remediation.ts hit with a bare "STEPS:" substring search
(see docs/HANDOFF.md's 2026-08-25 report-guided-remediation entry): a
conversational reply that happens to mention the phrase "update answer"
mid-sentence must not be misread as the structured action line.
"""

from app.engine.mentor import _extract_action


_LICENSE_ID = "fair.r1-1-license"
_PROVENANCE_ID = "fair.r1-2-provenance"
_VALID_IDS = {_LICENSE_ID, _PROVENANCE_ID}


def test_no_action_line_returns_plain_text_and_no_action():
    text = "That sounds like a good first step -- have you registered a DOI yet?"
    display_text, action = _extract_action(text, _VALID_IDS)
    assert display_text == text
    assert action is None


def test_action_line_is_parsed_and_stripped_from_display_text():
    text = (
        "Great, that resolves this one!\n\n"
        f"UPDATE_ANSWER: {_LICENSE_ID}|yes\n"
        "NOTE: Registered a DOI on Zenodo and added it to the README."
    )
    display_text, action = _extract_action(text, _VALID_IDS)
    assert display_text == "Great, that resolves this one!"
    assert action is not None
    assert action.indicator_id == _LICENSE_ID
    assert action.value == "yes"
    assert action.note == "Registered a DOI on Zenodo and added it to the README."


def test_partial_value_is_accepted():
    text = f"UPDATE_ANSWER: {_PROVENANCE_ID}|partial\nNOTE: Drafted a license but not yet published it."
    _, action = _extract_action(text, _VALID_IDS)
    assert action is not None
    assert action.indicator_id == _PROVENANCE_ID
    assert action.value == "partial"


def test_invalid_value_is_ignored_not_crashed_on():
    text = f"UPDATE_ANSWER: {_LICENSE_ID}|maybe\nNOTE: Not sure yet."
    display_text, action = _extract_action(text, _VALID_IDS)
    assert action is None
    assert display_text == text.strip()


def test_unknown_indicator_id_is_ignored_and_the_marker_is_still_stripped():
    # Defensive against a hallucinated or mistyped id -- same spirit as
    # plan.py's ADDRESSES: parsing dropping ids outside the valid set.
    # Regression: an earlier version left the raw UPDATE_ANSWER:/NOTE: lines
    # in display_text on this exact path -- the same class of "marker leaks
    # into the chat" bug the inline-note fallback above exists to prevent,
    # just triggered by an unknown id instead of a note-format deviation.
    text = "Sounds good!\n\nUPDATE_ANSWER: fair.not-a-real-indicator|yes\nNOTE: Done."
    display_text, action = _extract_action(text, _VALID_IDS)
    assert action is None
    assert display_text == "Sounds good!"
    assert "UPDATE_ANSWER" not in display_text


def test_mid_sentence_mention_of_the_marker_phrase_is_not_misread_as_an_action():
    # Regression case: only a line-start match on the exact marker counts.
    text = "Once you're ready, I can help you update answer details -- just let me know when you're done."
    display_text, action = _extract_action(text, _VALID_IDS)
    assert action is None
    assert display_text == text.strip()


def test_missing_note_line_still_parses_the_action_with_an_empty_note():
    text = f"Nice work.\n\nUPDATE_ANSWER: {_LICENSE_ID}|yes"
    display_text, action = _extract_action(text, _VALID_IDS)
    assert action is not None
    assert action.indicator_id == _LICENSE_ID
    assert action.value == "yes"
    assert action.note == ""
    assert display_text == "Nice work."


def test_note_tacked_onto_the_action_line_with_a_third_pipe_is_still_parsed():
    # Regression case: caught live against real vLLM output. Instead of a
    # separate NOTE: line, the model sometimes writes the note inline with
    # one more `|` -- without tolerating this, the whole line failed to
    # match at all and the raw marker leaked straight into the user-visible
    # reply (see docs/DECISIONS.md).
    text = f"That's a great step forward.\n\nUPDATE_ANSWER: {_LICENSE_ID}|yes|Added CC-BY 4.0 license statement"
    display_text, action = _extract_action(text, _VALID_IDS)
    assert action is not None
    assert action.indicator_id == _LICENSE_ID
    assert action.value == "yes"
    assert action.note == "Added CC-BY 4.0 license statement"
    assert display_text == "That's a great step forward."
    assert "UPDATE_ANSWER" not in display_text


def test_explicit_note_line_wins_over_an_inline_one_if_somehow_both_are_present():
    text = f"UPDATE_ANSWER: {_LICENSE_ID}|yes|inline version\nNOTE: the real, separate-line version"
    _, action = _extract_action(text, _VALID_IDS)
    assert action is not None
    assert action.note == "the real, separate-line version"
