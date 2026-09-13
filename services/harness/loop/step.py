"""Single D_φ LoopStep used for both ingest and emit tokens."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from services.harness.encoder.tools import EncoderTools, ToolRefusal
from services.harness.hashing import sha256_digest
from services.harness.loop.state import state_hash
from services.harness.memory.swa import SlidingWindow

HARNESS_VERSION = "rlh-0.1.0"

ChallengeFn = Callable[[dict[str, Any], Mapping[str, Any]], dict[str, Any]]


def loop_step(
    *,
    t: int,
    kind: str,
    memory: Mapping[str, Any],
    state_in: Mapping[str, Any],
    swa: SlidingWindow,
    tools: EncoderTools | None = None,
    tool_name: str | None = None,
    tool_request: Mapping[str, Any] | None = None,
    emit: Mapping[str, Any] | None = None,
    citations: list[str] | None = None,
    input_token: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """One versioned transition. Live and replay share this function."""
    swa_in = swa.content_hash()
    state_in_hash = state_hash(state_in)
    tool_record: dict[str, Any] | None = None
    if tool_name:
        assert tools is not None
        request = dict(tool_request or {})
        request.setdefault("as_of", memory["as_of"])
        try:
            tool_record = tools.call(tool_name, request)
        except ToolRefusal as exc:
            tool_record = tools.refuse_record(tool_name, request, exc.reason)
    step = {
        "t": t,
        "kind": kind,
        "harness_version": HARNESS_VERSION,
        "input_token_hash": sha256_digest(input_token or {"t": t, "kind": kind}),
        "encoder_memory_hash": memory["content_hash"],
        "state_in_hash": state_in_hash,
        "state_out_hash": state_hash(state_in),
        "swa_in_hash": swa_in,
        "swa_out_hash": swa_in,
        "tool": _tool_view(tool_record),
        "emit": dict(emit) if emit is not None else None,
        "citations": list(citations or [memory.get("context_snapshot_id") or memory["id"]]),
        "exact": True,
        "latency_ms": 0,
    }
    swa.append({"t": t, "kind": kind, "emit_hash": sha256_digest(step.get("emit")), "exact": True})
    step["swa_out_hash"] = swa.content_hash()
    return step


def _tool_view(record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "name": record["name"],
        "request": record.get("request") or {},
        "response_hash": record.get("response_hash"),
        "as_of": record["as_of"],
        "refused": bool(record.get("refused")),
        "refusal_reason": record.get("refusal_reason"),
    }
