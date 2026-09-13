"""Market payload includes volume so the chart can draw a histogram."""

from services.api.runtime import PrototypeRuntime, reset_runtime


def test_market_candles_include_positive_volume(tmp_path):
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    payload = runtime.market_payload("AVAXUSDT", persist=False)
    candles = payload["candles"]
    assert candles
    assert all("volume" in row for row in candles)
    assert all(row["volume"] > 0 for row in candles)
    assert candles[0]["volume"] != candles[-1]["volume"]
    runtime.close()
    reset_runtime()
