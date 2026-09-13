from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


class ForecastJournal:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(
            """
        CREATE TABLE IF NOT EXISTS forecasts (
          id TEXT PRIMARY KEY, symbol TEXT NOT NULL, forecasted_at TEXT NOT NULL,
          model_id TEXT NOT NULL, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
          context_snapshot_id TEXT, feature_schema_version TEXT, data_manifest_id TEXT,
          UNIQUE(symbol, forecasted_at, model_id)
        );
        CREATE TABLE IF NOT EXISTS outcomes (
          forecast_id TEXT NOT NULL, horizon INTEGER NOT NULL, payload_json TEXT NOT NULL,
          PRIMARY KEY(forecast_id, horizon), FOREIGN KEY(forecast_id) REFERENCES forecasts(id)
        );
        """
        )
        cols = {row[1] for row in self.db.execute("PRAGMA table_info(forecasts)")}
        for column in ("context_snapshot_id", "feature_schema_version", "data_manifest_id"):
            if column not in cols:
                self.db.execute(f"ALTER TABLE forecasts ADD COLUMN {column} TEXT")
        self.db.commit()

    @staticmethod
    def _canonical(payload: dict) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def append_forecast(
        self,
        forecast_id: str,
        symbol: str,
        forecasted_at: str,
        model_id: str,
        payload: dict,
        context_snapshot_id: str | None = None,
        feature_schema_version: str = "1",
        data_manifest_id: str | None = None,
    ) -> str:
        raw = self._canonical(payload)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        self.db.execute(
            """INSERT INTO forecasts(id,symbol,forecasted_at,model_id,payload_json,payload_sha256,
               context_snapshot_id,feature_schema_version,data_manifest_id)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                forecast_id,
                symbol,
                forecasted_at,
                model_id,
                raw,
                digest,
                context_snapshot_id,
                feature_schema_version,
                data_manifest_id,
            ),
        )
        self.db.commit()
        return digest

    def get_or_append(self, **kwargs) -> tuple[str, bool]:
        symbol = kwargs["symbol"]
        forecasted_at = kwargs["forecasted_at"]
        model_id = kwargs["model_id"]
        row = self.db.execute(
            "SELECT id, payload_sha256 FROM forecasts WHERE symbol=? AND forecasted_at=? AND model_id=?",
            (symbol, forecasted_at, model_id),
        ).fetchone()
        if row:
            return row[1], False
        digest = self.append_forecast(**kwargs)
        return digest, True

    def latest(self, symbol: str) -> dict | None:
        row = self.db.execute(
            """SELECT id, forecasted_at, model_id, payload_json, payload_sha256,
                      context_snapshot_id, feature_schema_version
               FROM forecasts WHERE symbol=? ORDER BY forecasted_at DESC LIMIT 1""",
            (symbol,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "forecasted_at": row[1],
            "model_id": row[2],
            "payload": json.loads(row[3]),
            "sha256": row[4],
            "context_snapshot_id": row[5],
            "feature_schema_version": row[6],
        }

    def append_outcome(self, forecast_id: str, horizon: int, payload: dict) -> None:
        self.db.execute(
            "INSERT INTO outcomes(forecast_id,horizon,payload_json) VALUES(?,?,?)",
            (forecast_id, horizon, self._canonical(payload)),
        )
        self.db.commit()

    def get_forecast(self, forecast_id: str) -> dict:
        row = self.db.execute(
            "SELECT payload_json,payload_sha256,context_snapshot_id,feature_schema_version FROM forecasts WHERE id=?",
            (forecast_id,),
        ).fetchone()
        if row is None:
            raise KeyError(forecast_id)
        return {
            "payload": json.loads(row[0]),
            "sha256": row[1],
            "context_snapshot_id": row[2],
            "feature_schema_version": row[3],
        }

    def close(self) -> None:
        self.db.close()
