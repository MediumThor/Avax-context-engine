from __future__ import annotations

import hashlib

from .models import Candle, Pivot, StructuralZone


def confirmed_pivots(candles: list[Candle], left: int = 3, right: int = 3) -> list[Pivot]:
    if left < 1 or right < 1:
        raise ValueError("left/right must be >= 1")
    out: list[Pivot] = []
    for i in range(left, len(candles) - right):
        hi, lo = candles[i].high, candles[i].low
        window = candles[i-left:i+right+1]
        if hi == max(c.high for c in window) and sum(c.high == hi for c in window) == 1:
            known = candles[i+right]
            out.append(Pivot(i, i+right, candles[i].open_time, known.open_time, hi, "high"))
        if lo == min(c.low for c in window) and sum(c.low == lo for c in window) == 1:
            known = candles[i+right]
            out.append(Pivot(i, i+right, candles[i].open_time, known.open_time, lo, "low"))
    return sorted(out, key=lambda p: (p.known_at_index, p.kind))


def _zone_id(lower: float, upper: float, role: str) -> str:
    return hashlib.sha1(f"{lower:.8f}:{upper:.8f}:{role}".encode()).hexdigest()[:12]


def cluster_zones(pivots: list[Pivot], current_price: float, tolerance_pct: float = 0.006) -> list[StructuralZone]:
    if not pivots:
        return []
    sorted_pivots = sorted(pivots, key=lambda p: p.price)
    clusters: list[list[Pivot]] = []
    for pivot in sorted_pivots:
        if not clusters:
            clusters.append([pivot]); continue
        center = sum(p.price for p in clusters[-1]) / len(clusters[-1])
        if abs(pivot.price-center) / max(center, 1e-12) <= tolerance_pct:
            clusters[-1].append(pivot)
        else:
            clusters.append([pivot])
    zones: list[StructuralZone] = []
    for cluster in clusters:
        prices = [p.price for p in cluster]
        lower, upper = min(prices), max(prices)
        midpoint = (lower+upper)/2.0
        role = "support" if midpoint < current_price else "resistance" if midpoint > current_price else "mixed"
        if len({p.kind for p in cluster}) > 1 and abs(midpoint-current_price)/current_price < tolerance_pct:
            role = "mixed"
        zones.append(StructuralZone(_zone_id(lower, upper, role), lower, upper, role, min(1.0, 0.2+0.15*len(cluster)), len(cluster)))
    return zones


def swing_state(pivots: list[Pivot]) -> str:
    highs = [p for p in pivots if p.kind == "high"][-2:]
    lows = [p for p in pivots if p.kind == "low"][-2:]
    if len(highs) < 2 or len(lows) < 2:
        return "insufficient"
    hh = highs[-1].price > highs[-2].price
    hl = lows[-1].price > lows[-2].price
    if hh and hl: return "HH_HL"
    if not hh and not hl: return "LH_LL"
    return "mixed"
