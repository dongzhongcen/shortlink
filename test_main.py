import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_engine = main.create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setattr(main, "engine", test_engine)
    main.init_db()
    return TestClient(main.app)

def test_shorten_and_redirect(client):
    resp = client.post("/shorten", json={"url": "https://www.python.org"})
    assert resp.status_code == 200
    code = resp.json()["code"]
    assert len(code) == 6

    # follow_redirects=False：不要真的跳過去，我們只檢查伺服器回了什麼
    resp = client.get(f"/{code}", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://www.python.org/"


def test_clicks_are_counted(client):
    code = client.post("/shorten", json={"url": "https://example.com"}).json()["code"]
    for _ in range(3):
        client.get(f"/{code}", follow_redirects=False)

    stats = client.get(f"/stats/{code}").json()
    assert stats["clicks"] == 3


def test_invalid_url_is_rejected(client):
    resp = client.post("/shorten", json={"url": "abc"})
    assert resp.status_code == 422


def test_unknown_code_returns_404(client):
    assert client.get("/nope12", follow_redirects=False).status_code == 404
    assert client.get("/stats/nope12").status_code == 404