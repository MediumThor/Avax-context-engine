"""Read-only EncoderMemory tools. Missing as_of or future known_at is a refusal."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from services.harness.hashing import sha256_digest


class ToolRefusal(Exception):
    def __init__(self, reason: str, *, name: str, as_of: str | None = None):
        super().__init__(reason)
        self.reason = reason
        self.name = name
        self.as_of = as_of


def _iso(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        return value.isoformat().replace("+00:00", "Z")
    return value


class EncoderTools:
    """Deterministic tool surface used by LoopStep."""

    def __init__(
        self,
        memory: Mapping[str, Any],
        *,
        snapshot: Mapping[str, Any] | None = None,
        forecast: Mapping[str, Any] | None = None,
        analogs: list[Mapping[str, Any]] | None = None,
        hypotheses: list[Mapping[str, Any]] | None = None,
        zones: list[Mapping[str, Any]] | None = None,
    ) -> None:
        self.memory = {key: value for key, value in dict(memory).items() if not str(key).startswith("_")}
        self.snapshot = dict(snapshot or {})
        self.forecast = dict(forecast or {})
        self.analogs = list(analogs or [])
        self.hypotheses = list(hypotheses or [])
        self.zones = list(zones or [])

    def call(self, name: str, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        as_of = _iso(request.get("as_of"))
        if as_of is None:
            raise ToolRefusal("missing_as_of", name=name)
        if as_of != self.memory["as_of"]:
            raise ToolRefusal("as_of_mismatch", name=name, as_of=as_of)
        try:
            response = self._dispatch(name, request, as_of)
        except ToolRefusal:
            raise
        return {
            "name": name,
            "request": request,
            "response": response,
            "response_hash": sha256_digest(response),
            "as_of": as_of,
            "refused": False,
            "refusal_reason": None,
        }

    def refuse_record(self, name: str, request: Mapping[str, Any] | None, reason: str) -> dict[str, Any]:
        request = dict(request or {})
        return {
            "name": name,
            "request": request,
            "response_hash": None,
            "as_of": _iso(request.get("as_of")) or self.memory["as_of"],
            "refused": True,
            "refusal_reason": reason,
        }

    def _dispatch(self, name: str, request: Mapping[str, Any], as_of: str) -> Any:
        if name == "market.get_snapshot":
            return {"memory": self.memory, "snapshot": self.snapshot}
        if name == "market.get_series":
            return {"as_of": as_of, "symbol": self.memory["symbol"]}
        if name == "context.get_zones":
            return self._filter_known(
                self.zones or [{"id": z} for z in self.memory.get("zone_ids", [])], as_of, name
            )
        if name == "context.get_structure":
            return {"timeframe_slices": self.memory["timeframe_slices"]}
        if name == "context.get_hypotheses":
            return self._filter_known(
                self.hypotheses or [{"id": h} for h in self.memory.get("hypothesis_ids", [])],
                as_of,
                name,
            )
        if name == "forecast.get_current":
            return {"forecast": self.forecast, "forecast_package_id": self.memory["forecast_package_id"]}
        if name == "forecast.get_history":
            return self._filter_known(request.get("history") or [], as_of, name)
        if name == "evaluation.get_metrics":
            return self._filter_metrics(request.get("metrics") or {}, as_of)
        if name == "analog.search":
            return self._filter_known(self.analogs, as_of, name)
        if name == "system.get_health":
            return {"health": self.memory["health"], "as_of": as_of}
        if name == "loop.get_state":
            return request.get("state") or {}
        if name == "loop.cite":
            return {"citations": list(request.get("citations") or [])}
        if name == "loop.halt":
            return request.get("halt") or {}
        raise ToolRefusal("unknown_tool", name=name, as_of=as_of)

    def _filter_known(
        self, items: list[Mapping[str, Any]], as_of: str, tool_name: str
    ) -> list[Mapping[str, Any]]:
        kept: list[Mapping[str, Any]] = []
        for item in items:
            known_at = _iso(item.get("known_at") or item.get("as_of") or as_of)
            if known_at and known_at > as_of:
                raise ToolRefusal("future_data", name=tool_name, as_of=as_of)
            kept.append(dict(item))
        return kept

    def _filter_metrics(self, metrics: Mapping[str, Any], as_of: str) -> Mapping[str, Any]:
        matured_at = _iso(metrics.get("matured_at") or as_of)
        if matured_at and matured_at > as_of:
            raise ToolRefusal("future_metrics", name="evaluation.get_metrics", as_of=as_of)
        return dict(metrics)
