"""Catch-up/drain may attach empirical P(up). Drift20 path and emit stay honest."""

from datetime import datetime, timedelta, timezone

from packages.context_engine.models import Candle
from packages.models.baselines import emit_baseline_forecast
from packages.models.direction_cal import CALIBRATION_REF, attach_empirical_signed_p, empirical_p_by_horizon
from packages.models.journal_scores import score_journaled_forecasts
from packages.models.outcomes import mature_outcomes
from services.api.runtime import SOURCE, PrototypeRuntime, reset_runtime


def _bar(open_time: datetime, close: float, prev: float | None = None) -> Candle:
    open_px = prev if prev is not None else close
    high = max(open_px, close) + 0.01
    low = min(open_px, close) - 0.01
    return Candle("AVAXUSDT", "5m", open_time, open_px, high, low, close, 10.0, True)


def _trend(n: int = 120) -> list[Candle]:
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    out: list[Candle] = []
    price = 20.0
    for i in range(n):
        nxt = price + (0.02 if i % 3 else -0.01)
        out.append(_bar(start + timedelta(minutes=5 * i), nxt, price))
        price = nxt
    return out


def test_emit_baseline_still_has_null_p():
    payload = emit_baseline_forecast(_trend(40))
    assert payload["model_id"] == "baseline.drift20"
    assert payload["horizons"][0]["p_close_above_origin"] is None
    assert payload["confidence_source"] == "insufficient-data"


def test_attach_fills_p_from_prefix_only():
    candles = _trend(80)
    prefix = candles[:-8]
    payload = attach_empirical_signed_p(emit_baseline_forecast(prefix), prefix)
    p = payload["horizons"][0]["p_close_above_origin"]
    assert p is not None
    assert 0.0 <= p <= 1.0
    assert payload["horizons"][0]["confidence_source"] == CALIBRATION_REF
    assert payload["promotion_allowed"] is False

    later = list(prefix)
    last = prefix[-1]
    later.append(
        _bar(last.open_time + timedelta(minutes=5), last.close + 5.0, last.close)
    )
    again = attach_empirical_signed_p(emit_baseline_forecast(prefix), prefix)
    assert again["horizons"][0]["p_close_above_origin"] == p
    flipped = attach_empirical_signed_p(emit_baseline_forecast(later), later)
    # Later bar may change p for the later origin; the prefix attach must stay put.
    assert empirical_p_by_horizon(prefix)[1] == p
    assert empirical_p_by_horizon(prefix)[1] == empirical_p_by_horizon(later[:-1])[1]


def test_attach_does_not_overwrite_existing_p():
    payload = emit_baseline_forecast(_trend(40))
    payload["horizons"][0]["p_close_above_origin"] = 0.42
    out = attach_empirical_signed_p(payload, _trend(40))
    assert out["horizons"][0]["p_close_above_origin"] == 0.42


def test_live_drain_rows_can_score_held_out_brier(tmp_path, monkeypatch):
    monkeypatch.delenv("AVAX_USE_FIXTURE", raising=False)
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=False)
    candles = _trend(160)
    runtime.store.insert_many(SOURCE, candles)
    monkeypatch.setattr(runtime, "_pull_closed_live", lambda *a, **k: [])
    drained = runtime.drain_shadow_journal("AVAXUSDT", budget=80, rounds=1)
    assert drained["wrote"] > 0
    rows = [row for row in runtime.journal.list_forecasts("AVAXUSDT") if row["model_id"] == "baseline.drift20"]
    assert rows
    assert all(row["payload"].get("data_source") == SOURCE for row in rows)
    with_p = [row for row in rows if row["payload"]["horizons"][0].get("p_close_above_origin") is not None]
    assert with_p
    mature_outcomes(runtime.journal, candles, "AVAXUSDT", as_of=candles[-1].close_time())
    scored = score_journaled_forecasts(runtime.journal, "AVAXUSDT", as_of=candles[-1].close_time())
    live = scored["horizons"]["1"]["probability_held_out_live"]
    assert live["sample_count"] >= 8
    assert live["brier"] is not None
    runtime.close()
    reset_runtime()
