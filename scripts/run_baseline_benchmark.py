from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from packages.market_data import CandleStore
from packages.models import evaluate_baselines


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--db",default="data/market.sqlite3"); p.add_argument("--output",default="artifacts/baseline.json"); p.add_argument("--symbol",default="AVAXUSDT"); args=p.parse_args()
    store=CandleStore(args.db)
    try:
        candles=store.load("binance-vision",args.symbol,"5m")
        manifest=store.manifest("binance-vision",args.symbol,"5m").to_dict()
    finally: store.close()
    result={"created_at":datetime.now(timezone.utc).isoformat(),"symbol":args.symbol,"target":"cumulative_log_return","horizons":evaluate_baselines(candles,10),"data_manifest":manifest}
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))

if __name__ == "__main__": main()
