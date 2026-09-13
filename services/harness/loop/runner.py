"""Deterministic loop runner: ENCODE_CHECK → … → HALT → JOURNAL."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from packages.harness.kill_switch import assert_not_severed

from services.harness.hashing import content_hash, sha256_digest
from services.harness.loop.challenge.critic import InvalidationMoveAttempt, challenge_and_invalidation
from services.harness.loop.state import empty_state, quote_forecast
from services.harness.loop.step import HARNESS_VERSION, loop_step
from services.harness.memory.swa import SlidingWindow, merge_query
from services.harness.encoder.tools import EncoderTools, ToolRefusal

DEFAULT_MAX_DEPTH = 8
DEFAULT_WINDOW_W = 16


def _halt(
    *,
    reason: str,
    depth_used: int,
    max_depth: int,
    window_w: int,
    citations: list[str],
    degraded: bool,
) -> dict[str, Any]:
    return {
        "halted": True,
        "reason": reason,
        "depth_used": depth_used,
        "max_depth": max_depth,
        "window_w": window_w,
        "budget_remaining": max(0, max_depth - depth_used),
        "citations": citations,
        "degraded": degraded,
    }


def _material_5m_change(memory: Mapping[str, Any]) -> bool:
    slices = memory.get("timeframe_slices") or {}
    parent = None
    for name in ("1d", "4h", "1h"):
        regime = (slices.get(name) or {}).get("regime")
        if regime in {"bullish", "bearish"}:
            parent = regime
            break
    child = (slices.get("5m") or {}).get("regime")
    if parent is None:
        return child not in {None, "unknown", "neutral"}
    if child in {None, "unknown", "neutral", "transition_up", "transition_down"}:
        return False
    return child == parent


def run_loop(
    *,
    memory: Mapping[str, Any],
    forecast: Mapping[str, Any],
    tools: EncoderTools | None = None,
    hypotheses: list[Mapping[str, Any]] | None = None,
    warm_start: Mapping[str, Any] | None = None,
    max_depth: int = DEFAULT_MAX_DEPTH,
    window_w: int = DEFAULT_WINDOW_W,
    commit_sha: str = "local",
    attempted_invalidation_edit: Mapping[str, Any] | None = None,
    directional: bool | None = None,
    journaled_at: str | None = None,
) -> dict[str, Any]:
    """Run one LoopTrace at memory.as_of. Kill switch aborts before the first step."""
    assert_not_severed()
    if warm_start and warm_start.get("outcomes_matured_after"):
        raise ToolRefusal("warm_start_future_outcomes", name="loop.warm_start", as_of=memory["as_of"])

    tools = tools or EncoderTools(memory, forecast=forecast)
    swa = SlidingWindow(window_w)
    state = empty_state(forecast_package_id=str(forecast.get("id") or memory["forecast_package_id"]))
    if warm_start and warm_start.get("state"):
        scratch = deepcopy(warm_start["state"])
        scratch["citations"] = list(scratch.get("citations") or []) + ["warm_start_scratch_not_evidence"]
        state["open_questions"] = list(scratch.get("open_questions") or [])
    steps: list[dict[str, Any]] = []
    citations = [memory["context_snapshot_id"], memory["id"]]
    health = memory.get("health", "unknown")
    degraded = health in {"stale", "unknown", "degraded"}
    is_directional = directional if directional is not None else _material_5m_change(memory)

    def emit_step(kind: str, **kwargs: Any) -> dict[str, Any]:
        step = loop_step(
            t=len(steps) + 1,
            kind=kind,
            memory=memory,
            state_in=state,
            swa=swa,
            tools=tools,
            **kwargs,
        )
        steps.append(step)
        state["step_index"] = step["t"]
        return step

    emit_step("ENCODE_CHECK", emit={"encoder_memory_hash": memory["content_hash"]})
    if len(steps) >= max_depth:
        halt = _halt(
            reason="max_depth",
            depth_used=len(steps),
            max_depth=max_depth,
            window_w=window_w,
            citations=citations,
            degraded=degraded,
        )
        emit_step("HALT", emit=halt)
        return _trace(memory, forecast, state, steps, halt, commit_sha, journaled_at)

    retrieve_hashes: list[str] = []
    for tool_name in ("market.get_snapshot", "system.get_health", "forecast.get_current"):
        record = tools.call(tool_name, {"as_of": memory["as_of"]})
        retrieve_hashes.append(record["response_hash"])
    emit_step("RETRIEVE", emit={"tool_response_hashes": retrieve_hashes})
    if len(steps) >= max_depth:
        halt = _halt(
            reason="max_depth",
            depth_used=len(steps),
            max_depth=max_depth,
            window_w=window_w,
            citations=citations,
            degraded=degraded,
        )
        emit_step("HALT", emit=halt)
        return _trace(memory, forecast, state, steps, halt, commit_sha, journaled_at)

    state.update(quote_forecast(state, forecast))
    slices = memory.get("timeframe_slices") or {}
    state["regime_reading"] = {tf: (slices.get(tf) or {}).get("regime") for tf in ("1d", "4h", "1h", "15m", "5m")}
    state["data_health"] = {"health": health}
    merge = merge_query("fact", encoder_memory=memory, swa=swa, state=state)
    state["contradictions"] = list(state.get("contradictions") or []) + list(merge["contradictions"])

    if health in {"stale", "unknown"}:
        state["what_did_not_change"] = ["forecast_claims_suppressed_stale_or_unknown"]
        state["confidence_source"] = "insufficient-data"
        emit_step("SYNTHESIZE", emit={"health": health})
        halt = _halt(
            reason="stale_or_unknown_data",
            depth_used=len(steps),
            max_depth=max_depth,
            window_w=window_w,
            citations=citations,
            degraded=True,
        )
        emit_step("HALT", emit=halt)
        emit_step("JOURNAL", emit={"trace_pending": True})
        return _trace(memory, forecast, state, steps, halt, commit_sha, journaled_at)

    if not is_directional:
        state["what_changed"] = []
        state["what_did_not_change"] = ["higher_timeframe_regime", "active_invalidations"]
        emit_step("SYNTHESIZE", emit={"no_change": True})
        emit_step("NO_CHANGE", emit={"reason": "immaterial_5m"})
        halt = _halt(
            reason="no_change",
            depth_used=len(steps),
            max_depth=max_depth,
            window_w=window_w,
            citations=citations,
            degraded=False,
        )
        emit_step("HALT", emit=halt)
        emit_step("JOURNAL", emit={"trace_pending": True})
        return _trace(memory, forecast, state, steps, halt, commit_sha, journaled_at)

    emit_step("SYNTHESIZE", emit={"directional": True})
    try:
        challenged = challenge_and_invalidation(
            state,
            memory,
            hypotheses=hypotheses,
            attempted_invalidation_edit=attempted_invalidation_edit,
        )
    except InvalidationMoveAttempt:
        halt = _halt(
            reason="invalidation_move_attempt",
            depth_used=len(steps) + 1,
            max_depth=max_depth,
            window_w=window_w,
            citations=citations,
            degraded=True,
        )
        emit_step("CHALLENGE", emit={"error": "invalidation_move_attempt"})
        emit_step("HALT", emit=halt)
        emit_step("JOURNAL", emit={"trace_pending": True})
        return _trace(memory, forecast, state, steps, halt, commit_sha, journaled_at)

    state.clear()
    state.update(challenged["state"])
    emit_step("CHALLENGE", emit=challenged["emit"])
    emit_step("INVALIDATION_CHECK", emit=state["invalidation"])
    if forecast:
        emit_step(
            "FORECAST_REFINE",
            emit={"quoted_fields": state["forecast_summary"]["quoted_fields"]},
        )
    halt = _halt(
        reason="challenge_complete",
        depth_used=len(steps),
        max_depth=max_depth,
        window_w=window_w,
        citations=citations,
        degraded=False,
    )
    emit_step("HALT", emit=halt)
    emit_step("JOURNAL", emit={"trace_pending": True})
    return _trace(memory, forecast, state, steps, halt, commit_sha, journaled_at)


def replay_loop(trace: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Exact replay: same function, same inputs, compare content_hash."""
    rebuilt = run_loop(**kwargs)
    if rebuilt["content_hash"] != trace["content_hash"]:
        raise ValueError("exact_replay_mismatch")
    return rebuilt


def _trace(
    memory: Mapping[str, Any],
    forecast: Mapping[str, Any],
    state: Mapping[str, Any],
    steps: list[dict[str, Any]],
    halt: Mapping[str, Any],
    commit_sha: str,
    journaled_at: str | None,
) -> dict[str, Any]:
    payload = {
        "id": f"loop-{sha256_digest(memory['id'] + memory['as_of'] + HARNESS_VERSION)[7:19]}",
        "schema_version": "1",
        "symbol": memory["symbol"],
        "as_of": memory["as_of"],
        "encoder_memory_id": memory["id"],
        "encoder_memory_hash": memory["content_hash"],
        "context_snapshot_id": memory["context_snapshot_id"],
        "forecast_package_id": str(forecast.get("id") or memory["forecast_package_id"]),
        "harness_version": HARNESS_VERSION,
        "tool_schema_version": "1",
        "commit_sha": commit_sha,
        "warm_start_from_trace_id": None,
        "steps": steps,
        "final_state": dict(state),
        "halt": dict(halt),
        "journaled_at": journaled_at or memory["as_of"],
    }
    payload["content_hash"] = content_hash(payload)
    return payload

