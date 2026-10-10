from tests.conftest import signup

BUGGY = 'def f(x, items=[]):\n    try:\n        run("a" + x)\n    except:\n        print("x")\n'


async def test_register_duplicate_and_bad_login(client):
    await signup(client, "a@example.com")
    dup = await client.post("/api/auth/register", json={"email": "a@example.com", "password": "password123"})
    assert dup.status_code == 409
    bad = await client.post("/api/auth/login", data={"username": "a@example.com", "password": "wrong-pass"})
    assert bad.status_code == 401


async def test_reviews_require_auth(client):
    assert (await client.get("/api/reviews")).status_code == 401
    assert (await client.post("/api/reviews", json={"code": "x=1"})).status_code == 401


async def test_create_review_returns_structured_feedback(client):
    headers = await signup(client, "a@example.com")
    r = await client.post("/api/reviews", json={"code": BUGGY, "language": "python"}, headers=headers)
    assert r.status_code == 201
    body = r.json()
    assert 0 <= body["feedback"]["score"] <= 100
    categories = {f["category"] for f in body["feedback"]["findings"]}
    assert {"bug", "style"} <= categories
    assert all(f["line"] for f in body["feedback"]["findings"])


async def test_history_is_private_per_user(client):
    alice = await signup(client, "alice@example.com")
    bob = await signup(client, "bob@example.com")
    created = await client.post("/api/reviews", json={"code": BUGGY}, headers=alice)
    review_id = created.json()["id"]

    assert len((await client.get("/api/reviews", headers=alice)).json()) == 1
    assert (await client.get("/api/reviews", headers=bob)).json() == []
    assert (await client.get(f"/api/reviews/{review_id}", headers=bob)).status_code == 404
    assert (await client.delete(f"/api/reviews/{review_id}", headers=bob)).status_code == 404
    assert (await client.delete(f"/api/reviews/{review_id}", headers=alice)).status_code == 204


async def test_empty_and_oversized_code_rejected(client):
    headers = await signup(client, "a@example.com")
    assert (await client.post("/api/reviews", json={"code": ""}, headers=headers)).status_code == 422
    big = {"code": "x" * 20_001}
    assert (await client.post("/api/reviews", json=big, headers=headers)).status_code == 422


def test_parse_feedback_handles_markdown_fences():
    from app.services.llm import parse_feedback

    raw = '```json\n{"summary":"ok","score":90,"findings":[]}\n```'
    assert parse_feedback(raw).score == 90
