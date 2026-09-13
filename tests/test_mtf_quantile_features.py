from __future__ import annotations

from packages.features import FEATURE_SCHEMA_VERSION
from packages.fixtures import btc_companion, sept_2026_failed_breakout
from packages.models.freqai_quantiles import (
    MODEL_FEATURE_NAMES,
    MODEL_ID,
    PYTHON_FALLBACK_ID,
    emit_quantile_forecast,
)
from tests.test_freqai_quantiles import as_of_index, make_5m, mutate_after


def test_quantile_payload_uses_mtf_schema():
    candles = make_5m(140)
    payload = emit_quantile_forecast(candles, as_of=as_of_index(candles, 129), backend="python")
    assert payload["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert payload["feature_schema_version"] == "avax.features.mtf.v1"
    assert payload["python_fallback"] == PYTHON_FALLBACK_ID
    assert payload["model_feature_names"] == list(MODEL_FEATURE_NAMES)
    assert payload["model_id"] == MODEL_ID
    assert payload["freqai_beats_baselines"] is None
    for row in payload["horizons"]:
        assert row["q10_cum_log_return"] <= row["q50_cum_log_return"] <= row["q90_cum_log_return"]


def test_future_avax_and_btc_do_not_change_forecast_at_t():
    avax = sept_2026_failed_breakout()[:220]
    btc = btc_companion(avax)
    origin = 180
    as_of = avax[origin].close_time()
    before = emit_quantile_forecast(avax, as_of=as_of, backend="python", btc_5m=btc)
    mutated_avax = mutate_after(avax, origin + 1)
    mutated_btc = list(btc)
    nxt = mutated_btc[origin + 1]
    mutated_btc[origin + 1] = nxt.__class__(
        nxt.symbol,
        nxt.timeframe,
        nxt.open_time,
        99000.0,
        100000.0,
        98000.0,
        99500.0,
        9_999.0,
        is_closed=True,
    )
    after = emit_quantile_forecast(mutated_avax, as_of=as_of, backend="python", btc_5m=mutated_btc)
    assert before["horizons"] == after["horizons"]
    assert before["feature_schema_version"] == FEATURE_SCHEMA_VERSION


def test_live_runtime_passes_btc_and_keeps_mtf_schema(tmp_path):
    from services.api.runtime import PrototypeRuntime

    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    out = runtime.forecast("AVAXUSDT")
    payload = out["forecast"]
    assert payload["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert payload["model_feature_names"] == list(MODEL_FEATURE_NAMES)
    assert out["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    runtime.close()
