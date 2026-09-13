"""Mandatory CHALLENGE + INVALIDATION_CHECK before directional halt."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

PARENT_ORDER = ("1w", "1d", "4h", "1h")


class InvalidationMoveAttempt(Exception):
    """Raised when a loop tries to edit an active thesis invalidation."""


def _parent_regime(slices: Mapping[str, Any]) -> str | None:
    for name in PARENT_ORDER:
        regime = (slices.get(name) or {}).get("regime")
        if regime in {"bullish", "bearish"}:
            return regime
    return None


def challenge_and_invalidation(
    state: Mapping[str, Any],
    memory: Mapping[str, Any],
    *,
    hypotheses: list[Mapping[str, Any]] | None = None,
    attempted_invalidation_edit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return challenge emit + updated state. Does not invent levels or percents."""
    if attempted_invalidation_edit:
        raise InvalidationMoveAttempt("invalidation_move_attempt")

    out = deepcopy(dict(state))
    slices = memory.get("timeframe_slices") or {}
    parent = _parent_regime(slices)
    child_5m = (slices.get("5m") or {}).get("regime")
    fired = list(out.get("invalidation", {}).get("fired") or [])
    intact = list(out.get("invalidation", {}).get("intact") or [])

    opposite_claims: list[str] = []
    if parent == "bearish":
        opposite_claims.append("counter_5m_bounce_does_not_reset_parent_bear")
        if child_5m in {"bullish", "transition_up", "neutral"}:
            out.setdefault("what_did_not_change", []).append("4h_regime_still_bearish")
            out.setdefault("what_changed", [])
            if "5m_relief_or_noise" not in out["what_changed"]:
                out["what_changed"].append("5m_relief_or_noise")
    elif parent == "bullish":
        opposite_claims.append("counter_5m_dip_does_not_reset_parent_bull")

    for hyp in hypotheses or []:
        status = hyp.get("status")
        rules = list(hyp.get("invalidation_rules") or hyp.get("invalidation") or [])
        hyp_id = str(hyp.get("id", "hypothesis"))
        if status in {"closed", "invalidated"}:
            if hyp_id not in fired:
                fired.append(hyp_id)
        else:
            if hyp_id not in intact:
                intact.append(f"{hyp_id}:{','.join(str(r) for r in rules) or 'unchanged'}")

    out["invalidation"] = {"fired": fired, "intact": intact}
    if parent:
        out.setdefault("regime_reading", {})
        out["regime_reading"]["parent"] = parent
        out["regime_reading"]["4h"] = (slices.get("4h") or {}).get("regime")
        out["regime_reading"]["5m"] = child_5m
        if parent == "bearish" and out["regime_reading"].get("4h") != "bearish":
            out["contradictions"] = list(out.get("contradictions") or []) + ["parent_regime_overwrite_blocked"]
            out["regime_reading"]["4h"] = "bearish"

    citations = list(out.get("citations") or [])
    citations.append(str(memory.get("id") or memory.get("context_snapshot_id")))
    out["citations"] = citations

    opposite_case = "bull_case" if parent == "bearish" else "bear_case"
    bucket = deepcopy(out.get(opposite_case) or {"claims": [], "citations": []})
    for claim in opposite_claims:
        if claim not in bucket["claims"]:
            bucket["claims"].append(claim)
    if memory.get("id") and memory["id"] not in bucket["citations"]:
        bucket["citations"].append(memory["id"])
    out[opposite_case] = bucket

    emit = {
        "kind": "CHALLENGE",
        "parent_regime": parent,
        "relief_vs_reversal": "relief" if parent == "bearish" and child_5m != "bearish" else "aligned",
        "invalidation": out["invalidation"],
        "opposite_claims": opposite_claims,
    }
    return {"state": out, "emit": emit}
