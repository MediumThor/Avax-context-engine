from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


class ForecastJournal:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS forecasts (
          id TEXT PRIMARY KEY, symbol TEXT NOT NULL, forecasted_at TEXT NOT NULL,
          model_id TEXT NOT NULL, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
          UNIQUE(symbol, forecasted_at, model_id)
        );
        CREATE TABLE IF NOT EXISTS outcomes (
          forecast_id TEXT NOT NULL, horizon INTEGER NOT NULL, payload_json TEXT NOT NULL,
          PRIMARY KEY(forecast_id, horizon), FOREIGN KEY(forecast_id) REFERENCES forecasts(id)
        );
        """)
        self.db.commit()

    @staticmethod
    def _canonical(payload: dict) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",",":"), allow_nan=False)

    def append_forecast(self, forecast_id: str, symbol: str, forecasted_at: str, model_id: str, payload: dict) -> str:
        raw=self._canonical(payload); digest=hashlib.sha256(raw.encode()).hexdigest()
        self.db.execute("INSERT INTO forecasts(id,symbol,forecasted_at,model_id,payload_json,payload_sha256) VALUES(?,?,?,?,?,?)",(forecast_id,symbol,forecasted_at,model_id,raw,digest))
        self.db.commit(); return digest

    def append_outcome(self, forecast_id: str, horizon: int, payload: dict) -> None:
        self.db.execute("INSERT INTO outcomes(forecast_id,horizon,payload_json) VALUES(?,?,?)",(forecast_id,horizon,self._canonical(payload)))
        self.db.commit()

    def get_forecast(self, forecast_id: str) -> dict:
        row=self.db.execute("SELECT payload_json,payload_sha256 FROM forecasts WHERE id=?",(forecast_id,)).fetchone()
        if row is None: raise KeyError(forecast_id)
        return {"payload":json.loads(row[0]),"sha256":row[1]}

    def close(self) -> None:
        self.db.close()
