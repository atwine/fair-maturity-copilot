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
