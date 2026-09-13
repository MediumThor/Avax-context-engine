from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.market_data import BinanceVisionClient, CandleStore


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--days",type=int,default=30)
    p.add_argument("--db",default="data/market.sqlite3")
    p.add_argument("--symbols",nargs="+",default=["AVAXUSDT","BTCUSDT","ETHUSDT"])
    args=p.parse_args()
    Path(args.db).parent.mkdir(parents=True,exist_ok=True)
    store=CandleStore(args.db); client=BinanceVisionClient()
    manifests=[]
    try:
        for symbol in args.symbols:
            candles=list(client.iter_recent_days(symbol,"5m",args.days))
            store.insert_many("binance-vision",candles)
            manifests.append(store.manifest("binance-vision",symbol,"5m").to_dict())
    finally:
        client.close(); store.close()
    print(json.dumps({"manifests":manifests},indent=2))

if __name__ == "__main__": main()
