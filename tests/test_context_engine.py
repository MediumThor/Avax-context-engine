from datetime import datetime, timedelta, timezone

from packages.context_engine import Candle, ContextEngine
from packages.context_engine.resample import resample_closed
from packages.context_engine.structure import confirmed_pivots


def candles(n=300,start=10.0,step=-0.01):
    t0=datetime(2026,1,1,tzinfo=timezone.utc); out=[]; price=start
    for i in range(n):
        close=price+step
        out.append(Candle("AVAXUSDT","5m",t0+timedelta(minutes=5*i),price,max(price,close)+0.01,min(price,close)-0.01,close,100+i))
        price=close
    return out


def test_resample_emits_only_complete_parent_bucket():
    xs=candles(5)
    assert len(resample_closed(xs,15,"15m")) == 1


def test_context_snapshot_is_bearish_for_persistent_decline():
    snap=ContextEngine().build_snapshot(candles())
    assert snap.timeframes["5m"].regime in {"bearish","transition_down"}
    assert snap.timeframes["1h"].regime in {"bearish","transition_down"}


def test_pivot_known_at_is_after_pivot_time():
    xs=candles(20,start=10.0,step=0.0)
    xs[8]=Candle("AVAXUSDT","5m",xs[8].open_time,10,12,9.9,10,100)
    high=next(p for p in confirmed_pivots(xs,left=2,right=2) if p.kind=="high" and p.index==8)
    assert high.known_at_index==10
    assert high.known_at > high.time
