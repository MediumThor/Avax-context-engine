from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.context_engine import ContextEngine
from packages.context_engine.engine import TIMEFRAMES
from packages.context_engine.indicators import ema
from packages.context_engine.resample import resample_closed
from packages.features import FEATURE_SCHEMA_VERSION as MTF_FEATURE_SCHEMA
from packages.features import assemble_features
from packages.fixtures import btc_companion, sept_2026_failed_breakout
from packages.harness.kill_switch import AgentsSevered, is_engaged
from packages.journal import ForecastJournal
from packages.market_data import CandleStore
from packages.models import (
    InsufficientHistory,
    attach_simple_return_aliases_payload,
    emit_baseline_forecast,
    emit_quantile_forecast,
    score_journaled_forecasts,
    walk_forward_baselines,
    walk_forward_htf_regime,
    walk_forward_probabilities,
    walk_forward_quantiles,
)
from packages.models.outcomes import mature_outcomes


SOURCE = "binance-vision"
FEATURE_SCHEMA = "1"
CHART_SOURCE_LIMIT = 8000
DEFAULT_CHART_TF = "5m"


class LiveDataUnavailable(RuntimeError):
    """Live Binance Vision pull failed. Do not seed the September fixture."""
QUANTILE_LOOKBACK = 400
QUANTILE_WF_MIN_HISTORY = 120
QUANTILE_WF_STEP = 80
_QUANTILE_BACKENDS = {"auto", "python", "sklearn", "lightgbm"}
SHADOW_CATCHUP_BUDGET = 24
SHADOW_DRAIN_BUDGET = 200
SHADOW_DRAIN_ROUNDS_MAX = 25
SHADOW_CATCHUP_MODEL = "baseline.drift20"


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
        if self.use_fixture:
            self._seed_fixture()

    def close(self) -> None:
        self.store.close()
        self.journal.close()

    def _with_data_source(self, payload: dict) -> dict:
        """Stamp candle origin on new journal writes. Existing rows stay append-only."""
        if payload.get("data_source") in {SOURCE, "fixture", "live"}:
            return payload
        payload["data_source"] = "fixture" if self.use_fixture else SOURCE
        return payload

    def _seed_fixture(self) -> None:
        avax = sept_2026_failed_breakout("AVAXUSDT")
        self.store.insert_many("fixture", avax)
        self.store.insert_many("fixture", btc_companion(avax))
        self.source_label = "fixture"

    def _pull_closed_live(self, symbol: str, *, start: datetime | None = None) -> list:
        """Closed 5m bars only. Callers must not treat an open bar as known."""
        from packages.market_data import BinanceVisionClient

        client = BinanceVisionClient(timeout=12.0)
        try:
            if start is None:
                rows = list(client.iter_recent_days(symbol, "5m", 10))
            else:
                end = datetime.now(timezone.utc)
                rows = [
                    candle
                    for candle in client.fetch_klines(
                        symbol,
                        "5m",
                        int(start.timestamp() * 1000),
                        int(end.timestamp() * 1000),
                    )
                    if candle.is_closed
                ]
        except Exception as exc:
            raise LiveDataUnavailable(str(exc)) from exc
        finally:
            client.close()
        return rows

    def _ensure(self, symbol: str) -> None:
        if self.use_fixture:
            existing = self.store.load("fixture", symbol, "5m")
            if not existing:
                self._seed_fixture()
            return
        existing = self.store.load(SOURCE, symbol, "5m")
        try:
            start = existing[-1].open_time if existing else None
            pulled = self._pull_closed_live(symbol, start=start)
        except LiveDataUnavailable:
            if existing:
                return
            raise
        if not pulled and not existing:
            raise LiveDataUnavailable(f"Binance Vision returned no closed {symbol} 5m bars")
        if pulled:
            self.store.insert_many(SOURCE, pulled)
        self.source_label = SOURCE

    def candles(self, symbol: str, as_of: datetime | None = None, limit: int = 400):
        self._ensure(symbol)
        source = "fixture" if self.use_fixture else SOURCE
        xs = self.store.load_upto(source, symbol, "5m", as_of) if as_of else self.store.load(source, symbol, "5m")
        return xs[-limit:]

    def snapshot(self, symbol: str, as_of: datetime | None = None, persist_theses: bool | None = None):
        avax = self.candles(symbol, as_of=as_of, limit=8000)
        should_write = persist_theses if persist_theses is not None else as_of is None
        cache_key = (
            symbol,
            avax[-1].close_time().isoformat() if avax else None,
            as_of.isoformat() if as_of else None,
        )
        cached = self._snap_cache.get(cache_key)
        if cached is not None:
            if should_write and not is_engaged():
                self.journal.sync_theses(cached.theses)
                cached = self._freeze_theses_from_ledger(cached)
                self._snap_cache[cache_key] = cached
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
        if should_write and not is_engaged():
            self.journal.sync_theses(snap.theses)
        snap = self._freeze_theses_from_ledger(snap)
        self._snap_cache[cache_key] = snap
        return snap

    def _freeze_theses_from_ledger(self, snap):
        """Keep stored invalidation. A later rebuild may not move a journaled price."""
        bound: list[dict[str, Any]] = []
        for row in snap.theses:
            item = dict(row)
            stored = self.journal.get_thesis(str(item.get("id") or ""))
            if stored:
                payload = stored["payload"]
                item["invalidation_rules"] = payload.get("invalidation_rules", item.get("invalidation_rules"))
                item["invalidation_fingerprint"] = stored["invalidation_fingerprint"]
                if payload.get("created_at"):
                    item["created_at"] = payload["created_at"]
                item["ledger"] = "journaled"
            else:
                item["ledger"] = "ephemeral"
            bound.append(item)
        return replace(snap, theses=tuple(bound))

    def forecast(self, symbol: str, as_of: datetime | None = None, persist: bool = True, snap=None) -> dict:
        candles = self.candles(symbol, as_of=as_of, limit=8000)
        btc: list = []
        try:
            btc = self.candles("BTCUSDT", as_of=as_of or candles[-1].close_time(), limit=8000)
        except Exception:
            btc = []
        payload = self.emit_live_forecast(candles, as_of=as_of, btc=btc)
        snap = snap or self.snapshot(
            symbol, as_of=as_of or candles[-1].close_time(), persist_theses=persist
        )
        snapshot_id = hashlib.sha256(repr(snap.to_dict()).encode()).hexdigest()[:16]
        feature_schema = self._attach_mtf_feature_snapshot(payload, candles, as_of=as_of)
        manifest_id = None
        try:
            source = "fixture" if self.use_fixture else SOURCE
            manifest_id = self.store.manifest(source, symbol, "5m").sha256[:16]
        except Exception:
            pass
        outcomes = {"forecasts_scanned": 0, "outcomes_written": 0}
        shadow = {"wrote": 0, "remaining": 0, "model_id": SHADOW_CATCHUP_MODEL}
        if persist and not is_engaged():
            payload = self._with_data_source(payload)
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
            shadow = self._journal_shadow_origins(
                symbol, candles, btc, as_of=as_of, manifest_id=manifest_id
            )
            outcomes = mature_outcomes(self.journal, candles, symbol, as_of=as_of)
        loop = self._maybe_run_live_loop(
            symbol=symbol,
            payload=payload,
            snap=snap,
            snapshot_id=snapshot_id,
            manifest_id=manifest_id,
            feature_schema=feature_schema,
            persist=persist,
        )
        latest = self.journal.latest(symbol)
        return {
            "forecast": payload,
            "journaled": latest is not None and latest["forecasted_at"] == payload["forecasted_at"],
            "context_snapshot_id": snapshot_id,
            "feature_schema_version": feature_schema,
            "outcomes": outcomes,
            "shadow_journal": shadow,
            "kill_switch_blocked_write": persist and is_engaged(),
            "loop": loop,
        }

    def _maybe_run_live_loop(
        self,
        *,
        symbol: str,
        payload: dict[str, Any],
        snap,
        snapshot_id: str,
        manifest_id: str | None,
        feature_schema: str,
        persist: bool,
    ) -> dict[str, Any]:
        """Bounded loop after journal write. Never mutates the forecast payload."""
        skipped = {
            "ran": False,
            "reason": "kill_switch",
            "note": "Kill switch skipped the loop. Forecast row unchanged.",
            "persisted": False,
        }
        if is_engaged():
            return skipped
        try:
            return self._run_live_loop(
                symbol=symbol,
                payload=payload,
                snap=snap,
                snapshot_id=snapshot_id,
                manifest_id=manifest_id,
                feature_schema=feature_schema,
                persist=persist,
            )
        except AgentsSevered:
            return skipped
        except Exception as exc:
            return {
                "ran": False,
                "reason": "loop_error",
                "persisted": False,
                "note": f"Loop did not finish ({type(exc).__name__}). Forecast row unchanged. Not confidence.",
            }

    def _run_live_loop(
        self,
        *,
        symbol: str,
        payload: dict[str, Any],
        snap,
        snapshot_id: str,
        manifest_id: str | None,
        feature_schema: str,
        persist: bool,
    ) -> dict[str, Any]:
        from services.harness.encoder import build_encoder_memory, snapshot_analogs, snapshot_theses
        from services.harness.encoder.tools import EncoderTools
        from services.harness.loop import run_loop

        snap_dict = snap.to_dict() if hasattr(snap, "to_dict") else dict(snap)
        as_of = snap.as_of if hasattr(snap, "as_of") else snap_dict.get("as_of")
        analogs = snapshot_analogs(snap)
        theses = snapshot_theses(snap)
        brief = self.health_brief(symbol)
        status = brief.get("status")
        health = "stale" if status == "stale" else "unknown" if status == "unknown" else "valid"
        forecast_id = payload.get("id") or f"{symbol}:{payload['forecasted_at']}:{payload['model_id']}"
        memory = build_encoder_memory(
            as_of=as_of,
            snapshot=snap,
            forecast_package={
                "id": forecast_id,
                "calibration_ref": payload.get("calibration_ref"),
                "horizons": payload.get("horizons") or [],
            },
            data_manifest_id=manifest_id or snapshot_id or "unknown",
            feature_schema_version=feature_schema,
            context_engine_version=str(getattr(snap, "schema_version", None) or snap_dict.get("schema_version") or "1"),
            cross_market=getattr(snap, "cross_market", None) or snap_dict.get("cross_market") or {},
            health=health,
        )
        tools = EncoderTools(
            memory,
            snapshot=snap_dict,
            forecast=payload,
            analogs=analogs,
            hypotheses=theses,
        )
        trace = run_loop(
            memory=memory,
            forecast=payload,
            tools=tools,
            hypotheses=theses,
            commit_sha="local",
            journaled_at=str(payload.get("forecasted_at") or memory["as_of"]),
        )
        halt = trace.get("halt") or {}
        journal_forecast_id = f"{symbol}:{payload['forecasted_at']}:{payload['model_id']}"
        persisted = False
        if persist and not is_engaged():
            try:
                self.journal.get_or_append_loop_trace(journal_forecast_id, trace)
                persisted = True
            except KeyError:
                persisted = False
        return {
            "ran": True,
            "loop_id": trace.get("id"),
            "encoder_memory_id": memory["id"],
            "encoder_memory_hash": memory["content_hash"],
            "halt_reason": halt.get("reason"),
            "analog_count": len(analogs),
            "hypothesis_ids": list(memory.get("hypothesis_ids") or []),
            "zone_count": len(memory.get("zone_ids") or []),
            "persisted": persisted,
            "note": "Loop reads frozen snapshot analogs and theses. Not a forecast and not confidence.",
        }

    def _forecast_at_or_before(self, symbol: str, as_of: datetime | None) -> dict | None:
        if as_of is None:
            return self.journal.latest(symbol)
        chosen = None
        for row in self.journal.list_forecasts(symbol):
            stamp = datetime.fromisoformat(str(row["forecasted_at"]).replace("Z", "+00:00"))
            if stamp <= as_of:
                chosen = row
        return chosen

    def run_harness_loop(
        self,
        symbol: str = "AVAXUSDT",
        as_of: datetime | None = None,
        persist: bool | None = None,
    ) -> dict[str, Any]:
        """Bounded loop on a journaled forecast. Does not emit a new forecast."""
        should_persist = persist if persist is not None else as_of is None
        stored = self._forecast_at_or_before(symbol, as_of)
        if stored is None:
            return {
                "accepted": True,
                "harness_version": "rlh-0.1.0",
                "ran": False,
                "reason": "no_journaled_forecast",
                "persisted": False,
                "note": "No journaled forecast to attach a loop to. Does not emit a forecast. Not confidence.",
            }
        payload = stored["payload"]
        forecasted_at = datetime.fromisoformat(str(stored["forecasted_at"]).replace("Z", "+00:00"))
        snap = self.snapshot(symbol, as_of=as_of or forecasted_at, persist_theses=False)
        snapshot_id = stored.get("context_snapshot_id") or hashlib.sha256(
            repr(snap.to_dict()).encode()
        ).hexdigest()[:16]
        loop = self._maybe_run_live_loop(
            symbol=symbol,
            payload=payload,
            snap=snap,
            snapshot_id=snapshot_id,
            manifest_id=None,
            feature_schema=stored.get("feature_schema_version") or FEATURE_SCHEMA,
            persist=should_persist,
        )
        if should_persist and not loop.get("persisted") and stored.get("id"):
            traces = self.journal.list_loop_traces(stored["id"])
            if traces:
                loop["persisted"] = True
                loop["loop_id"] = traces[-1].get("id") or loop.get("loop_id")
        return {
            "accepted": True,
            "harness_version": "rlh-0.1.0",
            "forecast_id": stored["id"],
            **loop,
            "note": loop.get("note")
            or "Loop reads a journaled forecast. Does not emit a new forecast. Not confidence.",
        }

    def _journal_prior_origin(self, symbol: str, candles, btc, as_of, manifest_id) -> None:
        """Journal T-10 so h=1..10 can mature on the same persist without rewriting T."""
        visible = _visible_closed(candles, as_of)
        if len(visible) < 40:
            return
        earlier = visible[:-10]
        prior = self._with_data_source(
            self.emit_live_forecast(earlier, as_of=earlier[-1].close_time(), btc=btc)
        )
        self.journal.get_or_append(
            forecast_id=f"{symbol}:{prior['forecasted_at']}:{prior['model_id']}",
            symbol=symbol,
            forecasted_at=prior["forecasted_at"],
            model_id=prior["model_id"],
            payload=prior,
            feature_schema_version=prior.get("feature_schema_version") or FEATURE_SCHEMA,
            data_manifest_id=manifest_id,
        )

    def _journaled_origin_stamps(self, symbol: str) -> set[str]:
        stamps: set[str] = set()
        for row in self.journal.list_forecasts(symbol):
            stamps.add(_origin_stamp(row.get("forecasted_at")))
        return stamps

    def _journal_shadow_origins(
        self, symbol: str, candles, btc, as_of, manifest_id, *, budget: int = SHADOW_CATCHUP_BUDGET
    ) -> dict[str, Any]:
        """Fill missing mature-able 5m origins with drift20. No extra quantile emit."""
        visible = _visible_closed(candles, as_of)
        empty = {"wrote": 0, "remaining": 0, "model_id": SHADOW_CATCHUP_MODEL}
        if len(visible) < 31:
            return empty
        matureable = visible[:-10]
        known = self._journaled_origin_stamps(symbol)
        missing = [
            index
            for index in range(20, len(matureable))
            if _origin_stamp(matureable[index].close_time()) not in known
        ]
        remaining = max(0, len(missing) - budget)
        wrote = 0
        for index in missing[:budget]:
            prefix = matureable[: index + 1]
            try:
                payload = self._with_data_source(emit_baseline_forecast(prefix))
            except ValueError:
                continue
            stamp = _origin_stamp(payload["forecasted_at"])
            if stamp in known:
                continue
            self.journal.get_or_append(
                forecast_id=f"{symbol}:{payload['forecasted_at']}:{payload['model_id']}",
                symbol=symbol,
                forecasted_at=payload["forecasted_at"],
                model_id=payload["model_id"],
                payload=payload,
                feature_schema_version=FEATURE_SCHEMA,
                data_manifest_id=manifest_id,
            )
            known.add(stamp)
            wrote += 1
        return {
            "wrote": wrote,
            "remaining": remaining,
            "model_id": SHADOW_CATCHUP_MODEL,
            "note": "Catch-up uses drift20 only. Not a quantile emit and not a promotion claim.",
        }

    def drain_shadow_journal(
        self,
        symbol: str,
        *,
        budget: int = SHADOW_DRAIN_BUDGET,
        rounds: int = 1,
    ) -> dict[str, Any]:
        """Fill more missing mature-able 5m origins. Does not emit a quantile or run a loop."""
        if is_engaged():
            return {
                "wrote": 0,
                "remaining": 0,
                "model_id": SHADOW_CATCHUP_MODEL,
                "blocked": True,
                "rounds_used": 0,
                "note": "Kill switch blocks journal drain.",
            }
        capped = max(1, min(int(budget), 500))
        capped_rounds = max(1, min(int(rounds), SHADOW_DRAIN_ROUNDS_MAX))
        candles = self.candles(symbol, limit=8000)
        as_of = candles[-1].close_time() if candles else None
        btc: list = []
        try:
            btc = self.candles("BTCUSDT", as_of=as_of, limit=8000)
        except Exception:
            btc = []
        manifest_id = None
        try:
            source = "fixture" if self.use_fixture else SOURCE
            manifest_id = self.store.manifest(source, symbol, "5m").sha256[:16]
        except Exception:
            pass
        wrote = 0
        remaining = 0
        used = 0
        shadow: dict[str, Any] = {
            "wrote": 0,
            "remaining": 0,
            "model_id": SHADOW_CATCHUP_MODEL,
        }
        for _ in range(capped_rounds):
            shadow = self._journal_shadow_origins(
                symbol, candles, btc, as_of, manifest_id, budget=capped
            )
            used += 1
            wrote += int(shadow.get("wrote") or 0)
            remaining = int(shadow.get("remaining") or 0)
            if wrote == 0 or remaining == 0 or int(shadow.get("wrote") or 0) == 0:
                break
        outcomes = mature_outcomes(self.journal, candles, symbol, as_of=as_of)
        self._metrics_cache.clear()
        shadow["wrote"] = wrote
        shadow["remaining"] = remaining
        shadow["blocked"] = False
        shadow["budget"] = capped
        shadow["rounds_used"] = used
        shadow["outcomes"] = outcomes
        return shadow

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

    def metrics(self, symbol: str, as_of: datetime | None = None, *, include_challenger: bool = False) -> dict:
        candles = self.candles(symbol, as_of=as_of, limit=8000)
        if len(candles) < 120:
            return {"available": False, "reason": "insufficient-history"}
        cache_key = (
            symbol,
            candles[-1].close_time().isoformat(),
            as_of.isoformat() if as_of else None,
            include_challenger,
        )
        cached = self._metrics_cache.get(cache_key)
        if cached is not None:
            return cached
        report = walk_forward_baselines(candles, horizons=10, min_history=80, step=20)
        cal = walk_forward_probabilities(candles, horizons=10, min_history=80, step=20, as_of=as_of)
        journaled = score_journaled_forecasts(self.journal, symbol, as_of=as_of or candles[-1].close_time())
        qwf: dict[str, Any] = {"horizons": {}, "promotion_allowed": False, "origin_count": 0}
        htf: dict[str, Any] = {"horizons": {}, "promotion_allowed": False, "origin_count": 0}
        if include_challenger:
            backend = os.environ.get("AVAX_QUANTILE_BACKEND", "python")
            if backend not in _QUANTILE_BACKENDS:
                backend = "python"
            try:
                qwf = walk_forward_quantiles(
                    candles,
                    horizons=10,
                    min_history=QUANTILE_WF_MIN_HISTORY,
                    step=QUANTILE_WF_STEP,
                    lookback=QUANTILE_LOOKBACK,
                    backend=backend,
                )
            except Exception:
                qwf = {"horizons": {}, "promotion_allowed": False, "origin_count": 0}
            try:
                htf = walk_forward_htf_regime(
                    candles,
                    horizons=10,
                    min_history=200,
                    step=40,
                )
            except Exception:
                htf = {"horizons": {}, "promotion_allowed": False, "origin_count": 0}
        for key, block in report.get("horizons", {}).items():
            extra = cal["horizons"].get(key, {})
            journal_h = journaled["horizons"].get(key, {})
            block["probability"] = extra.get("probability")
            block["interval"] = extra.get("interval")
            # Prefer journaled Brier/ECE when that sample is large enough; otherwise walk-forward.
            j_prob = journal_h.get("probability") or {}
            if j_prob.get("brier") is not None:
                merged = dict(block.get("probability") or {})
                merged.update(j_prob)
                merged["source"] = "journal"
                block["probability"] = merged
            elif block.get("probability"):
                block["probability"]["source"] = "walk_forward"
            j_live = journal_h.get("probability_held_out_live") or {}
            block["probability_held_out_live"] = {
                **j_live,
                "source": "journal_live",
            }
            j_iv = journal_h.get("interval") or {}
            if j_iv.get("coverage") is not None:
                merged_iv = dict(block.get("interval") or {})
                merged_iv.update(j_iv)
                merged_iv["source"] = "journal"
                block["interval"] = merged_iv
            elif block.get("interval"):
                block["interval"]["source"] = "walk_forward"
            j_d20 = journal_h.get("drift20") or {}
            if j_d20.get("mae") is not None:
                merged_d20 = dict(block.get("drift20") or {})
                merged_d20.update(j_d20)
                merged_d20["source"] = "journal"
                block["drift20"] = merged_d20
                j_zero = journal_h.get("zero") or {}
                if j_zero.get("mae") is not None:
                    merged_zero = dict(block.get("zero") or {})
                    merged_zero.update(j_zero)
                    merged_zero["source"] = "journal"
                    block["zero"] = merged_zero
            elif block.get("drift20"):
                block["drift20"]["source"] = "walk_forward"
            qh = (qwf.get("horizons") or {}).get(key) or {}
            q50 = qh.get("q50")
            if q50 and q50.get("mae") is not None:
                block["q50"] = {**q50, "source": "walk_forward", "sample_count": qh.get("sample_count")}
                block["q50_mae_minus_drift20_mae"] = qh.get("q50_mae_minus_drift20_mae")
            hh = (htf.get("horizons") or {}).get(key) or {}
            htf_row = hh.get("htf_regime")
            if htf_row and htf_row.get("mae") is not None:
                block["htf_regime"] = {**htf_row, "source": "walk_forward", "sample_count": hh.get("sample_count")}
                block["htf_mae_minus_drift20_mae"] = hh.get("htf_mae_minus_drift20_mae")
        report["available"] = True
        report["symbol"] = symbol
        report["probability_calibration_ref"] = cal["calibration_ref"]
        report["interval_ref"] = cal["interval_ref"]
        report["challenger"] = {
            "model_id": qwf.get("model_id"),
            "origin_count": qwf.get("origin_count"),
            "q50_mae_below_drift20_on_all_scored_horizons": qwf.get(
                "q50_mae_below_drift20_on_all_scored_horizons"
            ),
            "notes": qwf.get("notes"),
            "promotion_allowed": False,
        }
        if include_challenger:
            report["challenger"]["htf_regime"] = {
                "id": htf.get("model_id") or "baseline.htf_regime_drift.v1",
                "model_id": htf.get("model_id"),
                "origin_count": htf.get("origin_count"),
                "htf_mae_below_drift20_on_all_scored_horizons": htf.get(
                    "htf_mae_below_drift20_on_all_scored_horizons"
                ),
                "notes": htf.get("notes"),
                "promotion_allowed": False,
            }
        report["promotion_allowed"] = False
        self._metrics_cache[cache_key] = report
        return report

    def health_brief(self, symbol: str = "AVAXUSDT") -> dict:
        source = "fixture" if self.use_fixture else SOURCE
        existing = self.store.load(source, symbol, "5m")
        if not existing:
            if self.use_fixture:
                self._ensure(symbol)
                existing = self.store.load("fixture", symbol, "5m")
            else:
                return {"status": "unknown", "age_seconds": None, "last_close": None, "source": self.source_label}
        last_close = existing[-1].close_time()
        health = freshness(last_close)
        if self.use_fixture:
            health["status"] = "fixture"
        health["source"] = "fixture" if self.use_fixture else SOURCE
        return health

    def market_payload(
        self,
        symbol: str,
        as_of: datetime | None = None,
        chart_limit: int = 1000,
        persist: bool | None = None,
        chart_timeframe: str = DEFAULT_CHART_TF,
    ) -> dict:
        candles = self.candles(symbol, as_of=as_of, limit=max(chart_limit, CHART_SOURCE_LIMIT))
        last_close = candles[-1].close_time()
        should_persist = persist if persist is not None else as_of is None
        snap = self.snapshot(
            symbol, as_of=as_of or last_close, persist_theses=should_persist
        )
        health = freshness(last_close)
        if self.use_fixture:
            health["status"] = "fixture"
        forecast = self.forecast(symbol, as_of=as_of or last_close, persist=should_persist, snap=snap)
        metrics = self.metrics(symbol, as_of=as_of or last_close)
        chart = _chart_rows(candles, chart_limit)
        tf = normalize_chart_tf(chart_timeframe)
        by_tf = _chart_by_timeframe(candles, chart_limit)
        hint = None
        if self.use_fixture:
            from packages.fixtures import bounce_start_index, sept_2026_failed_breakout

            full = sept_2026_failed_breakout(symbol) if symbol == "AVAXUSDT" else []
            if full:
                hint = full[bounce_start_index(full) - 1].close_time().isoformat()
        payload = {
            "symbol": symbol,
            "source": "fixture" if self.use_fixture else SOURCE,
            "as_of": snap.as_of.isoformat(),
            "health": health,
            "last_price": candles[-1].close,
            "snapshot": snap.to_dict(),
            "interpretation": snap.interpretation,
            "forecast": forecast,
            "metrics": metrics,
            "candles": chart,
            "chart_timeframe": tf,
            "chart_candles": by_tf,
            "replay": as_of is not None,
            "replay_hint_as_of": hint,
            "execution_enabled": False,
        }
        return payload


def _origin_stamp(value: datetime | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        stamp = value
    else:
        stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc).replace(microsecond=0).isoformat()


_CHART_EMA_SPANS = (9, 20, 50, 100, 200)


def normalize_chart_tf(raw: str | None) -> str:
    if raw in TIMEFRAMES:
        return raw
    return DEFAULT_CHART_TF


def _chart_by_timeframe(candles_5m, chart_limit: int) -> dict[str, list[dict[str, Any]]]:
    """Resample closed 5m bars already truncated at as_of. Incomplete HTF buckets are dropped."""
    out: dict[str, list[dict[str, Any]]] = {}
    closed = [c for c in candles_5m if getattr(c, "is_closed", True)]
    for tf, minutes in TIMEFRAMES.items():
        series = closed if tf == DEFAULT_CHART_TF else resample_closed(closed, minutes, tf)
        out[tf] = _chart_rows(series, chart_limit)
    return out


def _chart_rows(candles, chart_limit: int) -> list[dict[str, Any]]:
    """OHLCV plus EMA 9/20/50/100/200 from closes known at each bar. Later bars cannot move earlier EMAs."""
    visible = [c for c in candles if getattr(c, "is_closed", True)]
    closes = [c.close for c in visible]
    ema_series = {span: ema(closes, span) if closes else [] for span in _CHART_EMA_SPANS}
    window = visible[-chart_limit:]
    offset = len(visible) - len(window)
    rows: list[dict[str, Any]] = []
    for i, candle in enumerate(window):
        idx = offset + i
        row: dict[str, Any] = {
            "time": int(candle.open_time.timestamp()),
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
        }
        for span, values in ema_series.items():
            if idx < len(values):
                row[f"ema{span}"] = values[idx]
        rows.append(row)
    return rows


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
