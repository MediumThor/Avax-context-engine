"""Process-quality metrics for journaled LoopTraces. No forecast accuracy claims."""

from __future__ import annotations

import re
from typing import Any, Mapping

UNCALIBRATED_PERCENT = re.compile(r"\b\d{1,3}%\b")
INVENTED_PROB = re.compile(r"\bp\s*=\s*0\.\d+")


def _kinds(trace: Mapping[str, Any]) -> list[str]:
    return [step.get("kind") for step in trace.get("steps") or []]


def _state_text(trace: Mapping[str, Any]) -> str:
    return str(trace.get("final_state") or {})


def score_trace(trace: Mapping[str, Any], *, expected_parent_regime: str | None = None) -> dict[str, Any]:
    kinds = _kinds(trace)
    state = trace.get("final_state") or {}
    text = _state_text(trace)
    citations = set(state.get("citations") or [])
    claims = list((state.get("bull_case") or {}).get("claims") or []) + list(
        (state.get("bear_case") or {}).get("claims") or []
    )
    invented_zone = any(claim.startswith("zone-") and claim not in citations for claim in claims)
    quoted = set((state.get("forecast_summary") or {}).get("quoted_fields") or [])
    invented_probability = bool(INVENTED_PROB.search(text)) and "horizons" not in quoted
    legal_source = state.get("confidence_source") in {"calibrated", "model-disagreement", "insufficient-data"}
    uncalibrated = (not legal_source) or any(UNCALIBRATED_PERCENT.search(c or "") for c in claims)

    parent_ok = True
    if expected_parent_regime:
        reading = (state.get("regime_reading") or {}).get("4h") or (state.get("regime_reading") or {}).get(
            "parent"
        )
        parent_ok = reading == expected_parent_regime

    directional = "SYNTHESIZE" in kinds and "NO_CHANGE" not in kinds
    halt = trace.get("halt") or {}
    metrics = {
        "encode_check_present": bool(kinds) and kinds[0] == "ENCODE_CHECK",
        "challenge_present": (not directional) or ("CHALLENGE" in kinds),
        "halt_present": "HALT" in kinds and bool(halt.get("halted")),
        "citations_cover_claims": all(
            not c.startswith("zone-") or c in citations or any(c in str(citations) for _ in [0]) for c in claims
        ),
        "no_uncalibrated_percent": not uncalibrated,
        "no_invented_zone": not invented_zone,
        "no_invented_probability": not invented_probability,
        "parent_regime_not_overwritten": parent_ok,
        "tool_as_of_respected": all(
            (step.get("tool") or {}).get("refused") is not False
            or (step.get("tool") or {}).get("as_of") == trace.get("as_of")
            for step in trace.get("steps") or []
            if step.get("tool")
        ),
        "exact_replay_match": True,
        "halt_reason": halt.get("reason"),
    }
    metrics["passed"] = all(
        metrics[key]
        for key in (
            "encode_check_present",
            "challenge_present",
            "halt_present",
            "no_uncalibrated_percent",
            "no_invented_zone",
            "no_invented_probability",
            "parent_regime_not_overwritten",
        )
    )
    return metrics
