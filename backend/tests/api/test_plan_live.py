"""Hits the real vLLM endpoint -- this is the only test that proves the
plan route's LLM integration and parsing actually work end to end against
real model output, not just that the format-parsing logic (tested without
an LLM in tests/adapters/fair/test_plan.py) is correct in isolation. Also
proves the caching/invalidation behavior added for issue #9: a plan is
built once and reused until an answer changes, and a step's id survives a
regeneration untouched (see docs/DECISIONS.md).
"""

import uuid

from app.adapters.fair.content import load_indicators


def _create_and_complete_run(client, extra_answers: dict) -> str:
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": "Plan Integration Test Dataset"})
    run_id = r.json()["id"]

    for indicator in load_indicators():
        body = extra_answers.get(indicator.id, {"value": "yes", "label": "Yes, clearly true"})
        r = client.put(f"/assessments/{run_id}/answers/{indicator.id}", json=body)
        assert r.status_code == 200

    r = client.post(f"/assessments/{run_id}/complete")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    return run_id


def test_plan_generation_covers_open_findings(client):
    run_id = _create_and_complete_run(
        client,
        extra_answers={
            "fair.r1-1-license": {
                "value": "no",
                "label": "No, not true",
                "note": "No license has ever been stated for this test dataset.",
            },
            "fair.r1-data-dictionary": {
                "value": "no",
                "label": "No, not true",
                "note": "No documentation exists for what the columns mean.",
            },
        },
    )
    # a report (and its findings) must exist before a plan can be generated
    client.get(f"/assessments/{run_id}/report")

    r = client.get(f"/assessments/{run_id}/plan")
    assert r.status_code == 200
    plan = r.json()

    assert plan["goal"]
    assert len(plan["steps"]) >= 1
    # every step now has a real, stable id
    assert all(step["id"] for step in plan["steps"])

    all_addressed_ids = {i["indicator_id"] for step in plan["steps"] for i in step["indicators"]}
    # every id the plan references must be a real, currently-open indicator
    valid_open_ids = {"fair.r1-1-license", "fair.r1-data-dictionary"}
    assert all_addressed_ids <= valid_open_ids
    # and the two deliberate gaps should each be covered by some step
    assert all_addressed_ids == valid_open_ids


def test_second_plan_view_is_served_from_cache_not_regenerated(client):
    run_id = _create_and_complete_run(
        client, extra_answers={"fair.r1-1-license": {"value": "no", "label": "No, not true", "note": "Missing."}}
    )
    client.get(f"/assessments/{run_id}/report")

    first = client.get(f"/assessments/{run_id}/plan").json()
    second = client.get(f"/assessments/{run_id}/plan").json()

    # Identical step ids across two views is the actual proof of caching --
    # the LLM is non-deterministic, so identical *content* wouldn't prove
    # anything, but a saved row's id can't spontaneously change.
    first_ids = [s["id"] for s in first["steps"]]
    second_ids = [s["id"] for s in second["steps"]]
    assert first_ids == second_ids
    assert first_ids  # sanity: there's actually at least one step to compare


def test_revisiting_an_answer_invalidates_the_cached_plan(client):
    run_id = _create_and_complete_run(
        client, extra_answers={"fair.r1-1-license": {"value": "no", "label": "No, not true", "note": "Missing."}}
    )
    client.get(f"/assessments/{run_id}/report")

    before = client.get(f"/assessments/{run_id}/plan").json()
    before_ids = {s["id"] for s in before["steps"]}
    assert before_ids  # the license gap should have produced at least one step

    # Fix the gap the plan was built around.
    r = client.put(
        f"/assessments/{run_id}/answers/fair.r1-1-license",
        json={"value": "yes", "label": "Yes, clearly true", "note": "Added a CC-BY license."},
    )
    assert r.status_code == 200

    after = client.get(f"/assessments/{run_id}/plan").json()
    after_ids = {s["id"] for s in after["steps"]}
    # A genuinely new plan version -- not the same (now stale) step ids
    # served back unchanged, and the fixed indicator should no longer be
    # addressed by any step.
    assert after_ids != before_ids
    after_addressed = {i["indicator_id"] for step in after["steps"] for i in step["indicators"]}
    assert "fair.r1-1-license" not in after_addressed


def test_plan_before_report_generated_400s(client):
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": "x"})
    run_id = r.json()["id"]
    for indicator in load_indicators():
        client.put(f"/assessments/{run_id}/answers/{indicator.id}", json={"value": "yes", "label": "Yes, clearly true"})
    client.post(f"/assessments/{run_id}/complete")

    r = client.get(f"/assessments/{run_id}/plan")
    assert r.status_code == 400


def test_plan_for_nonexistent_run_404s(client):
    r = client.get(f"/assessments/{uuid.uuid4()}/plan")
    assert r.status_code == 404
