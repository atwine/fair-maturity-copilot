"""Hits the real LLM endpoint -- proves the harmonization adapter's own
remediation/plan prompts (new content, issue #16) actually produce well-
formed output against a real model, not just that the format-parsing logic
is correct in isolation (tested without an LLM in
tests/adapters/harmonization/test_plan.py).

Deliberately leaner than test_report_live.py/test_plan_live.py's full
mirror for fair-v0: the *route* mechanics (caching, concurrent-request
dedup, revisit-rescoring) are engine-level code already proven live against
fair-v0 -- re-proving them here against a second adapter would just be
redundant LLM calls for zero new coverage. What's actually new here is the
not_started severity's behavior end to end, so that's what these two tests
target.
"""

from app.adapters.harmonization.content import load_indicators


def _create_and_complete_run(client, extra_answers: dict) -> str:
    r = client.post(
        "/assessments", json={"adapter_id": "harmonization-v0", "subject_label": "Harmonization Live Test Consortium"}
    )
    run_id = r.json()["id"]

    for indicator in load_indicators():
        body = extra_answers.get(indicator.id, {"value": "yes", "label": "Yes, clearly true"})
        r = client.put(f"/assessments/{run_id}/answers/{indicator.id}", json=body)
        assert r.status_code == 200

    r = client.post(f"/assessments/{run_id}/complete")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    return run_id


def test_not_started_finding_gets_real_remediation_and_is_excluded_from_score(client):
    run_id = _create_and_complete_run(
        client,
        extra_answers={
            "harmonization.h4-linkage-key": {"value": "not_started", "label": "We haven't started this yet"},
        },
    )

    r = client.get(f"/assessments/{run_id}/report")
    assert r.status_code == 200
    report = r.json()

    not_started = next(f for f in report["findings"] if f["indicator_id"] == "harmonization.h4-linkage-key")
    assert not_started["severity"] == "not_started"
    assert not_started["remediation_text"], "not_started finding has no remediation text"

    # 5 real passes + 1 not_started (excluded from scoring entirely) must
    # score identically to a run of 6 real passes -- a genuine 100, not
    # something dragged down by treating not_started as a fail.
    assert report["score"] == 100.0


def test_not_started_finding_gets_a_real_plan_step_not_excluded_like_pass(client):
    run_id = _create_and_complete_run(
        client,
        extra_answers={
            "harmonization.h4-linkage-key": {"value": "not_started", "label": "We haven't started this yet"},
        },
    )
    client.get(f"/assessments/{run_id}/report")

    r = client.get(f"/assessments/{run_id}/plan")
    assert r.status_code == 200
    plan = r.json()

    assert plan["goal"]
    assert len(plan["steps"]) >= 1
    all_addressed_ids = {i["indicator_id"] for step in plan["steps"] for i in step["indicators"]}
    # the not_started item has no score impact, but it must still get a
    # real "how to begin" step -- unlike a passing finding, which gets none
    assert "harmonization.h4-linkage-key" in all_addressed_ids
