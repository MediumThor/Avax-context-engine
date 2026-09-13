"""Challenger q50 vs drift20 is opt-in on metrics and never a promotion."""

from fastapi.testclient import TestClient

from services.api.runtime import PrototypeRuntime, reset_runtime


def test_metrics_attaches_q50_without_promotion(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    fake = {
        "model_id": "freqai.quantiles.research.v1",
        "origin_count": 3,
        "promotion_allowed": True,
        "q50_mae_below_drift20_on_all_scored_horizons": False,
        "notes": "Research walk-forward only.",
        "horizons": {
            "1": {
                "sample_count": 3,
                "q50": {"mae": 0.01, "rmse": 0.02},
                "q50_mae_minus_drift20_mae": 0.002,
            }
        },
    }
    monkeypatch.setattr("services.api.runtime.walk_forward_quantiles", lambda *a, **k: fake)
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    plain = runtime.metrics("AVAXUSDT")
    assert "q50" not in plain["horizons"]["1"]
    assert plain["promotion_allowed"] is False
    metrics = runtime.metrics("AVAXUSDT", include_challenger=True)
    assert metrics["promotion_allowed"] is False
    assert metrics["challenger"]["model_id"] == "freqai.quantiles.research.v1"
    assert metrics["challenger"]["q50_mae_below_drift20_on_all_scored_horizons"] is False
    assert metrics["horizons"]["1"]["q50"]["mae"] == 0.01
    assert metrics["horizons"]["1"]["q50"]["source"] == "walk_forward"
    assert metrics["horizons"]["1"]["q50_mae_minus_drift20_mae"] == 0.002
    runtime.close()
    reset_runtime()


def test_metrics_q50_absent_stays_unscored(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    monkeypatch.setattr(
        "services.api.runtime.walk_forward_quantiles",
        lambda *a, **k: {"horizons": {}, "promotion_allowed": False, "origin_count": 0},
    )
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    metrics = runtime.metrics("AVAXUSDT", include_challenger=True)
    assert metrics["promotion_allowed"] is False
    assert "q50" not in metrics["horizons"]["1"]
    assert metrics["horizons"]["1"].get("q50_mae_minus_drift20_mae") is None
    runtime.close()
    reset_runtime()


def test_forecast_metrics_challenger_query(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    monkeypatch.setattr(
        "services.api.runtime.walk_forward_quantiles",
        lambda *a, **k: {
            "model_id": "freqai.quantiles.research.v1",
            "origin_count": 1,
            "promotion_allowed": False,
            "q50_mae_below_drift20_on_all_scored_horizons": False,
            "notes": "Research walk-forward only.",
            "horizons": {
                "1": {
                    "sample_count": 1,
                    "q50": {"mae": 0.04},
                    "q50_mae_minus_drift20_mae": 0.01,
                }
            },
        },
    )
    from services.api.main import app

    client = TestClient(app)
    off = client.get("/api/v1/forecast/metrics", params={"symbol": "AVAXUSDT"})
    assert off.status_code == 200
    assert "q50" not in (off.json().get("horizons") or {}).get("1", {})
    on = client.get("/api/v1/forecast/metrics", params={"symbol": "AVAXUSDT", "challenger": True})
    assert on.status_code == 200
    body = on.json()
    assert body["promotion_allowed"] is False
    assert body["horizons"]["1"]["q50"]["mae"] == 0.04
    reset_runtime()
