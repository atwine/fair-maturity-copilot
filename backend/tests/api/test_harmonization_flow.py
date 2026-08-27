"""Fast API tests for the harmonization-v0 adapter -- no LLM call, no live
network. See tests/api/test_assessment_flow.py for the identical pattern
against fair-v0. The live report/plan generation path is covered separately
in test_harmonization_live.py.
"""

from app.adapters.harmonization.content import load_indicators


def _create_run(client, subject_label="Test Consortium"):
    r = client.post("/assessments", json={"adapter_id": "harmonization-v0", "subject_label": subject_label})
    assert r.status_code == 201
    return r.json()


def test_create_harmonization_assessment(client):
    run = _create_run(client)
    assert run["status"] == "in_progress"
    assert run["answered_indicator_ids"] == []


def test_not_started_is_a_valid_answer_value(client):
    # Issue #16: the 5th answer value must actually be accepted, not just
    # rejected by the old hardcoded 4-value global set.
    run = _create_run(client)
    run_id = run["id"]
    r = client.put(
        f"/assessments/{run_id}/answers/harmonization.h4-linkage-key",
        json={"value": "not_started", "label": "We haven't started this yet"},
    )
    assert r.status_code == 200
    assert r.json()["value"] == "not_started"
    assert r.json()["is_dont_know"] is False


def test_not_started_is_still_rejected_for_the_fair_adapter(client):
    # The per-question validation (routes_answers.py) must stay scoped to
    # what THIS adapter's question actually offers -- fair-v0's 12
    # questions never gained a 5th option, so this must still 422.
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": "x"})
    run_id = r.json()["id"]
    r = client.put(
        f"/assessments/{run_id}/answers/fair.f1-identifier",
        json={"value": "not_started", "label": "We haven't started this yet"},
    )
    assert r.status_code == 422


def test_complete_all_six_including_a_not_started_answer(client):
    run = _create_run(client)
    run_id = run["id"]
    indicators = load_indicators()
    assert len(indicators) == 6

    for indicator in indicators[:-1]:
        client.put(
            f"/assessments/{run_id}/answers/{indicator.id}", json={"value": "yes", "label": "Yes, clearly true"}
        )
    client.put(
        f"/assessments/{run_id}/answers/{indicators[-1].id}",
        json={"value": "not_started", "label": "We haven't started this yet"},
    )

    r = client.post(f"/assessments/{run_id}/complete")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_invalid_answer_value_still_rejected(client):
    run = _create_run(client)
    run_id = run["id"]
    r = client.put(
        f"/assessments/{run_id}/answers/harmonization.h1-field-names",
        json={"value": "maybe", "label": "Maybe?"},
    )
    assert r.status_code == 422
