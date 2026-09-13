"""Secondary /benchmarks and /models dests name gates without inventing scores."""

from pathlib import Path

from fastapi.testclient import TestClient


def test_five_primary_dests_still_named():
    dests = Path("apps/web/src/nav/destinations.ts").read_text(encoding="utf-8")
    nav = Path("apps/web/src/nav/DestNav.tsx").read_text(encoding="utf-8")
    assert "DEST_IDS = ['market', 'replay', 'accuracy', 'health', 'more']" in dests
    assert "SECONDARY_DESTS = ['benchmarks', 'models']" in dests
    assert "return '/benchmarks'" in dests
    assert "return '/models'" in dests
    assert "DEST_IDS.map" in nav
    more = Path("apps/web/src/views/MoreView.tsx").read_text(encoding="utf-8")
    assert "onNavigate?.('benchmarks')" in more
    assert "onNavigate?.('models')" in more


def test_benchmarks_api_lists_draft_gates_without_scores(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    from services.api.main import app

    client = TestClient(app)
    res = client.get("/api/v1/benchmarks")
    assert res.status_code == 200
    body = res.json()
    assert body["promotion_allowed"] is False
    assert body["execution_enabled"] is False
    ids = {row["id"] for row in body["entries"]}
    assert "avax-5m-next10" in ids
    assert "avax-2026-09-failed-8" in ids
    for row in body["entries"]:
        assert row["status"] == "draft"
        assert "mae" not in row
        assert "ece" not in row
        assert row.get("sealed") is False
    text = res.text.lower()
    assert "0.0123" not in text


def test_models_api_keeps_incumbent_and_research_unpromoted(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    from services.api.main import app

    client = TestClient(app)
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    body = res.json()
    assert body["promotion_allowed"] is False
    assert body["incumbent"]["model_id"] == "baseline.drift20"
    assert body["incumbent"]["promotion_allowed"] is False
    research_ids = {row["model_id"] for row in body["research"]}
    assert "freqai.quantiles.research.v1" in research_ids
    assert all(row["promotion_allowed"] is False for row in body["research"])
