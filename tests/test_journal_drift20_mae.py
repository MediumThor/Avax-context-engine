from __future__ import annotations

from datetime import datetime, timezone

from packages.journal import ForecastJournal
from packages.models.journal_scores import score_journaled_forecasts
from packages.models.probability_walkforward import MIN_MAE
from services.api.runtime import SHADOW_CATCHUP_MODEL, PrototypeRuntime, reset_runtime


def _row(stamp: str, drift: float) -> dict:
    return {
        "forecasted_at": stamp,
        "origin_close": 8.0,
        "model_id": SHADOW_CATCHUP_MODEL,
        "horizons": [
            {
                "h": 1,
                "p_close_above_origin": None,
                "expected_cum_log_return": drift,
                "drift20_cum_log_return": drift,
            }
        ],
    }


def test_journal_drift20_mae_ignores_null_probability(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    as_of = datetime(2026, 9, 2, tzinfo=timezone.utc)
    for i in range(MIN_MAE):
        stamp = f"2026-09-01T00:{i:02d}:00+00:00"
        journal.get_or_append(
            forecast_id=f"d20-{i}",
            symbol="AVAXUSDT",
            forecasted_at=stamp,
            model_id=SHADOW_CATCHUP_MODEL,
            payload=_row(stamp, 0.01),
        )
        journal.get_or_append_outcome(
            f"d20-{i}",
            1,
            {
                "h": 1,
                "matured_at": "2026-09-01T00:10:00+00:00",
                "realized_close_above_origin": True,
                "realized_cum_log_return": 0.02,
            },
        )
    scored = score_journaled_forecasts(journal, "AVAXUSDT", as_of=as_of)
    h1 = scored["horizons"]["1"]
    assert h1["probability"]["sample_count"] == 0
    assert h1["probability"]["brier"] is None
    assert h1["probability"]["ece"] is None
    assert h1["drift20"]["sample_count"] == MIN_MAE
    assert h1["drift20"]["mae"] == 0.01
    assert scored["promotion_allowed"] is False
    journal.close()


def test_journal_drift20_mae_stays_null_below_gate(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    journal.get_or_append(
        forecast_id="tiny",
        symbol="AVAXUSDT",
        forecasted_at="2026-09-01T00:00:00+00:00",
        model_id=SHADOW_CATCHUP_MODEL,
        payload=_row("2026-09-01T00:00:00+00:00", 0.01),
    )
    journal.get_or_append_outcome(
        "tiny",
        1,
        {
            "h": 1,
            "matured_at": "2026-09-01T00:05:00+00:00",
            "realized_cum_log_return": 0.02,
        },
    )
    scored = score_journaled_forecasts(
        journal, "AVAXUSDT", as_of=datetime(2026, 9, 2, tzinfo=timezone.utc)
    )
    assert scored["horizons"]["1"]["drift20"]["mae"] is None
    assert scored["horizons"]["1"]["drift20"]["sample_count"] == 1
    journal.close()


def test_drain_matures_outcomes_and_scores_mae(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    runtime.forecast("AVAXUSDT", persist=True)
    before = sum(len(runtime.journal.list_outcomes(row["id"])) for row in runtime.journal.list_forecasts("AVAXUSDT"))
    drained = runtime.drain_shadow_journal("AVAXUSDT", budget=40)
    assert drained["wrote"] > 0
    assert drained["outcomes"]["outcomes_written"] > 0
    after = sum(len(runtime.journal.list_outcomes(row["id"])) for row in runtime.journal.list_forecasts("AVAXUSDT"))
    assert after > before
    metrics = runtime.metrics("AVAXUSDT")
    h1 = metrics["horizons"]["1"]
    assert h1["drift20"]["source"] == "journal"
    assert h1["drift20"]["sample_count"] >= MIN_MAE
    assert h1["drift20"]["mae"] is not None
    assert metrics["promotion_allowed"] is False
    runtime.close()
    reset_runtime()
