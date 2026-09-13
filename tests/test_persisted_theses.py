"""Append-only thesis ledger. Invalidation cannot move after the first write."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from packages.harness.kill_switch import engage
from packages.journal import ForecastJournal
from services.api.runtime import PrototypeRuntime, reset_runtime


def test_sync_theses_refuses_invalidation_move(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    row = {
        "id": "AVAXUSDT:4h:bear:htf_continuation:v1",
        "lineage_id": "AVAXUSDT:4h:bear:htf_continuation",
        "symbol": "AVAXUSDT",
        "direction": "bear",
        "timeframe": "4h",
        "status": "active",
        "version": 1,
        "created_at": "2026-09-01T00:00:00+00:00",
        "invalidation_fingerprint": "fp-8-192",
        "invalidation_rules": [{"kind": "close_above", "price": 8.192, "timeframe": "4h"}],
        "note": "Invalidation frozen at open. Not a confidence score.",
    }
    first = journal.sync_theses([row])
    assert first["wrote"] == 1
    moved = dict(row)
    moved["invalidation_fingerprint"] = "fp-moved"
    moved["invalidation_rules"] = [{"kind": "close_above", "price": 7.40, "timeframe": "4h"}]
    second = journal.sync_theses([moved])
    assert second["wrote"] == 0
    assert second["kept"] == 1
    assert second["refused_move"] == 1
    stored = journal.get_thesis(row["id"])
    assert stored is not None
    assert stored["invalidation_fingerprint"] == "fp-8-192"
    assert stored["payload"]["invalidation_rules"][0]["price"] == 8.192
    journal.close()


def test_live_snapshot_journals_theses_and_second_load_keeps_eight(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    first = runtime.snapshot("AVAXUSDT")
    bears = [t for t in first.theses if t.get("direction") == "bear" and t.get("timeframe") == "4h"]
    assert bears
    assert bears[0]["ledger"] == "journaled"
    price = bears[0]["invalidation_rules"][0]["price"]
    fingerprint = bears[0]["invalidation_fingerprint"]
    stored = runtime.journal.get_thesis(bears[0]["id"])
    assert stored is not None
    assert stored["invalidation_fingerprint"] == fingerprint
    runtime._snap_cache.clear()
    second = runtime.snapshot("AVAXUSDT")
    again = [t for t in second.theses if t["id"] == bears[0]["id"]][0]
    assert again["invalidation_rules"][0]["price"] == price
    assert again["invalidation_fingerprint"] == fingerprint
    assert again["ledger"] == "journaled"
    assert abs(price - 8.192) < 1e-6
    runtime.close()

    reset_runtime()
    from services.api.main import app

    client = TestClient(app)
    body = client.get(f"/api/v1/theses/{bears[0]['id']}").json()
    assert body["invalidation_fingerprint"] == fingerprint
    assert body["payload"]["invalidation_rules"][0]["price"] == price
    assert client.get("/api/v1/theses/missing").status_code == 404
    reset_runtime()


def test_replay_snapshot_does_not_insert_theses(tmp_path):
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    as_of = datetime(2026, 9, 2, tzinfo=timezone.utc)
    snap = runtime.snapshot("AVAXUSDT", as_of=as_of, persist_theses=False)
    assert snap.theses
    assert all(row.get("ledger") == "ephemeral" for row in snap.theses)
    assert runtime.journal.get_thesis(snap.theses[0]["id"]) is None
    payload = runtime.market_payload("AVAXUSDT", as_of=as_of)
    assert payload["replay"] is True
    assert runtime.journal.list_theses("AVAXUSDT") == []
    runtime.close()


def test_kill_switch_skips_thesis_insert(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_KILL_SWITCH_PATH", str(tmp_path / "kill-switch.json"))
    engage(
        "block thesis writes",
        actor="test",
        path=tmp_path / "kill-switch.json",
        tasks_path=tmp_path / "active-tasks.json",
        health_path=tmp_path / "recursive-health.json",
    )
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    snap = runtime.snapshot("AVAXUSDT")
    assert snap.theses
    assert all(row.get("ledger") == "ephemeral" for row in snap.theses)
    assert runtime.journal.list_theses("AVAXUSDT") == []
    runtime.close()
