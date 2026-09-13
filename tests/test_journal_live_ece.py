"""Held-out live ECE excludes fixture and untagged journal rows."""

from datetime import datetime, timedelta, timezone

from packages.journal import ForecastJournal
from packages.models.journal_scores import score_journaled_forecasts
from packages.models.probability_walkforward import MIN_ECE
from services.api.runtime import PrototypeRuntime, reset_runtime


def _write(journal: ForecastJournal, *, stamp: str, source: str | None, forecast_id: str, p: float, up: bool):
    payload = {
        "forecasted_at": stamp,
        "horizons": [{"h": 1, "p_close_above_origin": p}],
    }
    if source is not None:
        payload["data_source"] = source
    journal.get_or_append(
        forecast_id=forecast_id,
        symbol="AVAXUSDT",
        forecasted_at=stamp,
        model_id="empirical_signed_base_rate.v1",
        payload=payload,
    )
    journal.get_or_append_outcome(
        forecast_id,
        1,
        {
            "h": 1,
            "matured_at": stamp,
            "realized_close_above_origin": up,
            "realized_cum_log_return": 0.001 if up else -0.001,
        },
    )


def test_live_slice_ignores_fixture_and_unknown(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    for i in range(MIN_ECE):
        stamp = (start + timedelta(minutes=5 * i)).isoformat()
        _write(journal, stamp=stamp, source="fixture", forecast_id=f"fx-{i}", p=0.8, up=True)
    for i in range(3):
        stamp = (start + timedelta(minutes=5 * (MIN_ECE + i))).isoformat()
        _write(journal, stamp=stamp, source=None, forecast_id=f"unk-{i}", p=0.2, up=False)
    scored = score_journaled_forecasts(journal, "AVAXUSDT")
    pooled = scored["horizons"]["1"]["probability"]
    live = scored["horizons"]["1"]["probability_held_out_live"]
    assert pooled["sample_count"] == MIN_ECE + 3
    assert pooled["ece"] is not None
    assert live["sample_count"] == 0
    assert live["ece"] is None
    assert live["brier"] is None
    journal.close()


def test_binance_vision_rows_score_held_out_live_ece(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    for i in range(MIN_ECE):
        stamp = (start + timedelta(minutes=5 * i)).isoformat()
        _write(
            journal,
            stamp=stamp,
            source="binance-vision",
            forecast_id=f"live-{i}",
            p=0.7,
            up=i % 2 == 0,
        )
    scored = score_journaled_forecasts(journal, "AVAXUSDT")
    live = scored["horizons"]["1"]["probability_held_out_live"]
    assert live["sample_count"] == MIN_ECE
    assert live["ece"] is not None
    assert live["brier"] is not None
    assert live["source"] == "journal_live"
    journal.close()


def test_fixture_persist_stamps_data_source(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    runtime.forecast("AVAXUSDT", persist=True)
    rows = runtime.journal.list_forecasts("AVAXUSDT")
    assert rows
    assert all(row["payload"].get("data_source") == "fixture" for row in rows)
    live = score_journaled_forecasts(runtime.journal, "AVAXUSDT")["horizons"]["1"]["probability_held_out_live"]
    assert live["sample_count"] == 0
    assert live["ece"] is None
    runtime.close()
    reset_runtime()
