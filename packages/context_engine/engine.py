from __future__ import annotations

from dataclasses import replace

from .indicators import atr, ema, realized_volatility, rsi
from .models import Candle, MarketSnapshot, TimeframeState
from .resample import resample_closed
from .structure import cluster_zones, confirmed_pivots, swing_state

TIMEFRAMES: dict[str, int] = {"5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440, "1w": 10080}


class ContextEngine:
    def build_snapshot(
        self,
        candles_5m: list[Candle],
        *,
        as_of=None,
        cross_market: dict | None = None,
    ) -> MarketSnapshot:
        closed = [c for c in candles_5m if c.is_closed]
        if as_of is not None:
            closed = [c for c in closed if c.close_time() <= as_of]
        if not closed:
            raise ValueError("Need at least one closed candle")
        symbol = closed[-1].symbol
        states: dict[str, TimeframeState] = {}
        for tf, minutes in TIMEFRAMES.items():
            candles = closed if tf == "5m" else resample_closed(closed, minutes, tf)
            if candles:
                states[tf] = self._state_for(candles, tf)
        states = self._apply_parent_context(states)
        parent = next((states[tf].regime for tf in ("1w", "1d", "4h", "1h") if tf in states and states[tf].regime in {"bullish", "bearish"}), "unknown")
        child = states.get("5m")
        opposite = {
            "bullish": {"bearish", "transition_down"},
            "bearish": {"bullish", "transition_up"},
        }
        interpretation = ""
        if child and parent in opposite and child.regime in opposite[parent]:
            interpretation = f"5m {child.regime} is relief/countertrend inside {parent} higher-timeframe regime, not a reversal"
        elif parent in {"bullish", "bearish"}:
            interpretation = f"higher-timeframe regime {parent}; 5m must not silently overwrite it"
        return MarketSnapshot(
            symbol=symbol,
            as_of=closed[-1].close_time(),
            timeframes=states,
            cross_market=cross_market or {},
            interpretation=interpretation,
        )

    def _state_for(self, candles: list[Candle], timeframe: str) -> TimeframeState:
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        ema20s, ema50s, ema200s = ema(closes, 20), ema(closes, 50), ema(closes, 200)
        rsis = rsi(closes, 14)
        atrs = atr(highs, lows, closes, 14)
        pivots = confirmed_pivots(candles, 3, 3) if len(candles) >= 7 else []
        swing = swing_state(pivots)
        close = closes[-1]
        e20, e50, e200 = ema20s[-1], ema50s[-1], ema200s[-1]
        evidence: list[str] = []
        bull = bear = 0
        if close > e20 > e50:
            bull += 2; evidence.append("close_above_fast_emas")
        if close < e20 < e50:
            bear += 2; evidence.append("close_below_fast_emas")
        if e20 > e50 > e200:
            bull += 1; evidence.append("bullish_ema_order")
        if e20 < e50 < e200:
            bear += 1; evidence.append("bearish_ema_order")
        if swing == "HH_HL":
            bull += 2; evidence.append("higher_high_higher_low")
        elif swing == "LH_LL":
            bear += 2; evidence.append("lower_high_lower_low")
        regime = "bullish" if bull >= bear + 2 else "bearish" if bear >= bull + 2 else "neutral"
        vol = realized_volatility(closes, 24)
        volatility = "unknown"
        if vol is not None:
            recent = [abs(closes[i]/closes[i-1]-1.0) for i in range(max(1,len(closes)-24),len(closes))]
            baseline = sum(recent)/len(recent) if recent else 0.0
            volatility = "expanded" if vol > baseline*1.5 else "compressed" if vol < baseline*0.75 else "normal"
        zones = cluster_zones(pivots, close)
        supports = tuple(z for z in zones if z.role in {"support","mixed"} and z.upper <= close*1.01)
        resistances = tuple(z for z in zones if z.role in {"resistance","mixed"} and z.lower >= close*0.99)
        return TimeframeState(timeframe=timeframe,as_of=candles[-1].close_time(),close=close,regime=regime,swing_state=swing,volatility=volatility,ema20=e20,ema50=e50,ema200=e200,rsi14=rsis[-1],atr14=atrs[-1],support_zones=supports[-5:],resistance_zones=resistances[:5],evidence=tuple(evidence))

    def _apply_parent_context(self, states: dict[str, TimeframeState]) -> dict[str, TimeframeState]:
        order = ["1w", "1d", "4h", "1h", "15m", "5m"]
        out = dict(states)
        parent_regime: str | None = None
        for tf in order:
            state = out.get(tf)
            if state is None:
                continue
            evidence = list(state.evidence)
            regime = state.regime
            if parent_regime in {"bullish", "bearish"} and regime not in {parent_regime, "neutral"}:
                evidence.append(f"countertrend_to_parent_{parent_regime}")
            if regime == "neutral" and parent_regime in {"bullish", "bearish"}:
                regime = "transition_up" if parent_regime == "bullish" else "transition_down"
                evidence.append("neutral_child_inherits_transition_bias")
            out[tf] = replace(state, regime=regime, evidence=tuple(evidence))
            if tf in {"1w", "1d", "4h", "1h"} and state.regime in {"bullish", "bearish"}:
                parent_regime = state.regime
        return out
