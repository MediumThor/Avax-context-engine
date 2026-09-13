from datetime import datetime, timezone

from services.harness.encoder import build_encoder_memory
from services.harness.loop import run_loop, replay_loop


def _memory(**overrides):
    slices = {
        "1w": {"regime": "bearish"},
        "1d": {"regime": "bearish"},
        "4h": {"regime": "bearish"},
        "1h": {"regime": "bearish"},
        "15m": {"regime": "neutral"},
        "5m": {"regime": "neutral"},
    }
    slices.update(overrides.get("slices") or {})
    payload = {
        "id": "encmem-loop-test",
        "schema_version": "1",
        "symbol": "AVAXUSDT",
        "as_of": "2026-09-13T09:05:00Z",
        "context_snapshot_id": "snapshot-loop-test",
        "forecast_package_id": "forecast-loop-test",
        "data_manifest_id": "m1",
        "feature_schema_version": "1",
        "context_engine_version": "1",
        "timeframe_slices": slices,
        "zone_ids": ["zone-8-00-8-20"],
        "hypothesis_ids": ["hyp-bear"],
        "cross_market": {"btc_regime": "bearish"},
        "health": overrides.get("health", "valid"),
    }
    return build_encoder_memory(
        as_of=datetime(2026, 9, 13, 9, 5, tzinfo=timezone.utc),
        snapshot={"symbol": "AVAXUSDT", "id": "snapshot-loop-test", "timeframes": slices},
        forecast_package={"id": "forecast-loop-test", "calibration_ref": "cal-1", "horizons": []},
        data_manifest_id="m1",
        health=payload["health"],
        memory_id="encmem-loop-test",
        hypothesis_ids=["hyp-bear"],
        zone_ids=["zone-8-00-8-20"],
        cross_market={"btc_regime": "bearish"},
    )


def _forecast():
    return {"id": "forecast-loop-test", "calibration_ref": "cal-1", "horizons": []}


def test_required_step_order_and_no_change_shortcut():
    trace = run_loop(memory=_memory(), forecast=_forecast(), directional=False, commit_sha="test")
    kinds = [s["kind"] for s in trace["steps"]]
    assert kinds[0] == "ENCODE_CHECK"
    assert "RETRIEVE" in kinds
    assert "SYNTHESIZE" in kinds
    assert "NO_CHANGE" in kinds
    assert kinds[-2] == "HALT"
    assert kinds[-1] == "JOURNAL"
    assert trace["halt"]["reason"] == "no_change"
    assert "CHALLENGE" not in kinds


def test_max_depth_halt_fires():
    trace = run_loop(memory=_memory(), forecast=_forecast(), max_depth=1, commit_sha="test")
    assert trace["halt"]["reason"] == "max_depth"
    assert [s["kind"] for s in trace["steps"]][0] == "ENCODE_CHECK"
    assert any(s["kind"] == "HALT" for s in trace["steps"])


def test_exact_replay_hash_match():
    kwargs = {"memory": _memory(), "forecast": _forecast(), "directional": False, "commit_sha": "test"}
    live = run_loop(**kwargs)
    replayed = replay_loop(live, **kwargs)
    assert replayed["content_hash"] == live["content_hash"]
    assert all(step["harness_version"] == "rlh-0.1.0" for step in live["steps"])
