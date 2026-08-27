"""Checkpoint 6 (issue #2): runs backend/eval/golden_set.yaml through the
real remediation and plan-generation prompts against a live LLM, and scores
the output -- formalizing what earlier checkpoints (Checkpoint 3's demo run,
every live-test verification pass in docs/DECISIONS.md) validated by hand.

Two different scoring strategies, matched to what's actually checkable:
- Remediation cases: LLM-as-judge. The output is free text with no fixed
  right answer, so an automated judge call scores it against the same
  RULES section the writer prompt itself uses (see _JUDGE_PROMPT below) --
  not exact-string-match, which would be meaningless against non-
  deterministic generation.
- Plan cases: mechanical. Whether every open finding actually got covered
  by some step (vs. silently dropped by a hallucinated/malformed ADDRESSES
  id) is an objective, checkable fact -- exactly the failure mode
  plan.py's own defensive parser exists to guard against. This proves that
  guard holds against live output, not just its own unit tests.

Usage: python scripts/run_eval.py
Needs LLM_BASE_URL/LLM_MODEL configured in .env, same as run_demo_assessment.py.
Writes a report to docs/eval_reports/<timestamp>.md and prints a summary.
"""

import re
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.fair.adapter import FairAdapter
from app.adapters.fair.plan import build_fairification_plan
from app.engine.llm_client import generate
from app.engine.models import Answer, Finding

_GOLDEN_SET_PATH = Path(__file__).parent.parent / "eval" / "golden_set.yaml"
_OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs" / "eval_reports"

_SUBJECT_LABEL = "ACE Eval Test Collection"

_CHECK_LABELS = {
    "format": "Follows the SUMMARY:/STEPS: format exactly, no other text before or after",
    "plain_language": (
        "Flag ONLY a bare ALL-CAPS or mixed-case acronym/abbreviation (e.g. 'DOI', 'API', 'RDA', 'PI') that "
        "appears with NO plain-words phrase anywhere in the same sentence explaining what it is. "
        "Do NOT flag ordinary proper-noun names, even if you don't personally know what they are -- Zenodo, "
        "OSF, Dataverse, Vivli, ICD-10, and similar named tools/standards/repositories are NEVER violations "
        "on their own, since this app's own writer prompt explicitly permits naming them as examples. "
        "Do NOT flag common English words like 'IT', 'IDs', or 'IP' used in their ordinary sense. "
        "If in doubt, PASS -- this check exists to catch a genuinely undefined acronym dropped with zero "
        "context, not to police whether every proper noun is individually defined."
    ),
    "no_fair_jargon": 'Never mentions "FAIR principles", indicator codes, or RDA jargon',
    "grounded": (
        "The OUTPUT reflects the person's specific situation rather than reading as boilerplate that could "
        "apply to any dataset. This can show up ANYWHERE in the output (the summary OR a step), and a "
        "paraphrase counts just as much as an exact quote -- e.g. if their note says 'proprietary Excel "
        "macros' and the output says 'Excel macros' or describes the same specific problem in different "
        "words, that IS grounded. Only FAIL this if the output is truly generic and shows no sign the "
        "writer read their specific answer/note at all."
    ),
    "no_invented_facts": "Doesn't name tools/facts not implied by the indicator or their answer",
    "finds_out_not_fixes": "For a don't-know answer, tells them who/where to find out, not how to fix it",
    "length": "Summary and each step are each reasonably concise, not sprawling paragraphs",
    "repository_fits_situation": "If a repository is named, it fits their stated situation (not just a bare 'Zenodo' reflex)",
}

_JUDGE_PROMPT = """You are auditing one piece of AI-generated remediation advice against a
strict style rubric, for an eval harness -- not a live user. Score ONLY the
dimensions listed under CHECKS, and score them against the OUTPUT BEING
AUDITED block ONLY. Be a strict, literal grader: a real violation is a FAIL
even if the overall output reads nicely.

CONTEXT is background so you can judge whether the output is grounded in
their actual situation -- it is NOT part of what you're auditing. A term
that appears only in CONTEXT (their own note, their own answer) and never
in the OUTPUT is not something the OUTPUT needed to explain. Only check
terms that actually appear in the OUTPUT text itself.

CONTEXT (background only, not the thing being audited)
- Severity: {severity}
- Their answer: "{answer_label}"
- Their note: {note}

OUTPUT BEING AUDITED (this is the only text your checks apply to)
---
{output_text}
---

CHECKS (score exactly these, one per line, nothing else)
{checks_block}

For each check, output exactly one line, with the reason (if any) on the
SAME line, no line break before it:
<CHECK_NAME>: PASS
or
<CHECK_NAME>: FAIL <one short sentence saying what's wrong, same line>
"""


def _load_golden_set() -> dict:
    with open(_GOLDEN_SET_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _make_answer(case: dict) -> Answer:
    a = case["answer"]
    return Answer(
        id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        indicator_id=case["indicator_id"],
        raw_answer={"value": a["value"], "label": a["label"]},
        free_text_note=a.get("note"),
        is_dont_know=a.get("is_dont_know", False),
    )


def _judge(*, severity: str, answer_label: str, note: str | None, output_text: str, checks: list[str]) -> dict[str, tuple[bool, str]]:
    checks_block = "\n".join(f"- {c}: {_CHECK_LABELS[c]}" for c in checks)
    prompt = _JUDGE_PROMPT.format(
        severity=severity,
        answer_label=answer_label,
        note=f'"{note}"' if note else "(none)",
        output_text=output_text or "(EMPTY -- the writer produced no text at all)",
        checks_block=checks_block,
    )
    verdict_text = generate(prompt, max_tokens=800, temperature=0.0)
    results: dict[str, tuple[bool, str]] = {}
    for check in checks:
        # Line-anchored per check name, defensively parsed -- same spirit as
        # this project's other marker-line parsing (plan.py's ADDRESSES:,
        # remediation.py's SUMMARY:/STEPS:): a judge that doesn't follow the
        # format exactly is treated as a script-level failure for that
        # check, not silently skipped. The reason is allowed to spill onto
        # following lines (DOTALL) up to the next <CHECK_NAME>: marker or
        # end of string, since the judge doesn't always keep it on one line
        # despite being asked to.
        next_marker = "|".join(re.escape(c) for c in _CHECK_LABELS)
        m = re.search(
            rf"^\s*{re.escape(check)}:\s*(PASS|FAIL)\b(.*?)(?=^\s*(?:{next_marker}):|\Z)",
            verdict_text,
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        if not m:
            results[check] = (False, "judge did not return a parseable verdict for this check")
        else:
            passed = m.group(1).upper() == "PASS"
            results[check] = (passed, m.group(2).strip(" -:"))
    return results


def _run_remediation_cases(adapter: FairAdapter, cases: list[dict]) -> list[dict]:
    indicators_by_id = {q.indicator.id: q.indicator for q in adapter.question_set()}
    results = []
    for case in cases:
        indicator = indicators_by_id[case["indicator_id"]]
        answer = _make_answer(case)
        severity = adapter.score(indicator, answer).severity
        prompt = adapter.render_remediation_prompt(
            indicator=indicator, answer=answer, subject_label=_SUBJECT_LABEL, severity=severity
        )
        t0 = time.perf_counter()
        output_text = generate(prompt)
        elapsed = time.perf_counter() - t0
        verdicts = _judge(
            severity=severity,
            answer_label=case["answer"]["label"],
            note=case["answer"].get("note"),
            output_text=output_text,
            checks=case["checks"],
        )
        results.append(
            {
                "id": case["id"],
                "indicator_id": case["indicator_id"],
                "severity": severity,
                "elapsed": elapsed,
                "output_text": output_text,
                "verdicts": verdicts,
                "passed": all(ok for ok, _ in verdicts.values()),
            }
        )
        print(f"  {case['id']}: {'PASS' if results[-1]['passed'] else 'FAIL'} ({elapsed:.1f}s)")
    return results


def _run_plan_cases(adapter: FairAdapter, cases: list[dict]) -> list[dict]:
    indicators_by_id = {q.indicator.id: q.indicator for q in adapter.question_set()}
    results = []
    for case in cases:
        run_id = uuid.uuid4()
        findings = [
            Finding(
                id=uuid.uuid4(),
                run_id=run_id,
                indicator_id=f["indicator_id"],
                answer_id=uuid.uuid4(),
                severity=f["severity"],
                priority_weight=1,
            )
            for f in case["findings"]
        ]
        expected_ids = {f["indicator_id"] for f in case["findings"]}
        t0 = time.perf_counter()
        plan = build_fairification_plan(findings=findings, indicators_by_id=indicators_by_id, subject_label=_SUBJECT_LABEL)
        elapsed = time.perf_counter() - t0
        addressed_ids = {iid for step in plan.steps for iid in step.indicator_ids}
        missing = expected_ids - addressed_ids
        passed = len(plan.steps) > 0 and not missing
        results.append(
            {
                "id": case["id"],
                "elapsed": elapsed,
                "goal": plan.goal,
                "step_count": len(plan.steps),
                "missing_ids": sorted(missing),
                "passed": passed,
            }
        )
        print(f"  {case['id']}: {'PASS' if passed else 'FAIL'} ({elapsed:.1f}s, {len(plan.steps)} steps, missing={sorted(missing)})")
    return results


def _write_report(remediation_results: list[dict], plan_results: list[dict]) -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
    path = _OUTPUT_DIR / f"{timestamp}.md"

    lines = [f"# Eval run — {timestamp} UTC", ""]
    rem_pass = sum(r["passed"] for r in remediation_results)
    plan_pass = sum(r["passed"] for r in plan_results)
    lines.append(f"**Remediation cases: {rem_pass}/{len(remediation_results)} passed.**")
    lines.append(f"**Plan cases: {plan_pass}/{len(plan_results)} passed.**")
    lines.append("")

    lines.append("## Remediation cases")
    for r in remediation_results:
        lines.append(f"### {r['id']} ({'PASS' if r['passed'] else 'FAIL'}, severity={r['severity']}, {r['elapsed']:.1f}s)")
        lines.append("")
        lines.append("```")
        lines.append(r["output_text"] or "(empty)")
        lines.append("```")
        for check, (ok, reason) in r["verdicts"].items():
            lines.append(f"- **{check}**: {'PASS' if ok else 'FAIL — ' + reason}")
        lines.append("")

    lines.append("## Plan cases")
    for r in plan_results:
        lines.append(f"### {r['id']} ({'PASS' if r['passed'] else 'FAIL'}, {r['elapsed']:.1f}s)")
        lines.append(f"- Goal: {r['goal']}")
        lines.append(f"- Steps generated: {r['step_count']}")
        lines.append(f"- Findings missing from any step: {r['missing_ids'] or 'none'}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    golden_set = _load_golden_set()
    adapter = FairAdapter()

    print(f"Running {len(golden_set['remediation_cases'])} remediation cases...")
    remediation_results = _run_remediation_cases(adapter, golden_set["remediation_cases"])

    print(f"\nRunning {len(golden_set['plan_cases'])} plan cases...")
    plan_results = _run_plan_cases(adapter, golden_set["plan_cases"])

    report_path = _write_report(remediation_results, plan_results)

    rem_pass = sum(r["passed"] for r in remediation_results)
    plan_pass = sum(r["passed"] for r in plan_results)
    total = len(remediation_results) + len(plan_results)
    total_pass = rem_pass + plan_pass
    print(f"\n{total_pass}/{total} cases passed. Full report: {report_path}")
    if total_pass < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
