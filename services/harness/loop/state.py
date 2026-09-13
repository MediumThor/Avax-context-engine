"""RecurrentState helpers for LoopStep."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from services.harness.hashing import sha256_digest

CONFIDENCE_SOURCES = {"calibrated", "model-disagreement", "insufficient-data"}


def empty_state(*, forecast_package_id: str, health: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "step_index": 0,
        "regime_reading": {},
        "what_changed": [],
        "what_did_not_change": [],
        "bull_case": {"claims": [], "citations": []},
        "bear_case": {"claims": [], "citations": []},
        "forecast_summary": {"forecast_package_id": forecast_package_id, "quoted_fields": []},
        "invalidation": {"fired": [], "intact": []},
        "data_health": dict(health or {}),
        "confidence_source": "insufficient-data",
        "open_questions": [],
        "citations": [],
        "contradictions": [],
    }


def state_hash(state: Mapping[str, Any]) -> str:
    return sha256_digest(state)


def quote_forecast(state: dict[str, Any], forecast: Mapping[str, Any]) -> dict[str, Any]:
    """Copy only fields present on the ForecastPackage. Never invent probabilities."""
    out = deepcopy(state)
    quoted: list[str] = []
    for key in ("horizons", "calibration_ref", "health", "component_models", "id"):
        if key in forecast:
            quoted.append(key)
    out["forecast_summary"] = {
        "forecast_package_id": forecast.get("id") or state["forecast_summary"]["forecast_package_id"],
        "quoted_fields": quoted,
    }
    if forecast.get("calibration_ref"):
        out["confidence_source"] = "calibrated"
    elif forecast.get("component_models") and len(forecast.get("component_models") or []) > 1:
        out["confidence_source"] = "model-disagreement"
    else:
        out["confidence_source"] = "insufficient-data"
    if out["confidence_source"] not in CONFIDENCE_SOURCES:
        raise ValueError("illegal confidence_source")
    return out


def assert_no_invented_numbers(state: Mapping[str, Any], forecast: Mapping[str, Any]) -> None:
    quoted = set(state.get("forecast_summary", {}).get("quoted_fields") or [])
    for claim in list(state.get("bull_case", {}).get("claims") or []) + list(
        state.get("bear_case", {}).get("claims") or []
    ):
        if "%" in claim and "confidence_source" not in claim:
            raise ValueError("uncalibrated_percent")
        if "p=" in claim and "horizons" not in quoted and "horizons" not in forecast:
            raise ValueError("invented_probability")
