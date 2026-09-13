"""Score matured journal rows. Never rewrite forecasts. Never invent scores."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from packages.evaluator.calibration import expected_calibration_error
from packages.evaluator.metrics import brier_score, interval_coverage, mae, rmse
from packages.journal import ForecastJournal
from packages.models.direction_cal import CALIBRATION_REF
from packages.models.probability_walkforward import MIN_BRIER, MIN_COVERAGE, MIN_ECE, MIN_MAE

LIVE_SOURCES = frozenset({"binance-vision", "live"})


def journal_data_source(payload: dict[str, Any]) -> str:
    raw = payload.get("data_source")
    if raw in LIVE_SOURCES:
        return "live"
    if raw == "fixture":
        return "fixture"
    return "unknown"


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    return value.astimezone(timezone.utc)


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def score_journaled_forecasts(
    journal: ForecastJournal,
    symbol: str,
    *,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Score matured journal rows known at as_of. Null p does not become a Brier."""
    cutoff = _aware(as_of) if as_of is not None else None
    per_h: dict[int, dict[str, list[float]]] = {
        h: {
            "y": [],
            "p": [],
            "live_y": [],
            "live_p": [],
            "actual": [],
            "q10": [],
            "q90": [],
            "point_actual": [],
            "drift20": [],
        }
        for h in range(1, 11)
    }
    used = 0
    for row in journal.list_forecasts(symbol):
        payload = row["payload"]
        source = journal_data_source(payload)
        try:
            issued = _parse(payload["forecasted_at"])
        except (KeyError, TypeError, ValueError):
            continue
        if cutoff is not None and issued > cutoff:
            continue
        by_h = {int(item["h"]): item for item in payload.get("horizons") or [] if "h" in item}
        for outcome in journal.list_outcomes(row["id"]):
            h = int(outcome["h"])
            matured = outcome.get("matured_at")
            if cutoff is not None and matured:
                if _parse(str(matured)) > cutoff:
                    continue
            forecast_row = by_h.get(h)
            if forecast_row is None:
                continue
            p = forecast_row.get("p_close_above_origin")
            y = outcome.get("realized_close_above_origin")
            if isinstance(p, (int, float)) and y is not None:
                per_h[h]["p"].append(float(p))
                per_h[h]["y"].append(1.0 if y else 0.0)
                if source == "live":
                    per_h[h]["live_p"].append(float(p))
                    per_h[h]["live_y"].append(1.0 if y else 0.0)
            q10 = forecast_row.get("q10_cum_log_return")
            q90 = forecast_row.get("q90_cum_log_return")
            actual = outcome.get("realized_cum_log_return")
            if isinstance(q10, (int, float)) and isinstance(q90, (int, float)) and isinstance(actual, (int, float)):
                per_h[h]["q10"].append(float(q10))
                per_h[h]["q90"].append(float(q90))
                per_h[h]["actual"].append(float(actual))
            pred = forecast_row.get("drift20_cum_log_return")
            if pred is None:
                pred = forecast_row.get("expected_cum_log_return")
            if isinstance(pred, (int, float)) and isinstance(actual, (int, float)):
                per_h[h]["point_actual"].append(float(actual))
                per_h[h]["drift20"].append(float(pred))
            used += 1

    horizons_out: dict[str, Any] = {}
    for h, series in per_h.items():
        n_p = len(series["p"])
        n_live = len(series["live_p"])
        n_iv = len(series["actual"])
        n_pt = len(series["point_actual"])
        scored = n_pt >= MIN_MAE
        zeros = [0.0] * n_pt
        horizons_out[str(h)] = {
            "probability": {
                "sample_count": n_p,
                "brier": brier_score(series["y"], series["p"]) if n_p >= MIN_BRIER else None,
                "ece": expected_calibration_error(series["y"], series["p"], bins=5) if n_p >= MIN_ECE else None,
                "calibration_ref": CALIBRATION_REF,
            },
            "probability_held_out_live": {
                "sample_count": n_live,
                "brier": brier_score(series["live_y"], series["live_p"]) if n_live >= MIN_BRIER else None,
                "ece": expected_calibration_error(series["live_y"], series["live_p"], bins=5)
                if n_live >= MIN_ECE
                else None,
                "calibration_ref": CALIBRATION_REF,
                "source": "journal_live",
                "note": "Fixture and untagged rows are excluded. Missing stays not yet scored.",
            },
            "interval": {
                "sample_count": n_iv,
                "coverage": interval_coverage(series["actual"], series["q10"], series["q90"])
                if n_iv >= MIN_COVERAGE
                else None,
            },
            "zero": {
                "sample_count": n_pt,
                "mae": mae(series["point_actual"], zeros) if scored else None,
                "rmse": rmse(series["point_actual"], zeros) if scored else None,
            },
            "drift20": {
                "sample_count": n_pt,
                "mae": mae(series["point_actual"], series["drift20"]) if scored else None,
                "rmse": rmse(series["point_actual"], series["drift20"]) if scored else None,
            },
        }
    return {
        "validation": "journaled_walk_forward",
        "forecasts_used": used,
        "promotion_allowed": False,
        "horizons": horizons_out,
    }
