from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from packages.context_engine import Candle, ContextEngine
from packages.fixtures import sept_2026_failed_breakout
from services.harness.encoder import (
    PARENT_TIMEFRAMES,
    build_encoder_memory,
    overlay_5m_observation,
    snapshot_analogs,
    snapshot_hypothesis_ids,
    snapshot_theses,
    snapshot_zone_ids,
)
from services.harness.encoder.tools import EncoderTools, ToolRefusal
from services.harness.loop import run_loop


def _candles(n: int = 400, start: float = 10.0, step: float = -0.004) -> list[Candle]:
    t0 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    out = []
    price = start
    for i in range(n):
        close = price + step
        out.append(
            Candle(
                "AVAXUSDT",
                "5m",
                t0 + timedelta(minutes=5 * i),
                price,
                max(price, close) + 0.02,
                min(price, close) - 0.02,
                close,
                100 + i,
            )
        )
        price = close
    return out


def _forecast() -> dict:
    return {"id": "forecast-test-1", "calibration_ref": "cal-1", "horizons": []}


def test_future_candle_perturbation_does_not_change_hash():
    xs = _candles()
    cutoff = 300
    as_of = xs[cutoff - 1].open_time
    snap = ContextEngine().build_snapshot(xs[:cutoff])
    a = build_encoder_memory(
        as_of=as_of,
        snapshot=snap,
        forecast_package=_forecast(),
        data_manifest_id="m1",
        observations=[{"open_time": c.open_time, "is_closed": True} for c in xs[:cutoff]],
    )
    mutated = xs[:cutoff] + [
        Candle("AVAXUSDT", "5m", c.open_time, 100, 110, 90, 105, 99999) for c in xs[cutoff:]
    ]
    snap_b = ContextEngine().build_snapshot(mutated[:cutoff])
    b = build_encoder_memory(
        as_of=as_of,
        snapshot=snap_b,
        forecast_package=_forecast(),
        data_manifest_id="m1",
        observations=[{"open_time": c.open_time, "is_closed": True} for c in mutated],
    )
    assert a["content_hash"] == b["content_hash"]
    assert a["timeframe_slices"]["4h"] == b["timeframe_slices"]["4h"]


def test_unfinished_parent_candle_ignored():
    as_of = datetime(2026, 9, 13, 10, 35, tzinfo=timezone.utc)
    snap = ContextEngine().build_snapshot(_candles())
    observations = [
        {"open_time": as_of.isoformat(), "known_at": as_of.isoformat(), "is_closed": True, "timeframe": "5m"},
        {
            "open_time": "2026-09-13T10:00:00+00:00",
            "known_at": "2026-09-13T11:00:00+00:00",
            "is_closed": False,
            "partial": True,
            "timeframe": "1h",
        },
    ]
    memory = build_encoder_memory(
        as_of=as_of,
        snapshot=snap,
        forecast_package=_forecast(),
        data_manifest_id="m1",
        observations=observations,
    )
    assert memory["_legal_observation_count"] == 1


def test_5m_overlay_cannot_write_parent_slices():
    snap = ContextEngine().build_snapshot(_candles())
    memory = build_encoder_memory(
        as_of=snap.as_of, snapshot=snap, forecast_package=_forecast(), data_manifest_id="m1"
    )
    parents = {name: deepcopy(memory["timeframe_slices"][name]) for name in PARENT_TIMEFRAMES}
    updated = overlay_5m_observation(memory, {"regime": "bullish", "swing_state": "mixed"})
    for name in PARENT_TIMEFRAMES:
        assert updated["timeframe_slices"][name] == parents[name]
    assert updated["timeframe_slices"]["5m"]["regime"] == "bullish"
    assert updated["content_hash"] != memory["content_hash"]


def test_fixture_snapshot_fills_encoder_ids_and_analog_search():
    snap = ContextEngine().build_snapshot(sept_2026_failed_breakout())
    memory = build_encoder_memory(
        as_of=snap.as_of, snapshot=snap, forecast_package=_forecast(), data_manifest_id="m1"
    )
    assert memory["hypothesis_ids"] == snapshot_hypothesis_ids(snap)
    assert memory["hypothesis_ids"]
    assert memory["zone_ids"] == snapshot_zone_ids(snap)
    assert memory["zone_ids"]
    analogs = snapshot_analogs(snap)
    theses = snapshot_theses(snap)
    assert analogs
    for row in analogs:
        assert row["known_at"].endswith("Z")
        assert row["known_at"] <= memory["as_of"]
    for row in theses:
        assert row["known_at"].endswith("Z")
        assert row["known_at"] <= memory["as_of"]
    tools = EncoderTools(memory, analogs=analogs, hypotheses=theses)
    found = tools.call("analog.search", {"as_of": memory["as_of"]})
    assert len(found["response"]) == len(analogs)
    hyps = tools.call("context.get_hypotheses", {"as_of": memory["as_of"]})
    assert [row["id"] for row in hyps["response"]] == memory["hypothesis_ids"]
    bait = list(analogs) + [{"id": "bait", "known_at": "2099-01-01T00:00:00Z"}]
    with pytest.raises(ToolRefusal) as exc:
        EncoderTools(memory, analogs=bait).call("analog.search", {"as_of": memory["as_of"]})
    assert exc.value.reason == "future_data"


def test_live_loop_with_snapshot_analogs_is_replay_stable():
    snap = ContextEngine().build_snapshot(sept_2026_failed_breakout())
    memory = build_encoder_memory(
        as_of=snap.as_of, snapshot=snap, forecast_package=_forecast(), data_manifest_id="m1"
    )
    analogs = snapshot_analogs(snap)
    theses = snapshot_theses(snap)
    kwargs = {
        "memory": memory,
        "forecast": _forecast(),
        "tools": EncoderTools(memory, analogs=analogs, hypotheses=theses),
        "hypotheses": theses,
        "commit_sha": "live-context",
    }
    live = run_loop(**kwargs)
    replay = run_loop(
        memory=memory,
        forecast=_forecast(),
        tools=EncoderTools(memory, analogs=analogs, hypotheses=theses),
        hypotheses=theses,
        commit_sha="live-context",
    )
    assert live["content_hash"] == replay["content_hash"]
    retrieve = next(step for step in live["steps"] if step["kind"] == "RETRIEVE")
    assert len(retrieve["emit"]["tool_response_hashes"]) >= 5
