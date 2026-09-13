"""Sealed September 2026 fixture dump. Checksum, not a forecast score."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from packages.context_engine import Candle, ContextEngine
from packages.fixtures import bounce_start_index, sept_2026_failed_breakout

ROOT = Path(__file__).resolve().parents[1]
DUMP_DIR = ROOT / "benchmarks" / "rlh" / "avax-2026-09-failed-8"
DUMP = DUMP_DIR / "candles.jsonl"
MANIFEST = DUMP_DIR / "manifest.json"


def _load_dump() -> list[Candle]:
    candles: list[Candle] = []
    for line in DUMP.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        candles.append(
            Candle(
                rec["symbol"],
                rec["timeframe"],
                datetime.fromisoformat(rec["open_time"]),
                rec["open"],
                rec["high"],
                rec["low"],
                rec["close"],
                rec["volume"],
                rec.get("is_closed", True),
            )
        )
    return candles


def test_sealed_dump_matches_manifest_and_fixture():
    body = DUMP.read_bytes()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["status"] == "sealed"
    assert manifest["candle_count"] == 3768
    assert hashlib.sha256(body).hexdigest() == manifest["sha256"]
    fixture = sept_2026_failed_breakout("AVAXUSDT")
    dump = _load_dump()
    assert len(dump) == len(fixture) == manifest["candle_count"]
    assert dump[0].open_time == fixture[0].open_time
    assert dump[-1].close_time() == fixture[-1].close_time()
    assert abs(dump[-1].close - fixture[-1].close) < 1e-12
    assert manifest["as_of_range"][0] == fixture[0].open_time.isoformat()
    assert manifest["as_of_range"][1] == fixture[-1].close_time().isoformat()


def test_dump_replay_at_bounce_keeps_4h_and_hides_later_closes():
    dump = _load_dump()
    idx = bounce_start_index(dump)
    as_of = dump[idx - 1].close_time()
    visible = [c for c in dump if c.close_time() <= as_of]
    assert visible[-1].close_time() == as_of
    assert len(visible) == idx
    snap = ContextEngine().build_snapshot(dump, as_of=as_of)
    assert snap.as_of == as_of
    assert snap.timeframes["4h"].regime in {"bearish", "transition_down"}
    for row in snap.analogs:
        assert row["known_at"] <= as_of.isoformat()
        assert "Not a forecast" in row["note"]
        assert "confidence" not in row
