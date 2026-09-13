import json
from pathlib import Path

from services.evaluator.rlh.metrics import score_trace
from services.harness.encoder import build_encoder_memory
from services.harness.loop import run_loop
from services.harness.loop.challenge import challenge_and_invalidation
from services.harness.loop.challenge.critic import InvalidationMoveAttempt
from services.harness.loop.state import empty_state

ROOT = Path(__file__).resolve().parents[3]
SEPT = ROOT / "benchmarks" / "rlh" / "avax-2026-09-failed-8"


def _failed_8_memory():
    slices = {
        "1w": {"regime": "bearish"},
        "1d": {"regime": "bearish"},
        "4h": {"regime": "bearish"},
        "1h": {"regime": "bearish"},
        "15m": {"regime": "transition_up"},
        "5m": {"regime": "bullish"},
    }
    return build_encoder_memory(
        as_of="2026-09-13T09:05:00Z",
        snapshot={"symbol": "AVAXUSDT", "id": "snapshot-failed-8", "timeframes": slices},
        forecast_package={"id": "forecast-failed-8", "calibration_ref": "cal-1", "horizons": []},
        data_manifest_id="manifest-failed-8",
        memory_id="encmem-failed-8",
        zone_ids=["zone-8-00-8-20"],
        hypothesis_ids=["hyp-bear-continuation-20260913"],
        cross_market={"btc_regime": "bearish"},
    )


def test_missing_challenge_fails_process_metric():
    bad = {
        "as_of": "2026-09-13T09:05:00Z",
        "steps": [{"kind": "ENCODE_CHECK"}, {"kind": "SYNTHESIZE"}, {"kind": "HALT"}],
        "halt": {"halted": True, "reason": "challenge_complete"},
        "final_state": {
            "regime_reading": {"4h": "bearish"},
            "bull_case": {"claims": [], "citations": []},
            "bear_case": {"claims": [], "citations": []},
            "forecast_summary": {"forecast_package_id": "f", "quoted_fields": []},
            "confidence_source": "insufficient-data",
            "citations": [],
        },
    }
    metrics = score_trace(bad)
    assert metrics["challenge_present"] is False
    assert metrics["passed"] is False


def test_invalidation_edit_attempt_halts():
    memory = _failed_8_memory()
    state = empty_state(forecast_package_id="forecast-failed-8")
    try:
        challenge_and_invalidation(
            state,
            memory,
            attempted_invalidation_edit={"hypothesis_id": "hyp-bear-continuation-20260913", "new_level": 7.80},
        )
        raise AssertionError("expected InvalidationMoveAttempt")
    except InvalidationMoveAttempt:
        pass
    trace = run_loop(
        memory=memory,
        forecast={"id": "forecast-failed-8", "calibration_ref": "cal-1"},
        directional=True,
        attempted_invalidation_edit={"new_level": 7.80},
        commit_sha="test",
    )
    assert trace["halt"]["reason"] == "invalidation_move_attempt"


def test_september_2026_relief_bounce_does_not_reset_4h_bear():
    expected = json.loads((SEPT / "expected_invariants.json").read_text())
    assert expected["parent_regime_after_failed_breakout"] == "bearish"
    assert expected["relief_bounce_is_not_reversal"] is True
    assert expected["invalidation_immutable"] is True
    memory = _failed_8_memory()
    trace = run_loop(
        memory=memory,
        forecast={"id": "forecast-failed-8", "calibration_ref": "cal-1", "horizons": []},
        directional=True,
        hypotheses=[
            {
                "id": "hyp-bear-continuation-20260913",
                "status": "active",
                "invalidation_rules": ["4h close reclaim above 8.20"],
            }
        ],
        commit_sha="test",
    )
    assert trace["final_state"]["regime_reading"]["4h"] == "bearish"
    assert "4h_regime_still_bearish" in trace["final_state"]["what_did_not_change"]
    assert any(s["kind"] == "CHALLENGE" for s in trace["steps"])
    metrics = score_trace(trace, expected_parent_regime="bearish")
    assert metrics["parent_regime_not_overwritten"]
    assert metrics["challenge_present"]
    assert metrics["encode_check_present"]
    assert metrics["no_uncalibrated_percent"]
