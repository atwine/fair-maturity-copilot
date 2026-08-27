def test_get_questions_for_fair_adapter(client):
    r = client.get("/adapters/fair-v0/questions")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 12
    assert {q["priority"] for q in data} <= {"essential", "important", "useful"}
    assert all(q["options"] for q in data)


def test_get_questions_for_unknown_adapter_404s(client):
    r = client.get("/adapters/nope/questions")
    assert r.status_code == 404


def test_get_questions_for_harmonization_adapter(client):
    r = client.get("/adapters/harmonization-v0/questions")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 6
    assert {q["priority"] for q in data} <= {"essential", "important", "useful"}
    assert all(q["options"] for q in data)
    # the 5th answer value (issue #16) must actually be offered, not just
    # accepted server-side
    all_values = {opt["value"] for q in data for opt in q["options"]}
    assert "not_started" in all_values
