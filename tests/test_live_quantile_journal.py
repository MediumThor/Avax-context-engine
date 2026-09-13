"""Live API journal path: empirical next-10 quantiles + MTF feature snapshot."""

from __future__ import annotations

import math
from fastapi.testclient import TestClient

from packages.features import FEATURE_SCHEMA_VERSION
from packages.fixtures import sept_2026_failed_breakout
from packages.models.baselines import emit_baseline_forecast
from services.api.runtime import PrototypeRuntime, reset_runtime

QUANTILE_MODEL = "freqai.quantiles.research.v1"


def _runtime(tmp_path) -> PrototypeRuntime:
    return PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)


def test_live_forecast_emits_ordered_quantiles_and_simple_aliases(tmp_path):
    runtime = _runtime(tmp_path)
    candles = runtime.candles("AVAXUSDT")
    as_of = candles[-1].close_time()
    payload = runtime.emit_live_forecast(candles, as_of=as_of)
    assert payload["model_id"] == QUANTILE_MODEL
    assert payload["freqai_beats_baselines"] is None
    assert len(payload["horizons"]) == 10
    for row in payload["horizons"]:
        assert row["q10_cum_log_return"] <= row["q50_cum_log_return"] <= row["q90_cum_log_return"]
        assert row["q10_cum_return"] <= row["q50_cum_return"] <= row["q90_cum_return"]
        assert row["p_close_above_origin"] is None
        assert row["q10_cum_return"] == math.exp(row["q10_cum_log_return"]) - 1.0
        assert row["q50_cum_return"] == math.exp(row["q50_cum_log_return"]) - 1.0
        assert row["q90_cum_return"] == math.exp(row["q90_cum_log_return"]) - 1.0
    runtime.close()


def test_future_perturbation_does_not_change_live_forecast_at_t(tmp_path):
    runtime = _runtime(tmp_path)
    candles = sept_2026_failed_breakout()
    origin = 900
    as_of = candles[origin].close_time()
    visible = candles[: origin + 1]
    before = runtime.emit_live_forecast(visible, as_of=as_of)
    mutated = list(candles)
    nxt = mutated[origin + 1]
    mutated[origin + 1] = nxt.__class__(
        nxt.symbol,
        nxt.timeframe,
        nxt.open_time,
        99.0,
        120.0,
        80.0,
        110.0,
        9_999.0,
        is_closed=True,
    )
    truncated = runtime.emit_live_forecast(mutated[: origin + 1], as_of=as_of)
    filtered = runtime.emit_live_forecast(mutated, as_of=as_of)
    assert before["horizons"] == truncated["horizons"]
    assert before["horizons"] == filtered["horizons"]
    runtime.close()


def test_short_history_falls_back_to_drift20(tmp_path):
    runtime = _runtime(tmp_path)
    short = runtime.candles("AVAXUSDT")[:25]
    payload = runtime.emit_live_forecast(short, as_of=short[-1].close_time())
    expected = emit_baseline_forecast(short)
    assert payload["model_id"] == "baseline.drift20"
    assert payload["horizons"] == expected["horizons"]
    runtime.close()


def test_journal_records_mtf_feature_snapshot(tmp_path):
    runtime = _runtime(tmp_path)
    out = runtime.forecast("AVAXUSDT")
    payload = out["forecast"]
    latest = runtime.journal.latest("AVAXUSDT")
    assert out["journaled"] is True
    assert out["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert latest is not None
    assert latest["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert latest["model_id"] == QUANTILE_MODEL
    snap = latest["payload"]["mtf_feature_snapshot"]
    assert snap["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert "values" in snap
    stored = runtime.journal.get_forecast(latest["id"])
    assert stored["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert payload["model_id"] == QUANTILE_MODEL
    runtime.close()


def test_api_market_returns_quantile_envelope(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    from services.api.main import app

    client = TestClient(app)
    body = client.get("/api/v1/market/AVAXUSDT").json()
    forecast = body["forecast"]["forecast"]
    assert body["health"]["status"] == "fixture"
    assert forecast["model_id"] == QUANTILE_MODEL
    row = forecast["horizons"][0]
    assert row["p_close_above_origin"] is None
    assert row["q10_cum_return"] <= row["q50_cum_return"] <= row["q90_cum_return"]
    assert forecast["mtf_feature_snapshot"]["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    reset_runtime()


def test_replay_as_of_ignores_later_quantile_training(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    from services.api.main import app

    candles = sept_2026_failed_breakout()
    as_of = candles[1200].close_time().isoformat()
    client = TestClient(app)
    body = client.get("/api/v1/replay/AVAXUSDT", params={"as_of": as_of}).json()
    assert body["replay"] is True
    assert abs(body["last_price"] - candles[1200].close) < 1e-9
    row = body["forecast"]["forecast"]["horizons"][0]
    assert row["p_close_above_origin"] is None
    assert "q10_cum_return" in row or body["forecast"]["forecast"]["model_id"] == "baseline.drift20"
    reset_runtime()
