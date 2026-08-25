"""Hits the real vLLM endpoint -- this is the only test that proves the
plan route's LLM integration and parsing actually work end to end against
real model output, not just that the format-parsing logic (tested without
an LLM in tests/adapters/fair/test_plan.py) is correct in isolation.
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

    all_addressed_ids = {i["indicator_id"] for step in plan["steps"] for i in step["indicators"]}
    # every id the plan references must be a real, currently-open indicator
    valid_open_ids = {"fair.r1-1-license", "fair.r1-data-dictionary"}
    assert all_addressed_ids <= valid_open_ids
    # and the two deliberate gaps should each be covered by some step
    assert all_addressed_ids == valid_open_ids


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
