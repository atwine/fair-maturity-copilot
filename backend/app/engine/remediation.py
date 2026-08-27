"""The remediation-writer stage. The engine owns *how* a remediation gets
generated and checked; the adapter owns *what* goes into the prompt (see
app/adapters/fair/prompts/remediation.jinja, built in a later milestone).

This module takes an already-rendered prompt string — it has no idea what
standard produced it.
"""

import re

from app.engine.llm_client import generate
from app.engine.models import Answer, Finding, RemediationDraft
from app.config import settings

_BANNED_TERMS = re.compile(r"\bFAIR principle\b|\bRDA-[A-Z0-9.\-]+\b", re.IGNORECASE)
# A passing finding gets just a short SUMMARY line (as few as ~10 words); a
# gap gets a SUMMARY plus 2-3 STEPS. Wide enough to cover both without being
# a no-op check.
_WORD_COUNT_RANGE = (5, 220)


def _grounding_ok(text: str, answer: Answer, severity: str) -> tuple[bool, str | None]:
    word_count = len(text.split())
    if not (_WORD_COUNT_RANGE[0] <= word_count <= _WORD_COUNT_RANGE[1]):
        return False, f"word count {word_count} outside {_WORD_COUNT_RANGE}"
    if _BANNED_TERMS.search(text):
        return False, "contains banned jargon (FAIR principle / RDA code)"

    # "I don't know" answers deliberately get generic "who to ask / where to
    # check" guidance (see prompts/remediation.jinja) rather than a fix tied
    # to specifics of what's often a thin or empty note — requiring overlap
    # here would penalize the model for following that instruction correctly.
    # A "pass" note is similarly generic by design (a short "why this is
    # fine" line) and its only reference material is often just a bare
    # "Yes, clearly true" label with no real content to ground against.
    # A "not_started" answer gets the same exemption for the same reason: its
    # guidance is a generic "here's how to begin" (see issue #16), and the
    # answer it's grounded against is typically just as thin.
    if answer.is_dont_know or severity in {"pass", "not_started"}:
        return True, None

    # Reference-grounding: the output should overlap with something the user
    # actually said, or it could have been written with zero knowledge of
    # their specific situation.
    reference_text = " ".join(
        filter(None, [answer.raw_answer.get("label"), answer.free_text_note])
    ).lower()
    reference_tokens = {t for t in re.findall(r"[a-z]{4,}", reference_text)}
    output_tokens = {t for t in re.findall(r"[a-z]{4,}", text.lower())}
    if reference_tokens and not (reference_tokens & output_tokens):
        return False, "no overlap with the user's actual answer/note — likely generic"
    return True, None


def write_remediation(
    *,
    finding: Finding,
    answer: Answer,
    prompt: str,
    prompt_version: str,
) -> RemediationDraft:
    text = generate(prompt)
    passed, notes = _grounding_ok(text, answer, finding.severity)
    return RemediationDraft(
        finding_id=finding.id,
        llm_model_id=settings.llm_model,
        prompt_version=prompt_version,
        remediation_text=text,
        grounding_check_passed=passed,
        grounding_check_notes=notes,
    )
