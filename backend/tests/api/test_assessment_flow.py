"""Fast API tests -- no LLM call, no live network. The report-generation
path (which does call the LLM) is covered separately in test_report_live.py."""


def _create_run(client, subject_label="Test Dataset"):
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": subject_label})
    assert r.status_code == 201
    return r.json()


def test_create_assessment(client):
    run = _create_run(client)
    assert run["status"] == "in_progress"
    assert run["answered_indicator_ids"] == []
    assert run["completed_at"] is None


def test_create_assessment_with_unknown_adapter_404s(client):
    r = client.post("/assessments", json={"adapter_id": "not-a-real-adapter", "subject_label": "x"})
    assert r.status_code == 404


def test_get_assessment_not_found_404s(client):
    r = client.get("/assessments/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_answer_and_reflect_in_get(client):
    run = _create_run(client)
    run_id = run["id"]

    r = client.put(
        f"/assessments/{run_id}/answers/fair.f1-identifier",
        json={"value": "yes", "label": "Yes, clearly true"},
    )
    assert r.status_code == 200
    assert r.json() == {
        "indicator_id": "fair.f1-identifier",
        "value": "yes",
        "label": "Yes, clearly true",
        "note": None,
        "is_dont_know": False,
    }

    r = client.get(f"/assessments/{run_id}")
    assert r.json()["answered_indicator_ids"] == ["fair.f1-identifier"]


def test_answering_twice_updates_not_duplicates(client):
    run = _create_run(client)
    run_id = run["id"]

    client.put(f"/assessments/{run_id}/answers/fair.f1-identifier", json={"value": "no", "label": "No, not true"})
    r = client.put(
        f"/assessments/{run_id}/answers/fair.f1-identifier",
        json={"value": "yes", "label": "Yes, clearly true", "note": "Changed my mind"},
    )
    assert r.status_code == 200
    assert r.json()["value"] == "yes"

    r = client.get(f"/assessments/{run_id}")
    assert r.json()["answered_indicator_ids"] == ["fair.f1-identifier"]  # still just one, not two


def test_dont_know_value_sets_the_flag(client):
    run = _create_run(client)
    run_id = run["id"]
    r = client.put(
        f"/assessments/{run_id}/answers/fair.f1-identifier",
        json={"value": "dont_know", "label": "I don't know"},
    )
    assert r.json()["is_dont_know"] is True


def test_invalid_answer_value_rejected(client):
    run = _create_run(client)
    run_id = run["id"]
    r = client.put(
        f"/assessments/{run_id}/answers/fair.f1-identifier",
        json={"value": "maybe", "label": "Maybe?"},
    )
    assert r.status_code == 422


def test_answer_unknown_indicator_404s(client):
    run = _create_run(client)
    run_id = run["id"]
    r = client.put(
        f"/assessments/{run_id}/answers/not-a-real-indicator",
        json={"value": "yes", "label": "Yes, clearly true"},
    )
    assert r.status_code == 404


def test_complete_with_missing_answers_fails(client):
    run = _create_run(client)
    run_id = run["id"]
    client.put(f"/assessments/{run_id}/answers/fair.f1-identifier", json={"value": "yes", "label": "Yes, clearly true"})

    r = client.post(f"/assessments/{run_id}/complete")
    assert r.status_code == 400
    assert "fair.f2-metadata-richness" in r.json()["detail"]


def test_report_before_completion_fails(client):
    run = _create_run(client)
    run_id = run["id"]
    r = client.get(f"/assessments/{run_id}/report")
    assert r.status_code == 400


def test_report_generation_without_seeded_indicators_gives_clear_error(tmp_path):
    """Regression test for a caught-in-review bug: generating a report
    against a database where scripts/seed_indicators.py was never run
    used to crash with a raw KeyError instead of a clear message."""
    from fastapi.testclient import TestClient
    from sqlmodel import Session, SQLModel, create_engine

    from app.db import get_session
    from app.main import app

    unseeded_engine = create_engine(f"sqlite:///{tmp_path / 'unseeded.db'}")
    SQLModel.metadata.create_all(unseeded_engine)  # tables exist, but no Indicator rows

    def _override():
        with Session(unseeded_engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override
    try:
        with TestClient(app) as unseeded_client:
            run = _create_run(unseeded_client)
            run_id = run["id"]
            from app.adapters.fair.content import load_indicators

            for indicator in load_indicators():
                unseeded_client.put(
                    f"/assessments/{run_id}/answers/{indicator.id}", json={"value": "yes", "label": "Yes, clearly true"}
                )
            unseeded_client.post(f"/assessments/{run_id}/complete")

            r = unseeded_client.get(f"/assessments/{run_id}/report")
            assert r.status_code == 500
            assert "seed_indicators.py" in r.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_can_edit_answers_after_completion(client):
    # Editing after completion is how revisiting a finding from the report
    # works -- no longer blocked. This run never has a report generated, so
    # the rescore-and-refresh path (tested live in test_report_live.py)
    # should safely no-op rather than error.
    from app.adapters.fair.content import load_indicators

    run = _create_run(client)
    run_id = run["id"]
    for indicator in load_indicators():
        client.put(f"/assessments/{run_id}/answers/{indicator.id}", json={"value": "yes", "label": "Yes, clearly true"})

    r = client.post(f"/assessments/{run_id}/complete")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    r = client.put(f"/assessments/{run_id}/answers/fair.f1-identifier", json={"value": "no", "label": "No, not true"})
    assert r.status_code == 200
    assert r.json()["value"] == "no"
