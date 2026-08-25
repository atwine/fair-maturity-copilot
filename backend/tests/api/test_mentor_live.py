"""Hits the real vLLM endpoint -- proves the mentor's conversation loop and
action-line parsing work end to end against real model output (the parsing
logic itself is tested without an LLM in tests/engine/test_mentor.py), and
that a confirmed fix in chat actually reuses the existing answer-update/
rescore machinery rather than a separate, duplicated path.
"""

import uuid

from app.adapters.fair.content import load_indicators

_LICENSE_INDICATOR_ID = "fair.r1-1-license"


def _create_completed_run_with_a_license_gap(client) -> str:
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": "Mentor Integration Test Dataset"})
    run_id = r.json()["id"]

    for indicator in load_indicators():
        if indicator.id == _LICENSE_INDICATOR_ID:
            body = {"value": "no", "label": "No, not true", "note": "We have never stated a license for this data."}
        else:
            body = {"value": "yes", "label": "Yes, clearly true"}
        r = client.put(f"/assessments/{run_id}/answers/{indicator.id}", json=body)
        assert r.status_code == 200

    r = client.post(f"/assessments/{run_id}/complete")
    assert r.status_code == 200

    # A report must exist first -- it's what creates the Finding row the
    # mentor route reads severity from, same precondition the plan has.
    r = client.get(f"/assessments/{run_id}/report")
    assert r.status_code == 200

    return run_id


def test_starting_a_conversation_creates_it_with_an_opening_message(client):
    run_id = _create_completed_run_with_a_license_gap(client)

    r = client.post(f"/assessments/{run_id}/mentor/{_LICENSE_INDICATOR_ID}/start", json={"skill_level": "new_to_this"})
    assert r.status_code == 200
    convo = r.json()
    assert convo["skill_level"] == "new_to_this"
    assert len(convo["messages"]) == 1
    assert convo["messages"][0]["role"] == "mentor"
    assert convo["messages"][0]["content"]

    # Starting again on the same (run, indicator) returns the same
    # conversation rather than a second opening message.
    r2 = client.post(f"/assessments/{run_id}/mentor/{_LICENSE_INDICATOR_ID}/start", json={"skill_level": "done_this_before"})
    assert r2.status_code == 200
    assert r2.json()["skill_level"] == "new_to_this"  # unchanged -- skill_level is set once, not re-negotiated
    assert len(r2.json()["messages"]) == 1


def test_confirming_a_fix_in_chat_updates_the_real_answer_and_rescores(client):
    run_id = _create_completed_run_with_a_license_gap(client)
    client.post(f"/assessments/{run_id}/mentor/{_LICENSE_INDICATOR_ID}/start", json={"skill_level": "done_this_before"})

    r = client.post(
        f"/assessments/{run_id}/mentor/{_LICENSE_INDICATOR_ID}/messages",
        json={
            "content": (
                "Done -- I just added a CC-BY 4.0 license statement to our dataset's README and "
                "our repository record. This indicator should be resolved now."
            )
        },
    )
    assert r.status_code == 200
    reply = r.json()
    assert reply["mentor_message"]["content"]
    # The raw UPDATE_ANSWER:/NOTE: marker lines must never leak into what's
    # actually shown to the user.
    assert "UPDATE_ANSWER" not in reply["mentor_message"]["content"]

    action = reply["action_taken"]
    assert action is not None, f"expected the mentor to confirm the fix, got: {reply['mentor_message']['content']!r}"
    assert action["indicator_id"] == _LICENSE_INDICATOR_ID
    assert action["new_value"] in {"yes", "partial"}
    assert action["new_severity"] in {"pass", "minor_gap"}

    # Prove this actually went through the real answer-update path, not a
    # side-channel: the report reflects the change too.
    report = client.get(f"/assessments/{run_id}/report").json()
    finding = next(f for f in report["findings"] if f["indicator_id"] == _LICENSE_INDICATOR_ID)
    assert finding["severity"] == action["new_severity"]


def test_conversation_history_persists_across_a_reload(client):
    run_id = _create_completed_run_with_a_license_gap(client)
    client.post(f"/assessments/{run_id}/mentor/{_LICENSE_INDICATOR_ID}/start", json={"skill_level": "new_to_this"})
    client.post(
        f"/assessments/{run_id}/mentor/{_LICENSE_INDICATOR_ID}/messages",
        json={"content": "What's a license statement, exactly?"},
    )

    r = client.get(f"/assessments/{run_id}/mentor/{_LICENSE_INDICATOR_ID}")
    assert r.status_code == 200
    messages = r.json()["messages"]
    # opening message + the user's question + the mentor's reply
    assert len(messages) == 3
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "What's a license statement, exactly?"


def test_mentor_before_a_report_exists_400s(client):
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": "x"})
    run_id = r.json()["id"]

    r = client.post(f"/assessments/{run_id}/mentor/{_LICENSE_INDICATOR_ID}/start", json={"skill_level": "new_to_this"})
    assert r.status_code == 400


def test_mentor_for_nonexistent_run_404s(client):
    r = client.post(
        f"/assessments/{uuid.uuid4()}/mentor/{_LICENSE_INDICATOR_ID}/start", json={"skill_level": "new_to_this"}
    )
    assert r.status_code == 404
