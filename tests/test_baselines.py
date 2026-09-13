from datetime import datetime,timedelta,timezone

from packages.context_engine.models import Candle
from packages.models import evaluate_baselines


def test_baseline_outputs_all_ten_horizons():
    t=datetime(2026,1,1,tzinfo=timezone.utc); xs=[]
    for i in range(400):
        p=10+i*.001
        xs.append(Candle("AVAXUSDT","5m",t+timedelta(minutes=5*i),p,p+.01,p-.01,p+.0005,100))
    result=evaluate_baselines(xs,10)
    assert set(result)=={str(i) for i in range(1,11)}
    assert all(result[str(i)]["sample_count"]>0 for i in range(1,11))
