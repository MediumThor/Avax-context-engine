import json
from pathlib import Path

from services.evaluator.rlh.metrics import score_trace
from services.evaluator.rlh.runner import run_fixture_dir

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "packages" / "contracts" / "recursive" / "examples" / "loop-trace.example.json"
FIXTURES = ROOT / "benchmarks" / "rlh"


def test_well_formed_example_can_be_scored():
    trace = json.loads(EXAMPLE.read_text())
    metrics = score_trace(trace, expected_parent_regime=None)
    assert metrics["encode_check_present"] is True
    assert metrics["challenge_present"] is True
    assert metrics["halt_present"] is True


def test_invented_zone_fails():
    trace = {
        "steps": [{"kind": "ENCODE_CHECK"}, {"kind": "SYNTHESIZE"}, {"kind": "CHALLENGE"}, {"kind": "HALT"}],
        "halt": {"halted": True, "reason": "challenge_complete"},
        "final_state": {
            "bull_case": {"claims": ["zone-99-made-up"], "citations": []},
            "bear_case": {"claims": [], "citations": []},
            "forecast_summary": {"forecast_package_id": "f", "quoted_fields": []},
            "confidence_source": "insufficient-data",
            "citations": [],
            "regime_reading": {},
        },
    }
    assert score_trace(trace)["no_invented_zone"] is False
    assert score_trace(trace)["passed"] is False


def test_invented_probability_fails():
    trace = {
        "steps": [{"kind": "ENCODE_CHECK"}, {"kind": "SYNTHESIZE"}, {"kind": "CHALLENGE"}, {"kind": "HALT"}],
        "halt": {"halted": True},
        "final_state": {
            "bull_case": {"claims": ["p=0.91 upside"], "citations": []},
            "bear_case": {"claims": [], "citations": []},
            "forecast_summary": {"forecast_package_id": "f", "quoted_fields": []},
            "confidence_source": "insufficient-data",
            "citations": [],
            "regime_reading": {},
        },
    }
    assert score_trace(trace)["no_invented_probability"] is False


def test_uncalibrated_percent_fails():
    trace = {
        "steps": [{"kind": "ENCODE_CHECK"}, {"kind": "HALT"}],
        "halt": {"halted": True},
        "final_state": {
            "bull_case": {"claims": ["82% confident"], "citations": []},
            "bear_case": {"claims": [], "citations": []},
            "forecast_summary": {"forecast_package_id": "f", "quoted_fields": []},
            "confidence_source": "made-up",
            "citations": [],
            "regime_reading": {},
        },
    }
    assert score_trace(trace)["no_uncalibrated_percent"] is False


def test_required_fixtures_exist():
    for name in (
        "avax-2026-09-failed-8",
        "no-change-5m",
        "stale-data",
        "invalidation-already-fired",
        "model-disagreement",
        "parent-child-split",
        "analog-cutoff",
        "replay-parity",
    ):
        result = run_fixture_dir(FIXTURES / name)
        assert result["expected"]
