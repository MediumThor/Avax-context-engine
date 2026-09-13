from __future__ import annotations

import math
from statistics import mean

from packages.context_engine.models import Candle
from packages.evaluator.metrics import direction_accuracy, mae, rmse


def _future_returns(closes: list[float], h: int) -> list[float]:
    return [math.log(closes[i+h]/closes[i]) for i in range(len(closes)-h)]


def evaluate_baselines(candles: list[Candle], horizons: int = 10) -> dict:
    if len(candles) < 300:
        raise ValueError("At least 300 candles required")
    closes=[c.close for c in candles]
    results={}
    for h in range(1,horizons+1):
        actual=_future_returns(closes,h)
        # Only compare timestamps where a 20-candle trailing drift is available.
        actual=actual[20:]
        zero=[0.0]*len(actual)
        drift=[]
        for i in range(20,len(closes)-h):
            past=[math.log(closes[j]/closes[j-1]) for j in range(i-19,i+1)]
            drift.append(mean(past)*h)
        results[str(h)]={
            "zero":{"mae":mae(actual,zero),"rmse":rmse(actual,zero),"direction_accuracy":direction_accuracy(actual,zero)},
            "drift20":{"mae":mae(actual,drift),"rmse":rmse(actual,drift),"direction_accuracy":direction_accuracy(actual,drift)},
            "sample_count":len(actual)
        }
    return results
