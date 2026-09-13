"""Deterministic thesis rebuild for a snapshot as_of.

Walks closed higher-timeframe bars in time order. Invalidation is frozen at
open. A 5m observation cannot fire a 4h rule. Re-opening after a close is a
new version, not a moved price on the dead version.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from .models import Candle, TimeframeState
from .resample import resample_closed
from .structure import confirmed_pivots
from .thesis import PriceObservation, Thesis, ThesisLedger

RELIEF_REGIMES = {"bullish", "transition_up"}


def _structure_extreme(candles: list[Candle], kind: str) -> float:
    pivots = confirmed_pivots(candles, 3, 3) if len(candles) >= 7 else []
    prices = [p.price for p in pivots if p.kind == kind]
    if prices:
        return max(prices) if kind == "high" else min(prices)
    if kind == "high":
        return max(c.high for c in candles)
    return min(c.low for c in candles)


def _summarize(thesis: Thesis, *, regime_relation: str, timeframe: str) -> dict[str, Any]:
    return {
        "id": thesis.id,
        "lineage_id": thesis.lineage_id,
        "symbol": thesis.symbol,
        "direction": thesis.direction,
        "kind": thesis.kind,
        "status": thesis.status,
        "version": thesis.version,
        "timeframe": timeframe,
        "regime_relation": regime_relation,
        "created_at": thesis.created_at.isoformat(),
        "closed_at": thesis.closed_at.isoformat() if thesis.closed_at else None,
        "closure_reason": thesis.closure_reason,
        "evidence": [item.text for item in thesis.evidence],
        "counter_evidence": [item.text for item in thesis.counter_evidence],
        "confirmation_rules": [rule.to_dict() for rule in thesis.confirmation_rules],
        "invalidation_rules": [rule.to_dict() for rule in thesis.invalidation_rules],
        "invalidation_fingerprint": thesis.invalidation_fingerprint,
        "fired_rule_ids": list(thesis.fired_rule_ids),
        "note": "Invalidation frozen at open. Not a confidence score.",
    }


def _open_htf(
    ledger: ThesisLedger,
    *,
    symbol: str,
    direction: str,
    kind: str,
    version: int,
    created_at: datetime,
    bars: list[Candle],
    timeframe: str,
    evidence: list[str],
    counter: list[str],
) -> Thesis:
    high = _structure_extreme(bars, "high")
    low = _structure_extreme(bars, "low")
    if high <= low:
        high = low * 1.002
    if direction == "bear":
        confirm_kind, confirm_price = "close_below", low
        invalid_kind, invalid_price = "close_above", high
        confirm_desc = f"{timeframe} acceptance below structure low {low:.4f}"
        invalid_desc = f"{timeframe} reclaim of structure high {high:.4f}"
    else:
        confirm_kind, confirm_price = "close_above", high
        invalid_kind, invalid_price = "close_below", low
        confirm_desc = f"{timeframe} acceptance above structure high {high:.4f}"
        invalid_desc = f"{timeframe} loss of structure low {low:.4f}"
    lineage = f"{symbol}:{timeframe}:{direction}:{kind}"
    return ledger.open(
        symbol=symbol,
        direction=direction,  # type: ignore[arg-type]
        kind=kind,
        created_at=created_at,
        thesis_id=f"{lineage}:v{version}",
        lineage_id=lineage,
        version=version,
        evidence=evidence,
        counter_evidence=counter,
        confirmation_rules=[
            {
                "id": f"{direction}-confirm-{timeframe}",
                "kind": confirm_kind,
                "price": confirm_price,
                "timeframe": timeframe,
                "description": confirm_desc,
            }
        ],
        invalidation_rules=[
            {
                "id": f"{direction}-invalidate-{timeframe}",
                "kind": invalid_kind,
                "price": invalid_price,
                "timeframe": timeframe,
                "description": invalid_desc,
            }
        ],
    )


def build_snapshot_theses(
    closed_5m: list[Candle],
    *,
    as_of: datetime,
    state_for: Callable[[list[Candle], str], TimeframeState],
    parent_regime: str,
    child_regime: str | None,
) -> tuple[dict[str, Any], ...]:
    """Rebuild competing theses knowable at as_of. Empty when history is too short."""
    visible = [c for c in closed_5m if c.is_closed and c.close_time() <= as_of]
    if len(visible) < 48:
        return ()
    symbol = visible[-1].symbol
    bars_4h = resample_closed(visible, 240, "4h")
    if len(bars_4h) < 7:
        return ()
    ledger = ThesisLedger()
    active: dict[str, str] = {}
    versions = {"bear": 0, "bull": 0}
    for index, bar in enumerate(bars_4h):
        prefix = bars_4h[: index + 1]
        regime = state_for(prefix, "4h").regime
        obs = PriceObservation(
            at=bar.close_time(),
            timeframe="4h",
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
        )
        for direction, thesis_id in list(active.items()):
            live = ledger.fire(thesis_id, obs, at=bar.close_time())
            if live.status == "closed":
                del active[direction]
        want = "bear" if regime == "bearish" else "bull" if regime == "bullish" else None
        if want and want not in active:
            versions[want] += 1
            opened = _open_htf(
                ledger,
                symbol=symbol,
                direction=want,
                kind="htf_continuation" if versions[want] == 1 else "htf_continuation_reopened",
                version=versions[want],
                created_at=bar.close_time(),
                bars=prefix,
                timeframe="4h",
                evidence=[f"4h regime {regime} at {bar.close_time().isoformat()}"],
                counter=["competing thesis and lower-timeframe bounce risk"],
            )
            active[want] = opened.id

    out: list[dict[str, Any]] = []
    for direction in ("bear", "bull"):
        thesis_id = active.get(direction)
        thesis = ledger.get(thesis_id) if thesis_id else None
        if thesis is None:
            prior = [t for t in ledger.all() if t.direction == direction]
            thesis = prior[-1] if prior else None
        if thesis is None:
            continue
        aligned = parent_regime == ("bearish" if thesis.direction == "bear" else "bullish")
        out.append(_summarize(thesis, regime_relation="aligned" if aligned else "mixed", timeframe="4h"))

    bear_live = ledger.get(active["bear"]) if "bear" in active else None
    if (
        bear_live is not None
        and bear_live.status == "active"
        and child_regime in RELIEF_REGIMES
    ):
        tail = visible[-48:]
        first_idx = None
        for offset, bar in enumerate(tail):
            prefix = visible[: len(visible) - len(tail) + offset + 1]
            if len(prefix) < 21:
                continue
            if state_for(prefix, "5m").regime in RELIEF_REGIMES:
                first_idx = offset
                break
        if first_idx is None:
            first_idx = len(tail) - 1
        open_bar = tail[first_idx]
        prefix_at_open = visible[: len(visible) - len(tail) + first_idx + 1]
        relief = _open_htf(
            ledger,
            symbol=symbol,
            direction="bull",
            kind="ltf_relief",
            version=1,
            created_at=open_bar.close_time(),
            bars=prefix_at_open[-24:] if len(prefix_at_open) >= 24 else prefix_at_open,
            timeframe="5m",
            evidence=["5m countertrend inside a bearish 4h regime"],
            counter=["4h invalidation has not fired"],
        )
        for bar in tail[first_idx:]:
            ledger.fire(
                relief.id,
                PriceObservation(
                    at=bar.close_time(),
                    timeframe="5m",
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                ),
                at=bar.close_time(),
            )
            # 5m wick through the 4h reclaim price must not close the HTF thesis.
            if "bear" in active:
                ledger.fire(
                    active["bear"],
                    PriceObservation(
                        at=bar.close_time(),
                        timeframe="5m",
                        open=bar.open,
                        high=bar.high,
                        low=bar.low,
                        close=bar.close,
                    ),
                    at=bar.close_time(),
                )
        out.append(_summarize(ledger.get(relief.id), regime_relation="countertrend", timeframe="5m"))
        bear_after = ledger.get(active["bear"]) if "bear" in active else bear_live
        for i, row in enumerate(out):
            if row["direction"] == "bear" and row["timeframe"] == "4h":
                out[i] = _summarize(bear_after, regime_relation="aligned", timeframe="4h")
                break

    return tuple(out)
