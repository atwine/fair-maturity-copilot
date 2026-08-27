"""Tests engine/remediation.py's grounding check directly — no LLM call
needed, these test the checking logic against synthetic text.

The dont_know-bypass case here is a regression test for a real bug found
during the Checkpoint 3 demo run against live vLLM output: a correct,
appropriate "who to ask" response for a don't-know answer with a thin note
was being rejected for lacking word overlap with that note, even though the
prompt design deliberately asks for generic guidance in that case.
"""

from uuid import uuid4

from app.engine.models import Answer
from app.engine.remediation import _grounding_ok


def _answer(*, label="No, not true", note=None, dont_know=False) -> Answer:
    return Answer(
        run_id=uuid4(),
        indicator_id="fair.f1-identifier",
        raw_answer={"value": "no", "label": label},
        free_text_note=note,
        is_dont_know=dont_know,
    )


def test_rejects_text_outside_word_count_band():
    ok, notes = _grounding_ok("Too short.", _answer(note="It's just a CSV in a Drive folder."), "major_gap")
    assert not ok
    assert "word count" in notes


def test_rejects_banned_jargon():
    text = (
        "You're missing a FAIR principle here, specifically RDA-F1-01M, and should fix it by "
        "adding a persistent identifier so your dataset is easier to find and reuse over time reliably." * 1
    )
    ok, notes = _grounding_ok(text, _answer(note="It's just a CSV in a Drive folder."), "major_gap")
    assert not ok
    assert "jargon" in notes


def test_rejects_generic_text_with_no_overlap_with_the_users_note():
    generic_text = (
        "You should improve your data management practices by following best practices for "
        "documentation and metadata. This will help other researchers understand and reuse your "
        "work more effectively over time, which benefits the broader research community as a whole today."
    )
    ok, notes = _grounding_ok(
        generic_text, _answer(note="It's just a CSV sitting in a shared Google Drive folder."), "major_gap"
    )
    assert not ok
    assert "overlap" in notes


def test_accepts_text_that_references_the_users_note():
    grounded_text = (
        "Right now this dataset is just a CSV file sitting in a shared Google Drive folder with no "
        "formal record. Assigning it a DOI through Zenodo or your institutional repository would give "
        "it a permanent identifier that survives even if the Drive folder is ever reorganized or deleted."
    )
    ok, notes = _grounding_ok(
        grounded_text, _answer(note="It's just a CSV sitting in a shared Google Drive folder."), "major_gap"
    )
    assert ok
    assert notes is None


def test_dont_know_answers_bypass_the_overlap_check():
    # A correct "who to ask" response for a thin dont_know note naturally
    # won't share words with that note — this must not be rejected for it.
    who_to_ask_text = (
        "You can start by checking your dataset's metadata record or data-sharing agreement to see if "
        "a reuse license or usage terms are stated. If you can't find it there, reach out to whoever "
        "set up your repository account or your organization's data manager to ask about the terms."
    )
    ok, notes = _grounding_ok(who_to_ask_text, _answer(note="This has never come up.", dont_know=True), "unknown")
    assert ok
    assert notes is None


def test_pass_findings_bypass_the_overlap_check():
    # A "why this is fine" note for a passing finding naturally won't share
    # words with a bare "Yes, clearly true" label — this must not be
    # rejected for it, same rationale as the dont_know bypass above.
    praise_text = "You already have a permanent identifier assigned through your institutional repository."
    ok, notes = _grounding_ok(praise_text, _answer(label="Yes, clearly true"), "pass")
    assert ok
    assert notes is None


def test_not_started_findings_bypass_the_overlap_check():
    # Issue #16: a "not_started" answer gets generic "here's how to begin"
    # guidance (the harmonization adapter's own remediation prompt), same
    # spirit as the dont_know/pass bypasses above — it naturally won't share
    # words with a thin "Not started yet" label either.
    getting_started_text = (
        "A good first step is agreeing on one shared field name and format for this concept across "
        "every site, even before anything else is standardized, so later work has something to build on."
    )
    ok, notes = _grounding_ok(
        getting_started_text, _answer(label="Not started yet"), "not_started"
    )
    assert ok
    assert notes is None
