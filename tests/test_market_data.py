from datetime import datetime,timedelta,timezone

import pytest

from packages.context_engine.models import Candle
from packages.market_data.store import CandleStore


def candle(i:int,close:float=10.0)->Candle:
    t=datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(minutes=5*i)
    return Candle("AVAXUSDT","5m",t,close,close+.1,close-.1,close,100+i)


def test_store_is_immutable_and_manifest_stable(tmp_path):
    store=CandleStore(tmp_path/"m.db")
    xs=[candle(i,10+i*.01) for i in range(20)]
    assert store.insert_many("test",xs)==20
    first=store.manifest("test","AVAXUSDT","5m")
    assert store.insert_many("test",xs)==0
    assert store.manifest("test","AVAXUSDT","5m").sha256==first.sha256
    with pytest.raises(ValueError): store.insert_many("test",[candle(3,99)])
    store.close()
