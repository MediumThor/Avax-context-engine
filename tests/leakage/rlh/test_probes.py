"""Five blocking RLH leakage probes."""

from datetime import datetime, timedelta, timezone

import pytest

from packages.context_engine import Candle, ContextEngine
from services.harness.encoder import build_encoder_memory
from services.harness.encoder.tools import EncoderTools, ToolRefusal
from services.harness.loop.runner import run_loop


def _series(n: int = 360) -> list[Candle]:
    t0 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    out = []
    price = 8.4
    for i in range(n):
        close = price - 0.002
        out.append(
            Candle(
                "AVAXUSDT",
                "5m",
                t0 + timedelta(minutes=5 * i),
                price,
                max(price, close) + 0.01,
                min(price, close) - 0.01,
                close,
                50 + i,
            )
        )
        price = close
    return out


def _forecast():
    return {"id": "forecast-leak", "calibration_ref": "cal-1", "horizons": []}


def test_probe_1_future_candle_perturbation_at_t():
    xs = _series()
    t = 250
    as_of = xs[t - 1].open_time
    snap = ContextEngine().build_snapshot(xs[:t])
    observations = [{"open_time": c.open_time, "is_closed": True} for c in xs[:t]]
    a = build_encoder_memory(
        as_of=as_of,
        snapshot=snap,
        forecast_package=_forecast(),
        data_manifest_id="m",
        observations=observations,
    )
    future = [
        Candle("AVAXUSDT", "5m", c.open_time, 1, 2, 0.5, 1.5, 9_999_999) for c in xs[t:]
    ]
    snap_b = ContextEngine().build_snapshot(xs[:t])
    b = build_encoder_memory(
        as_of=as_of,
        snapshot=snap_b,
        forecast_package=_forecast(),
        data_manifest_id="m",
        observations=[{"open_time": c.open_time, "is_closed": True} for c in xs[:t] + future],
    )
    assert a["content_hash"] == b["content_hash"]
    live = run_loop(memory=a, forecast=_forecast(), directional=False, commit_sha="leak")
    replay = run_loop(memory=b, forecast=_forecast(), directional=False, commit_sha="leak")
    assert live["content_hash"] == replay["content_hash"]


def test_probe_2_unfinished_parent_candle_injection():
    as_of = datetime(2026, 9, 13, 10, 35, tzinfo=timezone.utc)
    snap = ContextEngine().build_snapshot(_series())
    memory = build_encoder_memory(
        as_of=as_of,
        snapshot=snap,
        forecast_package=_forecast(),
        data_manifest_id="m",
        observations=[
            {"open_time": as_of, "is_closed": True},
            {"open_time": datetime(2026, 9, 13, 10, 0, tzinfo=timezone.utc), "is_closed": False, "partial": True},
        ],
    )
    assert memory["_legal_observation_count"] == 1


def test_probe_3_analog_post_cutoff_bait_refused():
    memory = build_encoder_memory(
        as_of="2026-09-13T09:05:00Z",
        snapshot={
            "symbol": "AVAXUSDT",
            "id": "s",
            "timeframes": {tf: {"regime": "bearish"} for tf in ("1w", "1d", "4h", "1h", "15m", "5m")},
        },
        forecast_package=_forecast(),
        data_manifest_id="m",
        memory_id="encmem-analog",
    )
    tools = EncoderTools(
        memory,
        analogs=[{"id": "bait", "known_at": "2026-09-13T10:00:00Z", "as_of": "2026-09-13T10:00:00Z"}],
    )
    with pytest.raises(ToolRefusal) as exc:
        tools.call("analog.search", {"as_of": "2026-09-13T09:05:00Z"})
    assert exc.value.reason == "future_data"


def test_probe_4_warm_start_with_future_outcomes_refused():
    memory = build_encoder_memory(
        as_of="2026-09-13T09:05:00Z",
        snapshot={
            "symbol": "AVAXUSDT",
            "id": "s",
            "timeframes": {tf: {"regime": "bearish"} for tf in ("1w", "1d", "4h", "1h", "15m", "5m")},
        },
        forecast_package=_forecast(),
        data_manifest_id="m",
        memory_id="encmem-warm",
    )
    with pytest.raises(ToolRefusal) as exc:
        run_loop(
            memory=memory,
            forecast=_forecast(),
            warm_start={"outcomes_matured_after": ["h1-from-future"]},
            directional=False,
        )
    assert exc.value.reason == "warm_start_future_outcomes"


def test_probe_5_tool_missing_as_of_refused():
    memory = build_encoder_memory(
        as_of="2026-09-13T09:05:00Z",
        snapshot={
            "symbol": "AVAXUSDT",
            "id": "s",
            "timeframes": {tf: {"regime": "bearish"} for tf in ("1w", "1d", "4h", "1h", "15m", "5m")},
        },
        forecast_package=_forecast(),
        data_manifest_id="m",
        memory_id="encmem-asof",
    )
    tools = EncoderTools(memory)
    with pytest.raises(ToolRefusal) as exc:
        tools.call("market.get_snapshot", {})
    assert exc.value.reason == "missing_as_of"
