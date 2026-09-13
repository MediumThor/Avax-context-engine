from datetime import datetime

from services.api.runtime import PrototypeRuntime, reset_runtime


def test_default_chart_includes_failed_breakout_high(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    narrow = runtime.market_payload("AVAXUSDT", chart_limit=240, persist=False)
    wide = runtime.market_payload("AVAXUSDT", persist=False)
    assert len(narrow["candles"]) == 240
    assert max(row["high"] for row in narrow["candles"]) < 8.0
    assert len(wide["candles"]) == 1000
    assert max(row["high"] for row in wide["candles"]) >= 8.18
    times = {row["time"] for row in wide["candles"]}
    rejected = None
    for state in wide["snapshot"]["timeframes"].values():
        for zone in [*(state.get("resistance_zones") or []), *(state.get("support_zones") or [])]:
            if zone.get("interaction") == "rejected":
                rejected = zone
    assert rejected is not None
    tested = rejected["last_test_at"]
    stamp = tested if isinstance(tested, datetime) else datetime.fromisoformat(str(tested))
    assert int(stamp.timestamp()) in times
    runtime.close()
    reset_runtime()
