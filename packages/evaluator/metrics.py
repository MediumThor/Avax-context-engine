from __future__ import annotations

from math import sqrt


def _pairs(a, b):
    xs, ys = list(a), list(b)
    if len(xs) != len(ys) or not xs:
        raise ValueError("metric inputs must be non-empty and equal length")
    return xs, ys


def mae(actual, predicted) -> float:
    a, p = _pairs(actual, predicted)
    return sum(abs(x-y) for x,y in zip(a,p))/len(a)


def rmse(actual, predicted) -> float:
    a, p = _pairs(actual, predicted)
    return sqrt(sum((x-y)**2 for x,y in zip(a,p))/len(a))


def brier_score(actual_binary, probability) -> float:
    a, p = _pairs(actual_binary, probability)
    if any(x < 0 or x > 1 for x in p): raise ValueError("probabilities must be in [0, 1]")
    return sum((float(x)-float(y))**2 for x,y in zip(a,p))/len(a)


def pinball_loss(actual, predicted_quantile, quantile: float) -> float:
    if not 0 < quantile < 1: raise ValueError("quantile must be in (0,1)")
    a, q = _pairs(actual, predicted_quantile)
    losses=[]
    for x,y in zip(a,q):
        error=x-y; losses.append(max(quantile*error,(quantile-1.0)*error))
    return sum(losses)/len(losses)


def interval_coverage(actual, lower, upper) -> float:
    a, lo = _pairs(actual, lower); _, hi = _pairs(actual, upper)
    return sum(float(l <= x <= h) for x,l,h in zip(a,lo,hi))/len(a)


def direction_accuracy(actual_return, predicted_return) -> float:
    a, p = _pairs(actual_return, predicted_return)
    return sum(float((x >= 0) == (y >= 0)) for x,y in zip(a,p))/len(a)


def signed_direction_accuracy(actual_return, predicted_return) -> dict:
    """Direction hits only where the model predicted a non-zero sign. Zeros abstain."""
    a, p = _pairs(actual_return, predicted_return)
    decided = [(x, y) for x, y in zip(a, p) if y != 0]
    abstentions = len(a) - len(decided)
    if not decided:
        return {"accuracy": None, "sample_count": 0, "abstentions": abstentions, "decided": 0}
    hits = sum(float((x > 0) == (y > 0)) for x, y in decided)
    return {
        "accuracy": hits / len(decided),
        "sample_count": len(decided),
        "abstentions": abstentions,
        "decided": len(decided),
        "metric": "signed_direction_accuracy",
        "zero_predictions_are_abstentions": True,
    }
