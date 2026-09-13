from datetime import datetime, timezone

from services.evaluator.rlh.depth import NOTES, ablate_depths
from services.harness.encoder import build_encoder_memory


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
    return build_encoder_memory(
        as_of=datetime(2026, 9, 13, 9, 5, tzinfo=timezone.utc),
        snapshot={"symbol": "AVAXUSDT", "id": "snapshot-depth-ablation", "timeframes": slices},
        forecast_package={"id": "forecast-depth-ablation", "calibration_ref": "cal-1", "horizons": []},
        data_manifest_id="m1",
        health=overrides.get("health", "valid"),
        memory_id="encmem-depth-ablation",
        hypothesis_ids=["hyp-bear"],
        zone_ids=["zone-8-00-8-20"],
        cross_market={"btc_regime": "bearish"},
    )


def _forecast():
    return {"id": "forecast-depth-ablation", "calibration_ref": "cal-1", "horizons": []}


def test_depth_one_halts_at_encode_check_or_max_depth():
    report = ablate_depths(
        _memory(),
        _forecast(),
        depths=(1,),
        directional=False,
        commit_sha="test",
    )
    row = report["rows"][0]
    assert row["step_count"] >= 1
    assert row["halt_reason"] == "max_depth"
    assert row["process_metrics"]["encode_check_present"] is True


def test_forecast_package_unchanged_across_depths():
    forecast = _forecast()
    before = dict(forecast)
    report = ablate_depths(
        _memory(),
        forecast,
        depths=(1, 2, 4, 8),
        directional=False,
        commit_sha="test",
    )
    assert forecast == before
    snapshots = [report["forecast_package_snapshot"]] + [
        row["forecast_package_id"] for row in report["rows"]
    ]
    assert all(item == "forecast-depth-ablation" for item in snapshots[1:])
    assert report["forecast_package_snapshot"] == before


def test_no_invented_probability_at_any_depth():
    report = ablate_depths(
        _memory(),
        _forecast(),
        depths=(1, 2, 4, 8, 16),
        directional=False,
        commit_sha="test",
    )
    for row in report["rows"]:
        assert row["process_metrics"]["no_invented_probability"] is True


def test_encoder_memory_hash_stable_across_depths():
    memory = _memory()
    report = ablate_depths(
        memory,
        _forecast(),
        depths=(1, 2, 4, 8, 16),
        directional=False,
        commit_sha="test",
    )
    hashes = {row["encoder_memory_hash"] for row in report["rows"]}
    assert len(hashes) == 1
    assert memory["content_hash"] in hashes


def test_no_change_fires_when_immaterial_5m():
    report = ablate_depths(
        _memory(),
        _forecast(),
        depths=(8, 16),
        directional=False,
        commit_sha="test",
    )
    for row in report["rows"]:
        assert row["no_change_fired"] is True
        assert row["halt_reason"] == "no_change"


def test_promotion_not_allowed_and_notes_disclaim_accuracy():
    report = ablate_depths(_memory(), _forecast(), depths=(1,), commit_sha="test")
    assert report["promotion_allowed"] is False
    assert "NOT an accuracy claim" in NOTES
    assert report["notes"] == NOTES
