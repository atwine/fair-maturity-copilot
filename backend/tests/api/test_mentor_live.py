"""Hits the real vLLM endpoint -- proves the mentor's conversation loop and
action-line parsing work end to end against real model output (the parsing
logic itself is tested without an LLM in tests/engine/test_mentor.py), that
a confirmed fix in chat actually reuses the existing answer-update/rescore
machinery rather than a separate, duplicated path, and that a chat is
scoped to a whole plan step -- which can bundle several indicators -- not
one indicator at a time (issue #9 / docs/DECISIONS.md v22).
"""

import uuid

from app.adapters.fair.content import load_indicators

_LICENSE_INDICATOR_ID = "fair.r1-1-license"
_PROVENANCE_INDICATOR_ID = "fair.r1-2-provenance"


def _create_completed_run_with_gaps(client, gap_indicator_ids: set[str]) -> str:
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": "Mentor Integration Test Dataset"})
    run_id = r.json()["id"]

    for indicator in load_indicators():
        if indicator.id in gap_indicator_ids:
            body = {"value": "no", "label": "No, not true", "note": f"Never addressed {indicator.id}."}
        else:
            body = {"value": "yes", "label": "Yes, clearly true"}
        r = client.put(f"/assessments/{run_id}/answers/{indicator.id}", json=body)
        assert r.status_code == 200

    r = client.post(f"/assessments/{run_id}/complete")
    assert r.status_code == 200

    # A report must exist first -- it's what creates the Finding rows the
    # plan (and so the mentor) reads severity from.
    r = client.get(f"/assessments/{run_id}/report")
    assert r.status_code == 200

    return run_id


def _first_step_id(client, run_id: str) -> str:
    plan = client.get(f"/assessments/{run_id}/plan").json()
    assert plan["steps"], f"expected at least one plan step, got: {plan}"
    return plan["steps"][0]["id"]


def test_starting_a_conversation_creates_it_with_an_opening_message(client):
    run_id = _create_completed_run_with_gaps(client, {_LICENSE_INDICATOR_ID})
    step_id = _first_step_id(client, run_id)

    r = client.post(f"/assessments/{run_id}/mentor/step/{step_id}/start", json={"skill_level": "new_to_this"})
    assert r.status_code == 200
    convo = r.json()
    assert convo["skill_level"] == "new_to_this"
    assert convo["indicators"]  # the step's indicator list came through
    assert len(convo["messages"]) == 1
    assert convo["messages"][0]["role"] == "mentor"
    assert convo["messages"][0]["content"]

    # Starting again on the same (run, step) returns the same conversation
    # rather than a second opening message.
    r2 = client.post(f"/assessments/{run_id}/mentor/step/{step_id}/start", json={"skill_level": "done_this_before"})
    assert r2.status_code == 200
    assert r2.json()["skill_level"] == "new_to_this"  # unchanged -- skill_level is set once, not re-negotiated
    assert len(r2.json()["messages"]) == 1


def test_confirming_a_fix_in_chat_updates_the_real_answer_and_rescores(client):
    run_id = _create_completed_run_with_gaps(client, {_LICENSE_INDICATOR_ID})
    step_id = _first_step_id(client, run_id)
    client.post(f"/assessments/{run_id}/mentor/step/{step_id}/start", json={"skill_level": "done_this_before"})

    r = client.post(
        f"/assessments/{run_id}/mentor/step/{step_id}/messages",
        json={
            "content": (
                "Done -- I just added a CC-BY 4.0 license statement to our dataset's README and "
                "our repository record. This should be resolved now."
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


def test_two_indicators_grouped_into_one_step_share_a_single_conversation(client):
    # If the plan happens to group these two gaps into the same step, one
    # conversation should cover both -- the actual point of issue #9.
    run_id = _create_completed_run_with_gaps(client, {_LICENSE_INDICATOR_ID, _PROVENANCE_INDICATOR_ID})
    plan = client.get(f"/assessments/{run_id}/plan").json()

    grouped_step = next(
        (
            s
            for s in plan["steps"]
            if {_LICENSE_INDICATOR_ID, _PROVENANCE_INDICATOR_ID} <= {i["indicator_id"] for i in s["indicators"]}
        ),
        None,
    )
    if grouped_step is None:
        # The model didn't happen to group them together this run -- not a
        # failure of this feature (grouping is the LLM's call), just not a
        # case this particular run can exercise. Fall back to asserting the
        # weaker but still-real guarantee: every step's indicators share one
        # conversation regardless of how many indicators that step has.
        step = plan["steps"][0]
        r = client.post(f"/assessments/{run_id}/mentor/step/{step['id']}/start", json={"skill_level": "new_to_this"})
        assert r.status_code == 200
        assert {i["indicator_id"] for i in r.json()["indicators"]} == {i["indicator_id"] for i in step["indicators"]}
        return

    r = client.post(f"/assessments/{run_id}/mentor/step/{grouped_step['id']}/start", json={"skill_level": "new_to_this"})
    assert r.status_code == 200
    indicator_ids = {i["indicator_id"] for i in r.json()["indicators"]}
    assert _LICENSE_INDICATOR_ID in indicator_ids
    assert _PROVENANCE_INDICATOR_ID in indicator_ids


def test_conversation_history_persists_across_a_reload(client):
    run_id = _create_completed_run_with_gaps(client, {_LICENSE_INDICATOR_ID})
    step_id = _first_step_id(client, run_id)
    client.post(f"/assessments/{run_id}/mentor/step/{step_id}/start", json={"skill_level": "new_to_this"})
    client.post(
        f"/assessments/{run_id}/mentor/step/{step_id}/messages",
        json={"content": "What's a license statement, exactly?"},
    )

    r = client.get(f"/assessments/{run_id}/mentor/step/{step_id}")
    assert r.status_code == 200
    messages = r.json()["messages"]
    # opening message + the user's question + the mentor's reply
    assert len(messages) == 3
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "What's a license statement, exactly?"


def test_a_conversation_stays_reachable_after_the_plan_regenerates(client):
    # The whole point of caching the plan with permanent step ids (issue #9)
    # is that a conversation survives a regeneration -- prove it directly.
    run_id = _create_completed_run_with_gaps(client, {_LICENSE_INDICATOR_ID})
    step_id = _first_step_id(client, run_id)
    client.post(f"/assessments/{run_id}/mentor/step/{step_id}/start", json={"skill_level": "new_to_this"})

    # Trigger a plan regeneration by revisiting an unrelated answer.
    other_indicator = next(i for i in load_indicators() if i.id != _LICENSE_INDICATOR_ID)
    r = client.put(
        f"/assessments/{run_id}/answers/{other_indicator.id}",
        json={"value": "partial", "label": "Partially / inconsistently true", "note": "Revisited."},
    )
    assert r.status_code == 200
    client.get(f"/assessments/{run_id}/plan")  # forces the regeneration

    r = client.get(f"/assessments/{run_id}/mentor/step/{step_id}")
    assert r.status_code == 200
    assert len(r.json()["messages"]) == 1  # the original opening message, untouched


def test_mentor_before_a_report_exists_400s(client):
    r = client.post("/assessments", json={"adapter_id": "fair-v0", "subject_label": "x"})
    run_id = r.json()["id"]

    r = client.post(f"/assessments/{run_id}/mentor/step/{uuid.uuid4()}/start", json={"skill_level": "new_to_this"})
    assert r.status_code == 400


def test_mentor_for_nonexistent_run_404s(client):
    r = client.post(
        f"/assessments/{uuid.uuid4()}/mentor/step/{uuid.uuid4()}/start", json={"skill_level": "new_to_this"}
    )
    assert r.status_code == 404
