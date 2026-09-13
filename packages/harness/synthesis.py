from __future__ import annotations

from packages.context_engine.models import MarketSnapshot


def build_analysis(snapshot: MarketSnapshot, forecast: dict | None = None) -> dict:
    """Deterministic pre-LLM synthesis. AI may explain this object but must not mutate facts."""
    hierarchy=[tf for tf in ["1d","4h","1h","15m","5m"] if tf in snapshot.timeframes]
    regimes={tf:snapshot.timeframes[tf].regime for tf in hierarchy}
    primary=next((regimes[tf] for tf in hierarchy if regimes[tf] in {"bullish","bearish"}),"neutral")
    bull_evidence=[]; bear_evidence=[]
    for tf in hierarchy:
        state=snapshot.timeframes[tf]
        bucket=bull_evidence if state.regime=="bullish" else bear_evidence if state.regime=="bearish" else None
        if bucket is not None: bucket.extend(f"{tf}:{item}" for item in state.evidence)
    return {"symbol":snapshot.symbol,"as_of":snapshot.as_of.isoformat(),"primary_regime":primary,"regimes":regimes,"bull_case":{"evidence":bull_evidence},"bear_case":{"evidence":bear_evidence},"forecast":forecast,"confidence_source":"calibrated" if forecast and forecast.get("calibration_ref") else "insufficient-data"}
