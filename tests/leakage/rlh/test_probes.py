"""Six blocking RLH leakage probes (wiki Recursive-Evaluation + parent-regime guard)."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from packages.context_engine import Candle, ContextEngine
from services.harness.encoder import PARENT_TIMEFRAMES, build_encoder_memory, overlay_5m_observation
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


def _bearish_snapshot(*, four_h: str = "bearish", five_m: str = "transition_up") -> dict:
    return {
        "symbol": "AVAXUSDT",
        "id": "s",
        "timeframes": {
            tf: {"regime": four_h if tf == "4h" else ("bearish" if tf in {"1d", "1w"} else five_m if tf == "5m" else "neutral")}
            for tf in ("1w", "1d", "4h", "1h", "15m", "5m")
        },
    }


def _encode_check_hash(trace: dict) -> str:
    encode = next(step for step in trace["steps"] if step["kind"] == "ENCODE_CHECK")
    assert encode["encoder_memory_hash"] == trace["encoder_memory_hash"]
    return encode["encoder_memory_hash"]


def test_probe_1_future_candle_perturbation_at_t():
    xs = _series()
    t = 250
    as_of = xs[t - 1].open_time
    snap = ContextEngine().build_snapshot(xs[:t])
    closed_obs = [{"open_time": c.open_time, "is_closed": True} for c in xs[:t]]
    a = build_encoder_memory(
        as_of=as_of,
        snapshot=snap,
        forecast_package=_forecast(),
        data_manifest_id="m",
        observations=closed_obs,
    )
    future = [
        Candle("AVAXUSDT", "5m", c.open_time, 1, 2, 0.5, 1.5, 9_999_999) for c in xs[t:]
    ]
    snap_b = ContextEngine().build_snapshot(xs[:t])
    bait_obs = closed_obs + [{"open_time": c.open_time, "is_closed": True} for c in future]
    b = build_encoder_memory(
        as_of=as_of,
        snapshot=snap_b,
        forecast_package=_forecast(),
        data_manifest_id="m",
        observations=bait_obs,
    )
    assert a["content_hash"] == b["content_hash"]
    assert a["timeframe_slices"]["4h"] == b["timeframe_slices"]["4h"]
    assert b["_legal_observation_count"] == len(closed_obs)

    live = run_loop(memory=a, forecast=_forecast(), directional=False, commit_sha="leak")
    replay = run_loop(memory=b, forecast=_forecast(), directional=False, commit_sha="leak")
    assert live["encoder_memory_hash"] == replay["encoder_memory_hash"] == a["content_hash"]
    assert _encode_check_hash(live) == _encode_check_hash(replay)
    assert live["content_hash"] == replay["content_hash"]


def test_probe_2_unfinished_parent_candle_ignored():
    as_of = datetime(2026, 9, 13, 10, 35, tzinfo=timezone.utc)
    snap = ContextEngine().build_snapshot(_series())
    closed_only = [{"open_time": as_of, "is_closed": True, "timeframe": "5m"}]
    baseline = build_encoder_memory(
        as_of=as_of,
        snapshot=snap,
        forecast_package=_forecast(),
        data_manifest_id="m",
        observations=closed_only,
    )
    with_partial_parent = build_encoder_memory(
        as_of=as_of,
        snapshot=snap,
        forecast_package=_forecast(),
        data_manifest_id="m",
        observations=closed_only
        + [
            {
                "open_time": datetime(2026, 9, 13, 10, 0, tzinfo=timezone.utc),
                "known_at": "2026-09-13T11:00:00Z",
                "is_closed": False,
                "partial": True,
                "timeframe": "4h",
            }
        ],
    )
    assert with_partial_parent["_legal_observation_count"] == 1
    assert baseline["content_hash"] == with_partial_parent["content_hash"]
    assert baseline["timeframe_slices"]["4h"] == with_partial_parent["timeframe_slices"]["4h"]


def test_probe_3_tool_refuses_known_at_after_as_of():
    memory = build_encoder_memory(
        as_of="2026-09-13T09:05:00Z",
        snapshot=_bearish_snapshot(),
        forecast_package=_forecast(),
        data_manifest_id="m",
        memory_id="encmem-analog",
    )
    as_of = memory["as_of"]
    future_row = {"id": "bait", "known_at": "2026-09-13T10:00:00Z", "as_of": "2026-09-13T10:00:00Z"}

    with pytest.raises(ToolRefusal) as exc:
        EncoderTools(memory, analogs=[future_row]).call("analog.search", {"as_of": as_of})
    assert exc.value.reason == "future_data"

    with pytest.raises(ToolRefusal) as exc:
        EncoderTools(memory, hypotheses=[future_row]).call("context.get_hypotheses", {"as_of": as_of})
    assert exc.value.reason == "future_data"

    with pytest.raises(ToolRefusal) as exc:
        EncoderTools(memory).call(
            "forecast.get_history",
            {"as_of": as_of, "history": [{"id": "h-future", "known_at": "2026-09-14T00:00:00Z"}]},
        )
    assert exc.value.reason == "future_data"

    with pytest.raises(ToolRefusal) as exc:
        EncoderTools(memory).call(
            "evaluation.get_metrics",
            {"as_of": as_of, "metrics": {"matured_at": "2026-09-14T00:00:00Z"}},
        )
    assert exc.value.reason == "future_metrics"


def test_probe_4_five_m_cannot_overwrite_parent_regime():
    snap = _bearish_snapshot(four_h="bearish", five_m="bearish")
    memory = build_encoder_memory(
        as_of="2026-09-13T09:05:00Z",
        snapshot=snap,
        forecast_package=_forecast(),
        data_manifest_id="m",
        memory_id="encmem-parent",
    )
    parents_before = {name: deepcopy(memory["timeframe_slices"][name]) for name in PARENT_TIMEFRAMES}
    assert memory["timeframe_slices"]["4h"]["regime"] == "bearish"

    updated = overlay_5m_observation(memory, {"regime": "bullish", "swing_state": "relief_bounce"})
    for name in PARENT_TIMEFRAMES:
        assert updated["timeframe_slices"][name] == parents_before[name]
    assert updated["timeframe_slices"]["4h"]["regime"] == "bearish"
    assert updated["timeframe_slices"]["5m"]["regime"] == "bullish"
    assert updated["content_hash"] != memory["content_hash"]

    trace = run_loop(memory=updated, forecast=_forecast(), directional=True, commit_sha="leak")
    assert trace["encoder_memory_hash"] == updated["content_hash"]
    assert trace["final_state"]["regime_reading"]["4h"] == "bearish"
    assert trace["final_state"]["regime_reading"]["5m"] == "bullish"


def test_probe_5_warm_start_with_future_outcomes_refused():
    memory = build_encoder_memory(
        as_of="2026-09-13T09:05:00Z",
        snapshot=_bearish_snapshot(),
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
    assert exc.value.name == "loop.warm_start"


def test_probe_6_tool_missing_as_of_refused():
    memory = build_encoder_memory(
        as_of="2026-09-13T09:05:00Z",
        snapshot=_bearish_snapshot(),
        forecast_package=_forecast(),
        data_manifest_id="m",
        memory_id="encmem-asof",
    )
    tools = EncoderTools(memory)
    for tool_name in ("market.get_snapshot", "context.get_structure", "analog.search"):
        with pytest.raises(ToolRefusal) as exc:
            tools.call(tool_name, {})
        assert exc.value.reason == "missing_as_of"
        assert exc.value.name == tool_name
