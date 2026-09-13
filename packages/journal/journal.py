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
        CREATE TABLE IF NOT EXISTS loop_traces (
          id TEXT PRIMARY KEY,
          forecast_id TEXT NOT NULL,
          encoder_memory_id TEXT,
          as_of TEXT NOT NULL,
          content_hash TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          journaled_at TEXT NOT NULL,
          UNIQUE(forecast_id, content_hash),
          FOREIGN KEY(forecast_id) REFERENCES forecasts(id)
        );
        CREATE TABLE IF NOT EXISTS theses (
          id TEXT PRIMARY KEY,
          lineage_id TEXT NOT NULL,
          symbol TEXT NOT NULL,
          direction TEXT NOT NULL,
          timeframe TEXT,
          status TEXT NOT NULL,
          version INTEGER NOT NULL,
          created_at TEXT NOT NULL,
          invalidation_fingerprint TEXT NOT NULL,
          payload_json TEXT NOT NULL
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

    def list_forecasts(self, symbol: str) -> list[dict]:
        rows = self.db.execute(
            """SELECT id, forecasted_at, model_id, payload_json, payload_sha256
               FROM forecasts WHERE symbol=? ORDER BY forecasted_at ASC""",
            (symbol,),
        ).fetchall()
        return [
            {
                "id": row[0],
                "forecasted_at": row[1],
                "model_id": row[2],
                "payload": json.loads(row[3]),
                "sha256": row[4],
            }
            for row in rows
        ]

    def has_outcome(self, forecast_id: str, horizon: int) -> bool:
        row = self.db.execute(
            "SELECT 1 FROM outcomes WHERE forecast_id=? AND horizon=?",
            (forecast_id, horizon),
        ).fetchone()
        return row is not None

    def append_outcome(self, forecast_id: str, horizon: int, payload: dict) -> None:
        self.db.execute(
            "INSERT INTO outcomes(forecast_id,horizon,payload_json) VALUES(?,?,?)",
            (forecast_id, horizon, self._canonical(payload)),
        )
        self.db.commit()

    def get_or_append_outcome(self, forecast_id: str, horizon: int, payload: dict) -> bool:
        """True when a new outcome row was written. Never overwrites."""
        if self.has_outcome(forecast_id, horizon):
            return False
        try:
            self.append_outcome(forecast_id, horizon, payload)
            return True
        except sqlite3.IntegrityError:
            return False

    def list_outcomes(self, forecast_id: str) -> list[dict]:
        rows = self.db.execute(
            "SELECT horizon, payload_json FROM outcomes WHERE forecast_id=? ORDER BY horizon",
            (forecast_id,),
        ).fetchall()
        return [{"horizon": row[0], **json.loads(row[1])} for row in rows]

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

    def get_or_append_loop_trace(self, forecast_id: str, trace: dict) -> tuple[str, bool]:
        """Append a LoopTrace. Never overwrites an existing id or content_hash."""
        existing = self.db.execute(
            "SELECT id FROM loop_traces WHERE forecast_id=? AND content_hash=?",
            (forecast_id, trace["content_hash"]),
        ).fetchone()
        if existing:
            return existing[0], False
        by_id = self.db.execute("SELECT content_hash FROM loop_traces WHERE id=?", (trace["id"],)).fetchone()
        if by_id:
            return str(trace["id"]), False
        forecast = self.db.execute("SELECT id FROM forecasts WHERE id=?", (forecast_id,)).fetchone()
        if forecast is None:
            raise KeyError(forecast_id)
        raw = self._canonical(trace)
        self.db.execute(
            """INSERT INTO loop_traces(id,forecast_id,encoder_memory_id,as_of,content_hash,payload_json,journaled_at)
               VALUES(?,?,?,?,?,?,?)""",
            (
                trace["id"],
                forecast_id,
                trace.get("encoder_memory_id"),
                trace["as_of"],
                trace["content_hash"],
                raw,
                trace.get("journaled_at") or trace["as_of"],
            ),
        )
        self.db.commit()
        return str(trace["id"]), True

    def get_loop_trace(self, loop_id: str) -> dict:
        row = self.db.execute(
            "SELECT forecast_id, payload_json FROM loop_traces WHERE id=?",
            (loop_id,),
        ).fetchone()
        if row is None:
            raise KeyError(loop_id)
        return {"forecast_id": row[0], "trace": json.loads(row[1])}

    def list_loop_traces(self, forecast_id: str) -> list[dict]:
        rows = self.db.execute(
            "SELECT payload_json FROM loop_traces WHERE forecast_id=? ORDER BY journaled_at ASC",
            (forecast_id,),
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def get_thesis(self, thesis_id: str) -> dict | None:
        row = self.db.execute(
            """SELECT lineage_id, symbol, invalidation_fingerprint, payload_json
               FROM theses WHERE id=?""",
            (thesis_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": thesis_id,
            "lineage_id": row[0],
            "symbol": row[1],
            "invalidation_fingerprint": row[2],
            "payload": json.loads(row[3]),
        }

    def list_theses(self, symbol: str) -> list[dict]:
        rows = self.db.execute(
            """SELECT id, invalidation_fingerprint, payload_json
               FROM theses WHERE symbol=? ORDER BY created_at ASC""",
            (symbol,),
        ).fetchall()
        return [
            {
                "id": row[0],
                "invalidation_fingerprint": row[1],
                "payload": json.loads(row[2]),
            }
            for row in rows
        ]

    def sync_theses(self, theses: list[dict] | tuple) -> dict:
        """Insert new thesis versions. Never rewrite invalidation on an existing id."""
        wrote = 0
        kept = 0
        refused_move = 0
        for row in theses:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            fingerprint = str(row.get("invalidation_fingerprint") or "")
            existing = self.db.execute(
                "SELECT invalidation_fingerprint FROM theses WHERE id=?",
                (row["id"],),
            ).fetchone()
            if existing:
                kept += 1
                if existing[0] != fingerprint:
                    refused_move += 1
                continue
            self.db.execute(
                """INSERT INTO theses(
                       id, lineage_id, symbol, direction, timeframe, status, version,
                       created_at, invalidation_fingerprint, payload_json
                   ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    row["id"],
                    str(row.get("lineage_id") or row["id"]),
                    str(row.get("symbol") or "AVAXUSDT"),
                    str(row.get("direction") or ""),
                    row.get("timeframe"),
                    str(row.get("status") or "active"),
                    int(row.get("version") or 1),
                    str(row.get("created_at") or ""),
                    fingerprint,
                    self._canonical(row),
                ),
            )
            wrote += 1
        if wrote:
            self.db.commit()
        return {"wrote": wrote, "kept": kept, "refused_move": refused_move}

    def close(self) -> None:
        self.db.close()
