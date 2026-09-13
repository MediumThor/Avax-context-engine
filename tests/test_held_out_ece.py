from __future__ import annotations

from datetime import datetime, timedelta, timezone

from packages.evaluator.calibration import expected_calibration_error
from packages.evaluator.held_out import (
    MIN_ECE,
    held_out_ece,
    held_out_start_index,
    row_eligible_for_live_ece,
)
from packages.journal import ForecastJournal
from packages.models import score_journaled_forecasts, walk_forward_probabilities
from packages.models.probability_walkforward import MIN_BRIER
from tests.test_freqai_quantiles import make_5m, mutate_after


def test_fixture_source_never_reports_ece():
    y = [0.0, 1.0] * 20
    p = [0.1, 0.9] * 20
    held = held_out_ece(y, p, report_source="fixture")
    assert held["ece"] is None
    assert held["reason"] == "requires-live-non-fixture"
    assert held["promotion_allowed"] is False


def test_unknown_source_never_reports_ece():
    y = [1.0] * 20
    p = [0.8] * 20
    held = held_out_ece(y, p, report_source=None)
    assert held["ece"] is None
    assert held["reason"] == "requires-live-non-fixture"


def test_held_out_ece_uses_later_slice_not_discovery():
    # First 24 pairs are badly miscalibrated; last 16 are perfectly calibrated.
    y = [1.0] * 24 + [0.0, 1.0] * 8
    p = [0.05] * 24 + [0.0, 1.0] * 8
    held = held_out_ece(y, p, report_source="binance-vision")
    assert held["held_out_sample_count"] >= MIN_ECE
    assert held["ece"] is not None
    assert held["ece"] < 0.05
    full = expected_calibration_error(y, p, bins=5)
    assert held["ece"] < full


def test_short_held_out_window_stays_null():
    y = [0.0, 1.0] * 10
    p = [0.2, 0.8] * 10
    held = held_out_ece(y, p, report_source="binance-vision")
    assert held["sample_count"] == 20
    assert held["held_out_sample_count"] < MIN_ECE
    assert held["ece"] is None
    assert held["reason"] == "insufficient-held-out"


def test_fixture_tagged_row_excluded_from_live_ece():
    assert row_eligible_for_live_ece("fixture", "binance-vision") is False
    assert row_eligible_for_live_ece(None, "binance-vision") is True
    assert row_eligible_for_live_ece("binance-vision", "fixture") is False


def _append_prob_row(journal: ForecastJournal, *, fid: str, issued: datetime, p: float, y: bool, source: str | None):
    payload = {
        "forecasted_at": issued.isoformat(),
        "horizons": [{"h": 1, "p_close_above_origin": p}],
    }
    if source is not None:
        payload["candle_source"] = source
    journal.get_or_append(
        forecast_id=fid,
        symbol="AVAXUSDT",
        forecasted_at=issued.isoformat(),
        model_id="empirical_signed_base_rate.v1",
        payload=payload,
    )
    journal.get_or_append_outcome(
        fid,
        1,
        {
            "h": 1,
            "matured_at": (issued + timedelta(minutes=5)).isoformat(),
            "realized_close_above_origin": y,
        },
    )


def test_journal_scores_withhold_ece_on_fixture(tmp_path):
    journal = ForecastJournal(tmp_path / "fixture.db")
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    for i in range(40):
        _append_prob_row(
            journal,
            fid=f"f-fix-{i}",
            issued=start + timedelta(minutes=5 * i),
            p=0.9 if i % 2 else 0.1,
            y=bool(i % 2),
            source="fixture",
        )
    scored = score_journaled_forecasts(journal, "AVAXUSDT", candle_source="fixture")
    prob = scored["horizons"]["1"]["probability"]
    assert scored["promotion_allowed"] is False
    assert prob["sample_count"] >= MIN_BRIER
    assert prob["brier"] is not None
    assert prob["ece"] is None
    assert prob["ece_reason"] == "requires-live-non-fixture"
    journal.close()


def test_journal_scores_held_out_ece_on_live(tmp_path):
    journal = ForecastJournal(tmp_path / "live.db")
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    for i in range(40):
        well = i >= 24
        _append_prob_row(
            journal,
            fid=f"f-live-{i}",
            issued=start + timedelta(minutes=5 * i),
            p=1.0 if well and i % 2 else (0.0 if well else 0.05),
            y=bool(i % 2) if well else True,
            source="binance-vision",
        )
    scored = score_journaled_forecasts(journal, "AVAXUSDT", candle_source="binance-vision")
    prob = scored["horizons"]["1"]["probability"]
    assert scored["ece_gate"] == "live_non_fixture_held_out"
    assert prob["ece"] is not None
    assert 0.0 <= prob["ece"] <= 1.0
    assert prob["ece_held_out_sample_count"] >= MIN_ECE
    assert scored["promotion_allowed"] is False
    journal.close()


def test_journal_future_rows_do_not_change_held_out_ece(tmp_path):
    journal = ForecastJournal(tmp_path / "asof.db")
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    as_of = start + timedelta(minutes=5 * 39)
    for i in range(50):
        _append_prob_row(
            journal,
            fid=f"f-asof-{i}",
            issued=start + timedelta(minutes=5 * i),
            p=0.8 if i % 2 else 0.2,
            y=bool(i % 2),
            source="binance-vision",
        )
    before = score_journaled_forecasts(
        journal, "AVAXUSDT", as_of=as_of, candle_source="binance-vision"
    )
    _append_prob_row(
        journal,
        fid="f-future",
        issued=as_of + timedelta(days=1),
        p=0.01,
        y=False,
        source="binance-vision",
    )
    after = score_journaled_forecasts(
        journal, "AVAXUSDT", as_of=as_of, candle_source="binance-vision"
    )
    assert before["horizons"]["1"]["probability"]["ece"] == after["horizons"]["1"]["probability"]["ece"]
    assert before["horizons"]["1"]["probability"]["sample_count"] == after["horizons"]["1"]["probability"]["sample_count"]
    journal.close()


def test_walk_forward_fixture_ece_is_null():
    from packages.fixtures import sept_2026_failed_breakout

    candles = sept_2026_failed_breakout()
    report = walk_forward_probabilities(
        candles, horizons=10, min_history=80, step=20, candle_source="fixture"
    )
    assert report["promotion_allowed"] is False
    h1 = report["horizons"]["1"]["probability"]
    assert h1["brier"] is not None
    assert h1["ece"] is None
    assert h1["ece_reason"] == "requires-live-non-fixture"


def test_walk_forward_live_held_out_ece_and_no_future_leak():
    candles = make_5m(220)
    as_of = candles[180].close_time()
    before = walk_forward_probabilities(
        candles,
        horizons=1,
        min_history=80,
        step=2,
        as_of=as_of,
        candle_source="binance-vision",
    )
    after = walk_forward_probabilities(
        mutate_after(candles, 181),
        horizons=1,
        min_history=80,
        step=2,
        as_of=as_of,
        candle_source="binance-vision",
    )
    assert before == after
    ece = before["horizons"]["1"]["probability"]["ece"]
    if ece is not None:
        assert 0.0 <= ece <= 1.0
        assert before["horizons"]["1"]["probability"]["ece_held_out_sample_count"] >= MIN_ECE


def test_held_out_start_leaves_a_discovery_window():
    assert held_out_start_index(40) == 24
    assert held_out_start_index(2) == 1
    assert held_out_start_index(1) == 1


def test_runtime_stamps_fixture_source_and_withholds_ece(tmp_path):
    from services.api.runtime import PrototypeRuntime

    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    body = runtime.forecast("AVAXUSDT")
    payload = body["forecast"]
    assert payload["candle_source"] == "fixture"
    latest = runtime.journal.latest("AVAXUSDT")
    assert latest is not None
    assert latest["payload"]["candle_source"] == "fixture"
    metrics = runtime.metrics("AVAXUSDT")
    ece = (metrics.get("horizons") or {}).get("1", {}).get("probability", {}).get("ece")
    assert ece is None
    assert metrics["promotion_allowed"] is False
    runtime.close()
