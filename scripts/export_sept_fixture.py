#!/usr/bin/env python3
"""Write the sealed September 2026 fixture candles.jsonl + checksum."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from packages.fixtures import sept_2026_failed_breakout

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "benchmarks" / "rlh" / "avax-2026-09-failed-8"
OUT = OUT_DIR / "candles.jsonl"


def main() -> None:
    candles = sept_2026_failed_breakout("AVAXUSDT")
    lines = []
    for candle in candles:
        rec = {
            "symbol": candle.symbol,
            "timeframe": candle.timeframe,
            "open_time": candle.open_time.isoformat(),
            "close_time": candle.close_time().isoformat(),
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
            "is_closed": candle.is_closed,
        }
        lines.append(json.dumps(rec, sort_keys=True, separators=(",", ":")))
    body = "\n".join(lines) + "\n"
    OUT.write_text(body, encoding="utf-8")
    digest = hashlib.sha256(body.encode()).hexdigest()
    manifest = {
        "id": "avax-2026-09-failed-8",
        "status": "sealed",
        "symbol": "AVAXUSDT",
        "timeframe": "5m",
        "candle_count": len(candles),
        "sha256": digest,
        "path": "benchmarks/rlh/avax-2026-09-failed-8/candles.jsonl",
        "purpose": "Founding dogfood: failed ~$8 breakout. Relief bounces must not reset 4H bear after structural invalidation.",
        "as_of_range": ["2026-08-20T00:00:00+00:00", candles[-1].close_time().isoformat()],
        "source": "packages.fixtures.sept_2026_failed_breakout",
        "owner": "agent-00",
        "required": True,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(OUT, len(candles), digest)


if __name__ == "__main__":
    main()
