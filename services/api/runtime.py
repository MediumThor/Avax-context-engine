from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.context_engine import ContextEngine
from packages.features import FEATURE_SCHEMA_VERSION as MTF_FEATURE_SCHEMA
from packages.features import assemble_features
from packages.fixtures import btc_companion, sept_2026_failed_breakout
from packages.harness.kill_switch import is_engaged
from packages.journal import ForecastJournal
from packages.market_data import CandleStore
from packages.models import (
    InsufficientHistory,
    attach_simple_return_aliases_payload,
    emit_baseline_forecast,
    emit_quantile_forecast,
    walk_forward_baselines,
)
from packages.models.outcomes import mature_outcomes


SOURCE = "binance-vision"
FEATURE_SCHEMA = "1"
QUANTILE_LOOKBACK = 400
LIVE_LOOKBACK_DAYS = 10
LIVE_FRESH_SECONDS = 6 * 60
LIVE_PULL_MIN_INTERVAL = 15
_QUANTILE_BACKENDS = {"auto", "python", "sklearn", "lightgbm"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def freshness(last_close: datetime, now: datetime | None = None) -> dict:
    current = now or _now()
    age = max(0.0, (current - last_close).total_seconds())
    status = "live" if age <= 12 * 60 else "stale"
    return {"status": status, "age_seconds": int(age), "last_close": last_close.isoformat()}


class PrototypeRuntime:
    def __init__(self, db_path: str | Path, journal_path: str | Path, *, use_fixture: bool = False):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(journal_path).parent.mkdir(parents=True, exist_ok=True)
        self.store = CandleStore(db_path)
        self.journal = ForecastJournal(journal_path)
        self.engine = ContextEngine()
        self.use_fixture = use_fixture or os.environ.get("AVAX_USE_FIXTURE") == "1"
        self.source_label = "fixture" if self.use_fixture else SOURCE
        self._snap_cache: dict[tuple, object] = {}
        self._metrics_cache: dict[tuple, dict] = {}
        self._last_pull: dict[str, datetime] = {}
        self._live_error: str | None = None
        if self.use_fixture:
            self._seed_fixture()

    def close(self) -> None:
        self.store.close()
        self.journal.close()

    def _seed_fixture(self) -> None:
        avax = sept_2026_failed_breakout("AVAXUSDT")
        self.store.insert_many("fixture", avax)
        self.store.insert_many("fixture", btc_companion(avax))
        self.source_label = "fixture"

    def _ensure(self, symbol: str) -> None:
        if self.use_fixture:
            existing = self.store.load("fixture", symbol, "5m")
            if not existing:
                self._seed_fixture()
            return
        self._refresh_live(symbol)

    def _pull_live_candles(self, symbol: str, after: datetime | None = None) -> list:
        from packages.market_data import BinanceVisionClient

        client = BinanceVisionClient(timeout=20.0)
        try:
            if after is None:
                return list(client.iter_recent_days(symbol, "5m", LIVE_LOOKBACK_DAYS))
            start_ms = int(after.timestamp() * 1000)
            end_ms = int(_now().timestamp() * 1000)
            return [c for c in client.fetch_klines(symbol, "5m", start_ms, end_ms) if c.is_closed]
        finally:
            client.close()

    def _pull_last_price(self, symbol: str) -> float:
        from packages.market_data import BinanceVisionClient

        client = BinanceVisionClient(timeout=8.0)
        try:
            return client.fetch_last_price(symbol)
        finally:
            client.close()

    def _refresh_live(self, symbol: str) -> None:
        """Append newly closed Binance 5m bars. Never silently become the fixture."""
        existing = self.store.load(SOURCE, symbol, "5m")
        now = _now()
        last_close = existing[-1].close_time() if existing else None
        if last_close and (now - last_close).total_seconds() < LIVE_FRESH_SECONDS:
            self.source_label = SOURCE
            return
        last_pull = self._last_pull.get(symbol)
        if last_pull and (now - last_pull).total_seconds() < LIVE_PULL_MIN_INTERVAL:
            if not existing:
                raise RuntimeError(self._live_error or f"live market data unavailable for {symbol}")
            return
        try:
            candles = self._pull_live_candles(symbol, after=existing[-1].open_time if existing else None)
            self._last_pull[symbol] = now
            if candles:
                self.store.insert_many(SOURCE, candles)
                self.source_label = SOURCE
                self._live_error = None
                return
            if existing:
                return
            raise RuntimeError(f"no live candles returned for {symbol}")
        except RuntimeError:
            raise
        except Exception as exc:
            self._last_pull[symbol] = now
            self._live_error = str(exc)
            if existing:
                return
            raise RuntimeError(f"live market data unavailable for {symbol}: {exc}") from exc

    def candles(self, symbol: str, as_of: datetime | None = None, limit: int = 400):
        self._ensure(symbol)
        source = "fixture" if self.use_fixture else SOURCE
        xs = self.store.load_upto(source, symbol, "5m", as_of) if as_of else self.store.load(source, symbol, "5m")
        return xs[-limit:]

    def snapshot(self, symbol: str, as_of: datetime | None = None):
        avax = self.candles(symbol, as_of=as_of, limit=8000)
        cache_key = (
            symbol,
            avax[-1].close_time().isoformat() if avax else None,
            as_of.isoformat() if as_of else None,
        )
        cached = self._snap_cache.get(cache_key)
        if cached is not None:
            return cached
        btc = []
        try:
            btc = self.candles("BTCUSDT", as_of=as_of or avax[-1].close_time(), limit=8000)
        except Exception:
            btc = []
        cross = {}
        if btc:
            btc_snap = self.engine.build_snapshot(btc, as_of=as_of)
            ret = None
            if len(btc) > 24:
                ret = (btc[-1].close / btc[-25].close) - 1.0
            cross = {
                "BTCUSDT": {
                    "regime_5m": btc_snap.timeframes.get("5m").regime if "5m" in btc_snap.timeframes else "unknown",
                    "regime_4h": btc_snap.timeframes.get("4h").regime if "4h" in btc_snap.timeframes else "unknown",
                    "ret_24": ret,
                }
            }
        snap = self.engine.build_snapshot(avax, as_of=as_of, cross_market=cross)
        self._snap_cache[cache_key] = snap
        return snap

    def forecast(self, symbol: str, as_of: datetime | None = None, persist: bool = True, snap=None) -> dict:
        candles = self.candles(symbol, as_of=as_of, limit=8000)
        btc: list = []
        try:
            btc = self.candles("BTCUSDT", as_of=as_of or candles[-1].close_time(), limit=8000)
        except Exception:
            btc = []
        payload = self.emit_live_forecast(candles, as_of=as_of, btc=btc)
        snap = snap or self.snapshot(symbol, as_of=as_of or candles[-1].close_time())
        snapshot_id = hashlib.sha256(repr(snap.to_dict()).encode()).hexdigest()[:16]
        feature_schema = self._attach_mtf_feature_snapshot(payload, candles, as_of=as_of)
        manifest_id = None
        try:
            source = "fixture" if self.use_fixture else SOURCE
            manifest_id = self.store.manifest(source, symbol, "5m").sha256[:16]
        except Exception:
            pass
        outcomes = {"forecasts_scanned": 0, "outcomes_written": 0}
        if persist and not is_engaged():
            self.journal.get_or_append(
                forecast_id=f"{symbol}:{payload['forecasted_at']}:{payload['model_id']}",
                symbol=symbol,
                forecasted_at=payload["forecasted_at"],
                model_id=payload["model_id"],
                payload=payload,
                context_snapshot_id=snapshot_id,
                feature_schema_version=feature_schema,
                data_manifest_id=manifest_id,
            )
            self._journal_prior_origin(symbol, candles, btc, as_of=as_of, manifest_id=manifest_id)
            outcomes = mature_outcomes(self.journal, candles, symbol, as_of=as_of)
        latest = self.journal.latest(symbol)
        return {
            "forecast": payload,
            "journaled": latest is not None and latest["forecasted_at"] == payload["forecasted_at"],
            "context_snapshot_id": snapshot_id,
            "feature_schema_version": feature_schema,
            "outcomes": outcomes,
            "kill_switch_blocked_write": persist and is_engaged(),
        }

    def _journal_prior_origin(self, symbol: str, candles, btc, as_of, manifest_id) -> None:
        """Journal T-10 so h=1..10 can mature on the same persist without rewriting T."""
        visible = _visible_closed(candles, as_of)
        if len(visible) < 40:
            return
        earlier = visible[:-10]
        prior = self.emit_live_forecast(earlier, as_of=earlier[-1].close_time(), btc=btc)
        self.journal.get_or_append(
            forecast_id=f"{symbol}:{prior['forecasted_at']}:{prior['model_id']}",
            symbol=symbol,
            forecasted_at=prior["forecasted_at"],
            model_id=prior["model_id"],
            payload=prior,
            feature_schema_version=prior.get("feature_schema_version") or FEATURE_SCHEMA,
            data_manifest_id=manifest_id,
        )

    def emit_live_forecast(self, candles, as_of: datetime | None = None, btc=None) -> dict[str, Any]:
        """Prefer leakage-safe empirical quantiles; fall back to honest drift20."""
        visible = _visible_closed(candles, as_of)
        window = visible[-QUANTILE_LOOKBACK:] if len(visible) > QUANTILE_LOOKBACK else list(visible)
        btc_visible = _visible_closed(btc or [], as_of)
        btc_window = btc_visible[-QUANTILE_LOOKBACK:] if len(btc_visible) > QUANTILE_LOOKBACK else list(btc_visible)
        backend = os.environ.get("AVAX_QUANTILE_BACKEND", "python")
        if backend not in _QUANTILE_BACKENDS:
            backend = "python"
        try:
            payload = emit_quantile_forecast(
                window,
                as_of=as_of,
                backend=backend,  # type: ignore[arg-type]
                btc_5m=btc_window or None,
            )
        except InsufficientHistory:
            payload = emit_baseline_forecast(window if len(window) >= 21 else visible)
        return attach_simple_return_aliases_payload(payload)

    def _attach_mtf_feature_snapshot(
        self,
        payload: dict[str, Any],
        candles,
        as_of: datetime | None = None,
    ) -> str:
        try:
            btc = []
            try:
                cutoff = as_of or candles[-1].close_time()
                btc = self.candles("BTCUSDT", as_of=cutoff, limit=8000)
            except Exception:
                btc = []
            snapshot = assemble_features(candles, as_of=as_of, btc_5m=btc or None)
            feature_dict = snapshot.to_dict()
            raw = json.dumps(feature_dict, sort_keys=True, separators=(",", ":"), allow_nan=False)
            digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
            payload["mtf_feature_snapshot"] = feature_dict
            payload["mtf_feature_schema_version"] = MTF_FEATURE_SCHEMA
            payload["feature_snapshot_id"] = digest
            return MTF_FEATURE_SCHEMA
        except Exception:
            return FEATURE_SCHEMA

    def metrics(self, symbol: str, as_of: datetime | None = None) -> dict:
        candles = self.candles(symbol, as_of=as_of, limit=8000)
        if len(candles) < 120:
            return {"available": False, "reason": "insufficient-history"}
        cache_key = (
            symbol,
            candles[-1].close_time().isoformat(),
            as_of.isoformat() if as_of else None,
        )
        cached = self._metrics_cache.get(cache_key)
        if cached is not None:
            return cached
        report = walk_forward_baselines(candles, horizons=10, min_history=80, step=15)
        report["available"] = True
        report["symbol"] = symbol
        self._metrics_cache[cache_key] = report
        return report

    def health_brief(self, symbol: str = "AVAXUSDT") -> dict:
        if self.use_fixture:
            self._ensure(symbol)
            existing = self.store.load("fixture", symbol, "5m")
            if not existing:
                return {"status": "unknown", "age_seconds": None, "last_close": None, "source": "fixture"}
            health = freshness(existing[-1].close_time())
            health["status"] = "fixture"
            health["source"] = "fixture"
            return health
        try:
            self._refresh_live(symbol)
        except RuntimeError as exc:
            return {
                "status": "unknown",
                "age_seconds": None,
                "last_close": None,
                "source": SOURCE,
                "error": str(exc),
            }
        existing = self.store.load(SOURCE, symbol, "5m")
        if not existing:
            return {"status": "unknown", "age_seconds": None, "last_close": None, "source": SOURCE}
        health = freshness(existing[-1].close_time())
        health["source"] = SOURCE
        if self._live_error:
            health["pull_error"] = self._live_error
        return health

    def market_payload(self, symbol: str, as_of: datetime | None = None, chart_limit: int = 576, persist: bool | None = None) -> dict:
        candles = self.candles(symbol, as_of=as_of, limit=max(chart_limit, 400))
        if not candles:
            raise RuntimeError(f"no candles available for {symbol}")
        snap = self.snapshot(symbol, as_of=as_of or candles[-1].close_time())
        last_close = candles[-1].close_time()
        health = freshness(last_close)
        if self.use_fixture:
            health["status"] = "fixture"
        health["source"] = "fixture" if self.use_fixture else SOURCE
        should_persist = persist if persist is not None else as_of is None
        forecast = self.forecast(symbol, as_of=as_of or last_close, persist=should_persist, snap=snap)
        metrics = self.metrics(symbol, as_of=as_of or last_close)
        chart = [
            {
                "time": int(c.open_time.timestamp()),
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
            }
            for c in candles[-chart_limit:]
        ]
        hint = None
        if self.use_fixture:
            from packages.fixtures import bounce_start_index, sept_2026_failed_breakout

            full = sept_2026_failed_breakout(symbol) if symbol == "AVAXUSDT" else []
            if full:
                hint = full[bounce_start_index(full) - 1].close_time().isoformat()
        last_price = candles[-1].close
        price_source = "last_close"
        if not self.use_fixture and as_of is None:
            try:
                last_price = self._pull_last_price(symbol)
                price_source = "ticker"
            except Exception:
                price_source = "last_close"
        payload = {
            "symbol": symbol,
            "source": "fixture" if self.use_fixture else SOURCE,
            "as_of": snap.as_of.isoformat(),
            "health": health,
            "last_price": last_price,
            "price_source": price_source,
            "snapshot": snap.to_dict(),
            "interpretation": snap.interpretation,
            "forecast": forecast,
            "metrics": metrics,
            "candles": chart,
            "replay": as_of is not None,
            "replay_hint_as_of": hint,
            "execution_enabled": False,
        }
        return payload


def _visible_closed(candles, as_of: datetime | None) -> list:
    """Bars whose close is known at as_of. Lookback must use this tail, not the series end."""
    closed = [c for c in candles if getattr(c, "is_closed", True)]
    if as_of is None:
        return closed
    return [c for c in closed if c.close_time() <= as_of]


_RUNTIME: dict[tuple[str, str, bool], PrototypeRuntime] = {}


def get_runtime() -> PrototypeRuntime:
    db = os.environ.get("AVAX_MARKET_DB", "data/market.sqlite3")
    journal = os.environ.get("AVAX_JOURNAL_DB", "data/journal.sqlite3")
    fixture = os.environ.get("AVAX_USE_FIXTURE", "0") == "1"
    key = (db, journal, fixture)
    if key not in _RUNTIME:
        _RUNTIME[key] = PrototypeRuntime(db, journal, use_fixture=fixture)
    return _RUNTIME[key]


def reset_runtime() -> None:
    for runtime in _RUNTIME.values():
        runtime.close()
    _RUNTIME.clear()
