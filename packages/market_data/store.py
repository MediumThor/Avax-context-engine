from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from packages.context_engine.models import Candle


@dataclass(frozen=True, slots=True)
class DataManifest:
    source: str
    symbol: str
    timeframe: str
    count: int
    first_open_time: str
    last_open_time: str
    sha256: str

    def to_dict(self) -> dict:
        return {"source":self.source,"symbol":self.symbol,"timeframe":self.timeframe,"count":self.count,"first_open_time":self.first_open_time,"last_open_time":self.last_open_time,"sha256":self.sha256}


class CandleStore:
    def __init__(self, path: str | Path):
        self.db = sqlite3.connect(str(path))
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS candles(
          source TEXT NOT NULL, symbol TEXT NOT NULL, timeframe TEXT NOT NULL,
          open_time TEXT NOT NULL, open REAL NOT NULL, high REAL NOT NULL,
          low REAL NOT NULL, close REAL NOT NULL, volume REAL NOT NULL,
          payload_sha256 TEXT NOT NULL,
          PRIMARY KEY(source,symbol,timeframe,open_time)
        )""")
        self.db.commit()

    @staticmethod
    def _payload(c: Candle) -> str:
        return json.dumps({"symbol":c.symbol,"timeframe":c.timeframe,"open_time":c.open_time.isoformat(),"open":c.open,"high":c.high,"low":c.low,"close":c.close,"volume":c.volume},sort_keys=True,separators=(",",":"))

    def insert_many(self, source: str, candles: list[Candle]) -> int:
        written = 0
        for candle in candles:
            if not candle.is_closed:
                continue
            raw=self._payload(candle); digest=hashlib.sha256(raw.encode()).hexdigest()
            existing=self.db.execute("SELECT payload_sha256 FROM candles WHERE source=? AND symbol=? AND timeframe=? AND open_time=?",(source,candle.symbol,candle.timeframe,candle.open_time.isoformat())).fetchone()
            if existing:
                if existing[0] != digest:
                    raise ValueError(f"Immutable candle conflict at {candle.symbol} {candle.open_time.isoformat()}")
                continue
            self.db.execute("INSERT INTO candles VALUES(?,?,?,?,?,?,?,?,?,?)",(source,candle.symbol,candle.timeframe,candle.open_time.isoformat(),candle.open,candle.high,candle.low,candle.close,candle.volume,digest)); written += 1
        self.db.commit(); return written

    def load(self, source: str, symbol: str, timeframe: str) -> list[Candle]:
        rows=self.db.execute("SELECT open_time,open,high,low,close,volume FROM candles WHERE source=? AND symbol=? AND timeframe=? ORDER BY open_time",(source,symbol,timeframe)).fetchall()
        from datetime import datetime
        return [Candle(symbol,timeframe,datetime.fromisoformat(r[0]),r[1],r[2],r[3],r[4],r[5],True) for r in rows]

    def manifest(self, source: str, symbol: str, timeframe: str) -> DataManifest:
        candles=self.load(source,symbol,timeframe)
        if not candles: raise ValueError("No candles for manifest")
        h=hashlib.sha256()
        for candle in candles:
            h.update(self._payload(candle).encode()); h.update(b"\n")
        return DataManifest(source,symbol,timeframe,len(candles),candles[0].open_time.isoformat(),candles[-1].open_time.isoformat(),h.hexdigest())

    def close(self) -> None:
        self.db.close()
