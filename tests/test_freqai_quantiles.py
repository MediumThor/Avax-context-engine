from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from adapters.freqtrade import (
    FreqtradeResearchAdapter,
    NO_BASELINE_CLAIM,
    ResearchOnlyViolation,
    emit_research_quantile_forecast,
)
from adapters.freqtrade.quantiles import main as quantile_cli_main, refuse_live_cli
from adapters.freqtrade.safety import load_research_config, validate_research_config
from packages.context_engine.models import Candle
from packages.journal import ForecastJournal
from packages.models.freqai_quantiles import (
    DECLARED_VERSIONS,
    FEATURE_SCHEMA_VERSION,
    MODEL_ID,
    assert_quantile_order,
    availability_at,
    candle_period_end,
    eligible_train_indices,
    emit_quantile_forecast,
    extract_features_at,
    visible_closed_candles,
)

REPO = Path(__file__).resolve().parents[1]
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_5m(
    n: int,
    *,
    start: float = 10.0,
    step: float = 0.01,
    t0: datetime = T0,
    symbol: str = "AVAXUSDT",
    volume: float = 100.0,
) -> list[Candle]:
    out: list[Candle] = []
    price = start
    for i in range(n):
        close = price + step + 0.004 * math.sin(i / 5.0)
        high = max(price, close) + 0.02
        low = min(price, close) - 0.02
        out.append(
            Candle(
                symbol,
                "5m",
                t0 + timedelta(minutes=5 * i),
                price,
                high,
                low,
                close,
                volume + i,
                is_closed=True,
            )
        )
        price = close
    return out


def as_of_index(candles: list[Candle], index: int) -> datetime:
    return candle_period_end(candles[index])


def mutate_after(candles: list[Candle], first_future: int) -> list[Candle]:
    out = list(candles[:first_future])
    for candle in candles[first_future:]:
        out.append(
            Candle(
                candle.symbol,
                candle.timeframe,
                candle.open_time,
                80.0,
                120.0,
                70.0,
                110.0,
                99_999.0,
                is_closed=True,
            )
        )
    return out


def poison_open_times(candles: list[Candle], opens: set[datetime]) -> list[Candle]:
    out = []
    for candle in candles:
        if candle.open_time in opens:
            out.append(
                Candle(
                    candle.symbol,
                    candle.timeframe,
                    candle.open_time,
                    40.0,
                    55.0,
                    30.0,
                    50.0,
                    77_777.0,
                    is_closed=True,
                )
            )
        else:
            out.append(candle)
    return out


def unclosed(candle: Candle) -> Candle:
    return Candle(
        candle.symbol,
        candle.timeframe,
        candle.open_time,
        90.0,
        140.0,
        60.0,
        130.0,
        88_888.0,
        is_closed=False,
    )


def _horizons(payload: dict) -> list[dict]:
    return payload["horizons"]


def test_python_backend_emits_journal_ready_quantiles():
    candles = make_5m(130)
    as_of = as_of_index(candles, 119)
    payload = emit_quantile_forecast(candles, as_of=as_of, backend="python")
    assert_quantile_order(payload)
    assert payload["model_id"] == MODEL_ID
    assert payload["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert payload["research_only"] is True
    assert payload["live_trading"] is False
    assert payload["dry_run"] is True
    assert payload["max_open_trades"] == 0
    assert payload["stake_amount"] == 0
    assert payload["freqai_beats_baselines"] is None
    assert payload["backend"] == "python"
    assert payload["train_origin_count"] >= 30
    assert [row["h"] for row in _horizons(payload)] == list(range(1, 11))
    for row in _horizons(payload):
        assert row["q10_cum_log_return"] <= row["q50_cum_log_return"] <= row["q90_cum_log_return"]
    assert "accuracy" not in json.dumps(payload).lower()
    assert "ece" not in json.dumps(payload).lower()
    assert DECLARED_VERSIONS["lightgbm"].startswith(">=4.5")
    assert DECLARED_VERSIONS["scikit-learn"].startswith(">=1.5")


def test_future_perturbation_does_not_change_forecast_at_t():
    candles = make_5m(140)
    origin = 119
    as_of = as_of_index(candles, origin)
    baseline = emit_quantile_forecast(candles, as_of=as_of, backend="python")
    mutated = mutate_after(candles, origin + 1)
    after = emit_quantile_forecast(mutated, as_of=as_of, backend="python")
    assert _horizons(baseline) == _horizons(after)
    assert baseline["origin_close"] == after["origin_close"]
    assert baseline["feature_schema_version"] == after["feature_schema_version"]
    assert baseline["availability"] == after["availability"]


def test_unclosed_and_unfinished_parent_unused():
    candles = make_5m(127)  # last open 10:30, period_end 10:35
    as_of = as_of_index(candles, 126)
    assert as_of == datetime(2026, 1, 1, 10, 35, tzinfo=timezone.utc)

    baseline = emit_quantile_forecast(candles, as_of=as_of, backend="python")
    features = extract_features_at(candles, as_of)
    avail = availability_at(candles, as_of)
    assert avail["avax_1h_last_open_time"] == datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc).isoformat()
    assert avail["avax_15m_last_open_time"] == datetime(2026, 1, 1, 10, 15, tzinfo=timezone.utc).isoformat()

    extra_unclosed = candles + [unclosed(make_5m(1, t0=datetime(2026, 1, 1, 10, 35, tzinfo=timezone.utc))[0])]
    after_unclosed = emit_quantile_forecast(extra_unclosed, as_of=as_of, backend="python")
    assert _horizons(baseline) == _horizons(after_unclosed)

    unfinished_1h = {
        datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 10, 5, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 10, 10, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 10, 15, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 10, 20, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 10, 25, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 10, 30, tzinfo=timezone.utc),
    }
    poisoned = poison_open_times(candles, unfinished_1h)
    poisoned_features = extract_features_at(poisoned, as_of)
    assert poisoned_features["htf_1h_logret_1"] == features["htf_1h_logret_1"]
    assert availability_at(poisoned, as_of)["avax_1h_last_open_time"] == avail["avax_1h_last_open_time"]

    # Explicit unfinished 1h bar must never enter the 5m training series.
    fake_parent = Candle(
        "AVAXUSDT",
        "1h",
        datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        20.0,
        40.0,
        15.0,
        35.0,
        50_000.0,
        is_closed=False,
    )
    with_fake = candles + [fake_parent]
    assert len(visible_closed_candles(with_fake, as_of)) == len(visible_closed_candles(candles, as_of))
    assert extract_features_at(with_fake, as_of) == features
    assert _horizons(emit_quantile_forecast(with_fake, as_of=as_of, backend="python")) == _horizons(baseline)


def test_train_origins_require_matured_horizon_before_or_at_t():
    candles = make_5m(80)
    as_of = as_of_index(candles, 69)
    visible = visible_closed_candles(candles, as_of)
    origins = eligible_train_indices(visible, as_of, horizons=10, min_feature_bars=24)
    assert origins
    for origin in origins:
        assert candle_period_end(visible[origin + 10]) <= as_of
        assert origin + 10 < len(visible)
    # The forecast origin itself is not a training row: its h=10 close is in the future.
    assert max(origins) == 69 - 10
    assert 69 not in origins


def test_adapter_emit_has_no_order_surface_and_stays_research_only():
    candles = make_5m(130)
    as_of = as_of_index(candles, 119)
    adapter = FreqtradeResearchAdapter(repo_root=REPO)
    payload = adapter.emit_research_quantile_forecast(candles, as_of=as_of, backend="python")
    assert_quantile_order(payload)
    assert payload["research_status"]["live_trading"] is False
    assert payload["research_status"]["freqai_beats_baselines"] is None
    assert "does not claim" in payload["research_status"]["performance_claim"]
    with pytest.raises(ResearchOnlyViolation):
        adapter.place_order()
    with pytest.raises(ResearchOnlyViolation):
        adapter.execute()
    with pytest.raises(ResearchOnlyViolation):
        adapter.research_command("trade")
    config = load_research_config()
    validate_research_config(config)
    assert config["dry_run"] is True
    assert config["max_open_trades"] == 0
    assert config["stake_amount"] == 0


def test_research_cli_refuses_live_flags(capsys):
    with pytest.raises(ResearchOnlyViolation):
        refuse_live_cli(["--trade"])
    with pytest.raises(ResearchOnlyViolation):
        refuse_live_cli(["execute"])
    assert quantile_cli_main(["--help-research"]) == 0
    printed = capsys.readouterr().out
    status = json.loads(printed)
    assert status["live_trading"] is False
    assert status["stake_amount"] == 0
    assert status["freqai_beats_baselines"] is None
    assert status["performance_claim"] == NO_BASELINE_CLAIM


def test_payload_is_journal_appendable(tmp_path):
    candles = make_5m(120)
    as_of = as_of_index(candles, 109)
    payload = emit_research_quantile_forecast(candles, as_of=as_of, backend="python")
    journal = ForecastJournal(tmp_path / "journal.db")
    digest = journal.append_forecast(
        payload["id"],
        payload["symbol"],
        payload["forecasted_at"],
        payload["model_id"],
        payload,
        feature_schema_version=payload["feature_schema_version"],
    )
    stored = journal.get_forecast(payload["id"])
    assert stored["sha256"] == digest
    assert stored["payload"]["horizons"] == payload["horizons"]
    journal.close()


@pytest.mark.parametrize("backend", ["sklearn", "lightgbm"])
def test_optional_backends_skip_if_missing_and_keep_order(backend: str):
    candles = make_5m(130)
    as_of = as_of_index(candles, 119)
    if backend == "sklearn":
        pytest.importorskip("sklearn.ensemble")
    else:
        pytest.importorskip("lightgbm")
    payload = emit_quantile_forecast(candles, as_of=as_of, backend=backend)  # type: ignore[arg-type]
    assert_quantile_order(payload)
    assert payload["backend"] in {backend, "python"}
    assert payload["freqai_beats_baselines"] is None
