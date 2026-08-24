"""Hits the real vLLM endpoint -- slower than the rest of the suite (a
handful of live generations), but this is the only test that proves the
report route's LLM integration actually works end to end, not just that
the surrounding routes are wired correctly. Mostly "yes" answers to keep
the LLM call count (and runtime) low; two deliberate gaps to exercise
scoring, remediation, and the regenerate endpoint.
"""

from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from sqlmodel import Session, select

from app.adapters.fair.content import load_indicators
from app.engine.models import Finding, Report


def _create_and_complete_run(client, extra_answers: dict) -> str:
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": "API Integration Test Dataset"})
    run_id = r.json()["id"]

    for indicator in load_indicators():
        body = extra_answers.get(indicator.id, {"value": "yes", "label": "Yes, clearly true"})
        r = client.put(f"/assessments/{run_id}/answers/{indicator.id}", json=body)
        assert r.status_code == 200

    r = client.post(f"/assessments/{run_id}/complete")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    return run_id


def test_report_generation_scoring_and_caching(client):
    run_id = _create_and_complete_run(
        client,
        extra_answers={
            "fair.r1-1-license": {
                "value": "no",
                "label": "No, not true",
                "note": "No license has ever been stated for this test dataset.",
            },
            "fair.a2-metadata-persistence": {"value": "dont_know", "label": "I don't know"},
        },
    )

    r = client.get(f"/assessments/{run_id}/report")
    assert r.status_code == 200
    report = r.json()

    assert 0 <= report["score"] <= 100
    non_pass = [f for f in report["findings"] if f["severity"] != "pass"]
    assert len(non_pass) == 2
    for finding in non_pass:
        assert finding["remediation_text"], f"{finding['indicator_id']} has no remediation text"
    assert report["markdown"]

    # second GET must be cached -- same generated_at, no re-generation
    first_generated_at = report["generated_at"]
    r2 = client.get(f"/assessments/{run_id}/report")
    assert r2.status_code == 200
    assert r2.json()["generated_at"] == first_generated_at


def test_concurrent_report_generation_does_not_duplicate_rows(client, db_engine):
    """Regression test for a real bug found via the browser: React Strict
    Mode double-invoking the report page's effect fired two near-simultaneous
    GET /report calls, and each one ran a full generation pass -- 2 Report
    rows and 24 Findings for a 12-indicator assessment. Fixed with unique
    constraints on Finding(run_id, indicator_id) and Report(run_id); this
    test fires two real concurrent requests (via threads, not just
    sequential calls) and checks the DB directly for duplicates."""
    run_id = _create_and_complete_run(
        client,
        extra_answers={
            "fair.r1-1-license": {
                "value": "no",
                "label": "No, not true",
                "note": "No license has ever been stated for this test dataset.",
            }
        },
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(client.get, f"/assessments/{run_id}/report") for _ in range(2)]
        responses = [f.result() for f in futures]

    for r in responses:
        assert r.status_code == 200

    with Session(db_engine) as session:
        reports = session.exec(select(Report).where(Report.run_id == UUID(run_id))).all()
        findings = session.exec(select(Finding).where(Finding.run_id == UUID(run_id))).all()

    assert len(reports) == 1, f"expected exactly 1 Report row, found {len(reports)}"
    assert len(findings) == 12, f"expected exactly 12 Finding rows, found {len(findings)}"


def test_regenerate_finding(client):
    run_id = _create_and_complete_run(
        client,
        extra_answers={
            "fair.r1-1-license": {
                "value": "no",
                "label": "No, not true",
                "note": "No license has ever been stated for this test dataset.",
            }
        },
    )
    # report must exist before a finding can be regenerated
    client.get(f"/assessments/{run_id}/report")

    r = client.post(f"/assessments/{run_id}/findings/fair.r1-1-license/regenerate")
    assert r.status_code == 200
    assert r.json()["remediation_text"]


def test_regenerate_before_report_exists_404s(client):
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": "x"})
    run_id = r.json()["id"]
    r = client.post(f"/assessments/{run_id}/findings/fair.f1-identifier/regenerate")
    assert r.status_code == 404


def test_regenerate_on_passing_finding_rejected(client):
    run_id = _create_and_complete_run(client, extra_answers={})  # all "yes" -> everything passes
    client.get(f"/assessments/{run_id}/report")

    r = client.post(f"/assessments/{run_id}/findings/fair.f1-identifier/regenerate")
    assert r.status_code == 400
