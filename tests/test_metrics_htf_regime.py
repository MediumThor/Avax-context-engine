"""HTF-gated drift vs drift20 is opt-in on metrics and never a promotion."""

from fastapi.testclient import TestClient

from services.api.runtime import PrototypeRuntime, reset_runtime


def _fake_q50():
    return {"horizons": {}, "promotion_allowed": False, "origin_count": 0}


def _fake_htf(*, promotion_allowed: bool = True):
    return {
        "model_id": "baseline.htf_regime_drift.v1",
        "origin_count": 5,
        "promotion_allowed": promotion_allowed,
        "htf_mae_below_drift20_on_all_scored_horizons": True,
        "notes": "Research walk-forward only.",
        "horizons": {
            "1": {
                "sample_count": 5,
                "htf_regime": {"mae": 0.000010, "rmse": 0.000012},
                "htf_mae_minus_drift20_mae": -0.000010,
            }
        },
    }


def test_metrics_attaches_htf_without_promotion(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    monkeypatch.setattr("services.api.runtime.walk_forward_quantiles", lambda *a, **k: _fake_q50())
    monkeypatch.setattr("services.api.runtime.walk_forward_htf_regime", lambda *a, **k: _fake_htf())
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    plain = runtime.metrics("AVAXUSDT")
    assert "htf_regime" not in plain["horizons"]["1"]
    assert plain["horizons"]["1"].get("htf_mae_minus_drift20_mae") is None
    assert "htf_regime" not in plain.get("challenger", {})
    assert plain["promotion_allowed"] is False

    metrics = runtime.metrics("AVAXUSDT", include_challenger=True)
    assert metrics["promotion_allowed"] is False
    assert metrics["challenger"]["promotion_allowed"] is False
    assert metrics["challenger"]["htf_regime"]["id"] == "baseline.htf_regime_drift.v1"
    assert metrics["challenger"]["htf_regime"]["model_id"] == "baseline.htf_regime_drift.v1"
    assert metrics["challenger"]["htf_regime"]["promotion_allowed"] is False
    assert metrics["challenger"]["htf_regime"]["origin_count"] == 5
    assert metrics["horizons"]["1"]["htf_regime"]["mae"] == 0.000010
    assert metrics["horizons"]["1"]["htf_regime"]["source"] == "walk_forward"
    assert metrics["horizons"]["1"]["htf_regime"]["sample_count"] == 5
    assert metrics["horizons"]["1"]["htf_mae_minus_drift20_mae"] == -0.000010
    runtime.close()
    reset_runtime()


def test_metrics_omit_htf_when_challenger_off(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    called = {"htf": 0}

    def boom(*_a, **_k):
        called["htf"] += 1
        raise AssertionError("walk_forward_htf_regime must not run when challenger is off")

    monkeypatch.setattr("services.api.runtime.walk_forward_htf_regime", boom)
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    payload = runtime.metrics("AVAXUSDT", include_challenger=False)
    assert payload["promotion_allowed"] is False
    assert "htf_regime" not in payload.get("challenger", {})
    assert payload["horizons"]["1"].get("htf_regime") is None
    assert called["htf"] == 0
    runtime.close()
    reset_runtime()


def test_forecast_metrics_challenger_query_includes_htf(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    monkeypatch.setattr("services.api.runtime.walk_forward_quantiles", lambda *a, **k: _fake_q50())
    monkeypatch.setattr("services.api.runtime.walk_forward_htf_regime", lambda *a, **k: _fake_htf())
    from services.api.main import app

    client = TestClient(app)
    off = client.get("/api/v1/forecast/metrics", params={"symbol": "AVAXUSDT"})
    assert off.status_code == 200
    assert "htf_regime" not in (off.json().get("horizons") or {}).get("1", {})
    on = client.get("/api/v1/forecast/metrics", params={"symbol": "AVAXUSDT", "challenger": True})
    assert on.status_code == 200
    body = on.json()
    assert body["promotion_allowed"] is False
    assert body["horizons"]["1"]["htf_regime"]["mae"] == 0.000010
    assert body["challenger"]["htf_regime"]["promotion_allowed"] is False
    reset_runtime()
