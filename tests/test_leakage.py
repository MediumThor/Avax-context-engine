from datetime import datetime,timedelta,timezone

from packages.context_engine import Candle,ContextEngine


def make(n=320):
    t0=datetime(2026,1,1,tzinfo=timezone.utc)
    return [Candle("AVAXUSDT","5m",t0+timedelta(minutes=5*i),10+i*.001,10.02+i*.001,9.98+i*.001,10.005+i*.001,100) for i in range(n)]


def test_future_candles_do_not_change_prior_snapshot():
    xs=make(); t=250
    a=ContextEngine().build_snapshot(xs[:t])
    mutated=xs[:t]+[Candle("AVAXUSDT","5m",c.open_time,100,110,90,105,99999) for c in xs[t:]]
    b=ContextEngine().build_snapshot(mutated[:t])
    assert a.to_dict()==b.to_dict()
