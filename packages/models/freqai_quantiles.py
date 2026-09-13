"""Research-only next-10 AVAX 5m quantile forecasts (q10 / q50 / q90).

This is a leakage-safe LightGBM/sklearn-style wrapper, not a live FreqAI trainer
and not a promotion over project baselines. CI may lack LightGBM/sklearn; a
pure-Python empirical residual-quantile fallback is always available.

Constitution constraints honored here:
- only closed candles with period_end <= T are visible
- training origins require the h=10 outcome to be known at or before T
- no random shuffle
- no fabricated ECE / accuracy / baseline-beating claims
- no order execution
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Iterable, Literal, Mapping, Sequence

from adapters.freqtrade.constants import NO_BASELINE_CLAIM, PINNED_COMMIT
from packages.features import assemble_features
from packages.features.schema import FEATURE_SCHEMA_VERSION as MTF_FEATURE_SCHEMA
from packages.features.resample import completed_parents, period_end as feature_period_end

MODEL_ID = "freqai.quantiles.research.v1"
FEATURE_SCHEMA_VERSION = MTF_FEATURE_SCHEMA
PYTHON_FALLBACK_ID = "mtf_ridge_residual_quantiles.v1"
SCHEMA_VERSION = "1"
HORIZONS: tuple[int, ...] = tuple(range(1, 11))
QUANTILES: tuple[float, ...] = (0.1, 0.5, 0.9)
PRIMARY_TIMEFRAME = "5m"
MIN_FEATURE_BARS = 24
DEFAULT_MIN_TRAIN = 30

# Declared pins. CI must not pip-install random wheels for this path.
DECLARED_VERSIONS: dict[str, str] = {
    "model_id": MODEL_ID,
    "feature_schema_version": FEATURE_SCHEMA_VERSION,
    "python_fallback": PYTHON_FALLBACK_ID,
    "scikit-learn": ">=1.5 (optional; skip if missing)",
    "lightgbm": ">=4.5 (optional; skip if missing)",
    "freqtrade_commit": PINNED_COMMIT,
}

PLACEHOLDER_FEATURE_NAMES: tuple[str, ...] = (
    "logret_1",
    "logret_3",
    "logret_12",
    "logret_24",
    "range_pct",
    "body_pct",
    "vol_ratio_12",
    "ema9_dist",
    "ema20_dist",
    "realized_vol_12",
    "htf_15m_logret_1",
    "htf_1h_logret_1",
)
FEATURE_NAMES = PLACEHOLDER_FEATURE_NAMES
MODEL_FEATURE_NAMES: tuple[str, ...] = (
    "avax_5m_logret_1",
    "avax_5m_logret_3",
    "avax_5m_logret_12",
    "avax_5m_logret_24",
    "avax_5m_realized_vol_24",
    "avax_5m_atr14_pct",
    "avax_5m_rsi14_centered",
    "avax_5m_ema20_dist",
    "avax_5m_ema50_dist",
    "avax_5m_ema_stack_score",
    "avax_15m_logret_1",
    "avax_1h_logret_1",
    "avax_4h_logret_1",
    "avax_1d_logret_1",
    "btc_5m_logret_1",
    "btc_5m_logret_12",
    "rel_avax_btc_logret_12",
    "rel_avax_btc_corr_24",
)

BackendName = Literal["auto", "lightgbm", "sklearn", "python"]

NO_PERFORMANCE_CLAIM = (
    "Research-only quantile payload. Not scored against baselines here. "
    "No fabricated confidence percentage or interval-coverage number is attached."
)


class InsufficientHistory(ValueError):
    """Raised when a point-in-time window cannot legally emit a forecast."""


def _aware(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


def candle_period_end(candle: Any) -> datetime:
    timeframe = getattr(candle, "timeframe", PRIMARY_TIMEFRAME)
    closer = getattr(candle, "close_time", None)
    if callable(closer):
        return _aware(closer(), field_name="period_end")
    return feature_period_end(candle.open_time, timeframe)


def is_closed_known(candle: Any, as_of: datetime) -> bool:
    if not bool(getattr(candle, "is_closed", True)):
        return False
    return candle_period_end(candle) <= as_of


def visible_closed_candles(candles: Sequence[Any], as_of: datetime) -> list[Any]:
    cutoff = _aware(as_of, field_name="as_of")
    visible = [
        c
        for c in candles
        if is_closed_known(c, cutoff) and getattr(c, "timeframe", PRIMARY_TIMEFRAME) == PRIMARY_TIMEFRAME
    ]
    visible.sort(key=lambda c: c.open_time)
    return visible


def _log_return(later: float, now: float) -> float | None:
    if later <= 0 or now <= 0:
        return None
    return math.log(later / now)


def _ema(values: Sequence[float], span: int) -> float:
    if not values:
        return 0.0
    alpha = 2.0 / (span + 1.0)
    current = float(values[0])
    for value in values[1:]:
        current = alpha * float(value) + (1.0 - alpha) * current
    return current


def _realized_vol(closes: Sequence[float], window: int) -> float:
    if len(closes) < window + 1:
        return 0.0
    rets = []
    start = len(closes) - window
    for i in range(start, len(closes)):
        prev, cur = closes[i - 1], closes[i]
        if prev <= 0 or cur <= 0:
            continue
        rets.append(math.log(cur / prev))
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((x - mean) ** 2 for x in rets) / len(rets)
    return math.sqrt(var)


def _finite(value: float | None) -> float:
    if value is None or not math.isfinite(value):
        return 0.0
    return float(value)


def extract_features_at(candles: Sequence[Any], as_of: datetime) -> dict[str, float]:
    """Point-in-time feature row. Unfinished parents never enter HTF slots."""
    cutoff = _aware(as_of, field_name="as_of")
    visible = visible_closed_candles(candles, cutoff)
    if len(visible) < 2:
        raise InsufficientHistory("need at least two closed candles at as_of")

    closes = [float(c.close) for c in visible]
    last = visible[-1]

    def lookback_return(bars: int) -> float:
        if len(closes) <= bars:
            return 0.0
        return _finite(_log_return(closes[-1], closes[-1 - bars]))

    range_pct = (float(last.high) - float(last.low)) / float(last.close) if last.close else 0.0
    body_pct = abs(float(last.close) - float(last.open)) / float(last.open) if last.open else 0.0
    volumes = [float(c.volume) for c in visible]
    if len(volumes) >= 12:
        mean_v = sum(volumes[-12:]) / 12.0
        vol_ratio = volumes[-1] / mean_v if mean_v else 0.0
    else:
        vol_ratio = 0.0

    ema9 = _ema(closes, 9)
    ema20 = _ema(closes, 20)
    close = float(last.close)
    ema9_dist = (close - ema9) / close if close else 0.0
    ema20_dist = (close - ema20) / close if close else 0.0

    parents_15 = completed_parents(visible, cutoff, "15m")
    parents_1h = completed_parents(visible, cutoff, "1h")
    htf_15 = 0.0
    if len(parents_15) >= 2:
        htf_15 = _finite(_log_return(float(parents_15[-1].close), float(parents_15[-2].close)))
    htf_1h = 0.0
    if len(parents_1h) >= 2:
        htf_1h = _finite(_log_return(float(parents_1h[-1].close), float(parents_1h[-2].close)))

    return {
        "logret_1": lookback_return(1),
        "logret_3": lookback_return(3),
        "logret_12": lookback_return(12),
        "logret_24": lookback_return(24),
        "range_pct": _finite(range_pct),
        "body_pct": _finite(body_pct),
        "vol_ratio_12": _finite(vol_ratio),
        "ema9_dist": _finite(ema9_dist),
        "ema20_dist": _finite(ema20_dist),
        "realized_vol_12": _realized_vol(closes, 12),
        "htf_15m_logret_1": htf_15,
        "htf_1h_logret_1": htf_1h,
    }


def feature_vector(features: Mapping[str, float]) -> list[float]:
    return [_finite(features[name]) for name in FEATURE_NAMES]


def availability_at(candles: Sequence[Any], as_of: datetime) -> dict[str, str | None]:
    cutoff = _aware(as_of, field_name="as_of")
    visible = visible_closed_candles(candles, cutoff)
    parents_15 = completed_parents(visible, cutoff, "15m")
    parents_1h = completed_parents(visible, cutoff, "1h")
    last_5m = candle_period_end(visible[-1]) if visible else None
    last_15 = candle_period_end(parents_15[-1]) if parents_15 else None
    last_1h = candle_period_end(parents_1h[-1]) if parents_1h else None
    return {
        "avax_5m_known_at": last_5m.isoformat() if last_5m else None,
        "avax_15m_known_at": last_15.isoformat() if last_15 else None,
        "avax_1h_known_at": last_1h.isoformat() if last_1h else None,
        "avax_15m_last_open_time": parents_15[-1].open_time.isoformat() if parents_15 else None,
        "avax_1h_last_open_time": parents_1h[-1].open_time.isoformat() if parents_1h else None,
    }


def eligible_train_indices(
    visible: Sequence[Any],
    as_of: datetime,
    *,
    horizons: int = 10,
    min_feature_bars: int = MIN_FEATURE_BARS,
) -> list[int]:
    """Origins whose full outcome horizon is known at or before ``as_of``."""
    cutoff = _aware(as_of, field_name="as_of")
    out: list[int] = []
    if horizons < 1:
        raise ValueError("horizons must be >= 1")
    last_origin = len(visible) - horizons - 1
    first_origin = min_feature_bars - 1
    for index in range(max(0, first_origin), max(-1, last_origin) + 1):
        outcome = visible[index + horizons]
        if candle_period_end(outcome) <= cutoff:
            out.append(index)
    return out


def _target_log_return(visible: Sequence[Any], origin: int, horizon: int) -> float:
    now = float(visible[origin].close)
    later = float(visible[origin + horizon].close)
    value = _log_return(later, now)
    if value is None:
        raise InsufficientHistory("non-positive close in training target")
    return value


def empirical_quantile(values: Sequence[float], quantile: float) -> float:
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must be in [0, 1]")
    if not values:
        return 0.0
    ordered = sorted(float(x) for x in values)
    if len(ordered) == 1:
        return ordered[0]
    position = quantile * (len(ordered) - 1)
    low = int(math.floor(position))
    high = min(low + 1, len(ordered) - 1)
    frac = position - low
    return ordered[low] * (1.0 - frac) + ordered[high] * frac


def _enforce_order(q10: float, q50: float, q90: float) -> tuple[float, float, float]:
    ordered = sorted((float(q10), float(q50), float(q90)))
    return ordered[0], ordered[1], ordered[2]


def detect_backend(requested: BackendName) -> str:
    if requested == "python":
        return "python"
    if requested in {"auto", "lightgbm"}:
        try:
            import lightgbm  # noqa: F401
        except Exception:
            if requested == "lightgbm":
                return "python"
        else:
            return "lightgbm"
    if requested in {"auto", "sklearn"}:
        try:
            import sklearn.ensemble  # noqa: F401
        except Exception:
            return "python"
        return "sklearn"
    return "python"


def _drift20(closes: Sequence[float]) -> float:
    if len(closes) < 21:
        return 0.0
    past = [_log_return(closes[j], closes[j - 1]) or 0.0 for j in range(len(closes) - 19, len(closes))]
    return sum(past) / len(past)


def _mtf_model_row(
    avax: Sequence[Any],
    as_of: datetime,
    btc: Sequence[Any] | None = None,
    eth: Sequence[Any] | None = None,
) -> list[float]:
    snapshot = assemble_features(avax, as_of=as_of, btc_5m=btc or None, eth_5m=eth or None)
    values = snapshot.values
    row: list[float] = []
    for name in MODEL_FEATURE_NAMES:
        raw = values.get(name)
        row.append(0.0 if raw is None or not math.isfinite(float(raw)) else float(raw))
    return row


def _visible_cross(candles: Sequence[Any] | None, as_of: datetime) -> list[Any]:
    if not candles:
        return []
    return visible_closed_candles(candles, as_of)


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _solve_linear(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    n = len(rhs)
    aug = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            aug[col][col] = 1e-12
        else:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= scale
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]
    return [aug[i][n] for i in range(n)]


def _ridge_fit(x_rows: Sequence[Sequence[float]], y: Sequence[float], l2: float = 1.0) -> list[float]:
    if not x_rows:
        return [0.0]
    dim = len(x_rows[0]) + 1
    xtx = [[0.0] * dim for _ in range(dim)]
    xty = [0.0] * dim
    for row, target in zip(x_rows, y):
        z = [1.0, *row]
        for i in range(dim):
            xty[i] += z[i] * float(target)
            for j in range(dim):
                xtx[i][j] += z[i] * z[j]
    for j in range(1, dim):
        xtx[j][j] += l2
    return _solve_linear(xtx, xty)


def _ridge_predict(weights: Sequence[float], x_row: Sequence[float]) -> float:
    return float(weights[0]) + _dot(weights[1:], x_row)


def _fit_python(
    train_targets: dict[int, list[float]],
    x_rows: Sequence[Sequence[float]],
    drift20s: Sequence[float],
) -> dict[str, Any]:
    """q50 may use MTF ridge; q10/q90 width is residual vs drift20, not in-sample leftover."""
    weights: dict[int, list[float]] = {}
    spread: dict[int, dict[float, float]] = {}
    for horizon, ys in train_targets.items():
        loc = [float(drift) * horizon for drift in drift20s]
        resid = [y - loc[i] for i, y in enumerate(ys)]
        weights[horizon] = _ridge_fit(x_rows, resid, l2=8.0)
        spread[horizon] = {q: empirical_quantile(resid, q) for q in QUANTILES}
    return {"weights": weights, "spread": spread}


def _predict_python(
    model: Mapping[str, Any],
    x_row: Sequence[float],
    current_drift20: float,
) -> dict[int, tuple[float, float, float]]:
    out: dict[int, tuple[float, float, float]] = {}
    for horizon in HORIZONS:
        loc = float(current_drift20) * horizon + _ridge_predict(model["weights"][horizon], x_row)
        spread = model["spread"][horizon]
        out[horizon] = _enforce_order(loc + spread[0.1], loc + spread[0.5], loc + spread[0.9])
    return out


def _standardize_fit(rows: Sequence[Sequence[float]]) -> tuple[list[float], list[float]]:
    cols = len(rows[0])
    means = [0.0] * cols
    scales = [1.0] * cols
    n = float(len(rows))
    for j in range(cols):
        col = [row[j] for row in rows]
        mean = sum(col) / n
        var = sum((x - mean) ** 2 for x in col) / n
        means[j] = mean
        scales[j] = math.sqrt(var) if var > 1e-18 else 1.0
    return means, scales


def _standardize_apply(
    rows: Sequence[Sequence[float]], means: Sequence[float], scales: Sequence[float]
) -> list[list[float]]:
    return [[(value - means[j]) / scales[j] for j, value in enumerate(row)] for row in rows]


def _fit_lightgbm(x_train: Sequence[Sequence[float]], train_targets: dict[int, list[float]]) -> dict[str, Any]:
    from lightgbm import LGBMRegressor

    models: dict[tuple[int, float], Any] = {}
    for horizon, ys in train_targets.items():
        for quantile in QUANTILES:
            model = LGBMRegressor(
                objective="quantile",
                alpha=quantile,
                n_estimators=40,
                learning_rate=0.08,
                min_child_samples=8,
                subsample=1.0,
                colsample_bytree=1.0,
                verbosity=-1,
                random_state=0,
                n_jobs=1,
            )
            model.fit(x_train, ys)
            models[(horizon, quantile)] = model
    return {"models": models}


def _fit_sklearn(x_train: Sequence[Sequence[float]], train_targets: dict[int, list[float]]) -> dict[str, Any]:
    from sklearn.ensemble import GradientBoostingRegressor

    models: dict[tuple[int, float], Any] = {}
    for horizon, ys in train_targets.items():
        for quantile in QUANTILES:
            model = GradientBoostingRegressor(
                loss="quantile",
                alpha=quantile,
                n_estimators=30,
                max_depth=2,
                learning_rate=0.08,
                random_state=0,
            )
            model.fit(x_train, ys)
            models[(horizon, quantile)] = model
    return {"models": models}


def _predict_tree(model_bundle: Mapping[str, Any], x_row: Sequence[float]) -> dict[int, tuple[float, float, float]]:
    models = model_bundle["models"]
    out: dict[int, tuple[float, float, float]] = {}
    for horizon in HORIZONS:
        q10 = float(models[(horizon, 0.1)].predict([x_row])[0])
        q50 = float(models[(horizon, 0.5)].predict([x_row])[0])
        q90 = float(models[(horizon, 0.9)].predict([x_row])[0])
        out[horizon] = _enforce_order(q10, q50, q90)
    return out


def _iso(value: datetime) -> str:
    return _aware(value, field_name="datetime").isoformat()


def emit_quantile_forecast(
    candles: Sequence[Any],
    as_of: datetime | None = None,
    *,
    backend: BackendName = "auto",
    min_train: int = DEFAULT_MIN_TRAIN,
    min_feature_bars: int = MIN_FEATURE_BARS,
    symbol: str | None = None,
    btc_5m: Sequence[Any] | None = None,
    eth_5m: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Emit a journal-ready ForecastPackage-shaped payload. Does not trade."""
    if as_of is None:
        closed = [c for c in candles if bool(getattr(c, "is_closed", True))]
        if not closed:
            raise InsufficientHistory("no closed candles")
        as_of = max(candle_period_end(c) for c in closed)
    cutoff = _aware(as_of, field_name="as_of")
    visible = visible_closed_candles(candles, cutoff)
    if len(visible) < min_feature_bars + max(HORIZONS) + 1:
        raise InsufficientHistory(
            f"need at least {min_feature_bars + max(HORIZONS) + 1} closed candles at as_of"
        )

    origins = eligible_train_indices(
        visible, cutoff, horizons=max(HORIZONS), min_feature_bars=min_feature_bars
    )
    if len(origins) < min_train:
        raise InsufficientHistory(
            f"need at least {min_train} train origins with matured h=10 labels; got {len(origins)}"
        )

    x_rows: list[list[float]] = []
    drift20s: list[float] = []
    train_targets: dict[int, list[float]] = {h: [] for h in HORIZONS}
    for origin in origins:
        origin_t = candle_period_end(visible[origin])
        prefix = visible[: origin + 1]
        try:
            row = _mtf_model_row(
                prefix,
                origin_t,
                _visible_cross(btc_5m, origin_t),
                _visible_cross(eth_5m, origin_t),
            )
        except Exception:
            continue
        x_rows.append(row)
        drift20s.append(_drift20([float(c.close) for c in prefix]))
        for horizon in HORIZONS:
            train_targets[horizon].append(_target_log_return(visible, origin, horizon))
    if len(x_rows) < min_train:
        raise InsufficientHistory(
            f"need at least {min_train} MTF train rows; got {len(x_rows)}"
        )

    chosen = detect_backend(backend)
    fitted: dict[str, Any] | None = None
    used = "python"
    if chosen == "lightgbm":
        try:
            means, scales = _standardize_fit(x_rows)
            fitted = _fit_lightgbm(_standardize_apply(x_rows, means, scales), train_targets)
            fitted["means"] = means
            fitted["scales"] = scales
            used = "lightgbm"
        except Exception:
            fitted = None
    if fitted is None and chosen in {"sklearn", "lightgbm", "auto"} and backend != "python":
        if detect_backend("sklearn") == "sklearn":
            try:
                means, scales = _standardize_fit(x_rows)
                fitted = _fit_sklearn(_standardize_apply(x_rows, means, scales), train_targets)
                fitted["means"] = means
                fitted["scales"] = scales
                used = "sklearn"
            except Exception:
                fitted = None
    if fitted is None or used == "python":
        fitted = _fit_python(train_targets, x_rows, drift20s)
        used = "python"

    current_vector = _mtf_model_row(
        visible,
        cutoff,
        _visible_cross(btc_5m, cutoff),
        _visible_cross(eth_5m, cutoff),
    )
    current_drift20 = _drift20([float(c.close) for c in visible])
    if used == "python":
        bands = _predict_python(fitted, current_vector, current_drift20)
    else:
        scaled = _standardize_apply([current_vector], fitted["means"], fitted["scales"])[0]
        bands = _predict_tree(fitted, scaled)

    origin = visible[-1]
    forecasted_at = candle_period_end(origin)
    origin_close = float(origin.close)
    resolved_symbol = symbol or getattr(origin, "symbol", "AVAXUSDT")
    horizons_out = []
    for horizon in HORIZONS:
        q10, q50, q90 = bands[horizon]
        horizons_out.append(
            attach_simple_return_aliases(
                {
                    "h": horizon,
                    "expected_cum_log_return": q50,
                    "q10_cum_log_return": q10,
                    "q50_cum_log_return": q50,
                    "q90_cum_log_return": q90,
                    "p_close_above_origin": None,
                    "expected_max_favorable_excursion": None,
                    "expected_max_adverse_excursion": None,
                    "zone_touch_probabilities": {},
                }
            )
        )

    payload = {
        "id": f"{MODEL_ID}:{resolved_symbol}:{_iso(forecasted_at)}",
        "schema_version": SCHEMA_VERSION,
        "symbol": resolved_symbol,
        "base_timeframe": PRIMARY_TIMEFRAME,
        "forecasted_at": _iso(forecasted_at),
        "created_at": _iso(forecasted_at),
        "origin_close": origin_close,
        "origin_open_time": _iso(origin.open_time),
        "context_snapshot_id": None,
        "feature_snapshot_id": None,
        "model_ensemble_id": MODEL_ID,
        "model_id": MODEL_ID,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "data_manifest_id": None,
        "source_data_hash": None,
        "application_commit": None,
        "upstream_freqtrade_commit": PINNED_COMMIT,
        "horizons": horizons_out,
        "component_models": [
            {
                "model_id": MODEL_ID,
                "backend": used,
                "role": "quantile",
                "feature_schema_version": FEATURE_SCHEMA_VERSION,
            }
        ],
        "calibration_ref": None,
        "health": "valid",
        "research_only": True,
        "live_trading": False,
        "dry_run": True,
        "max_open_trades": 0,
        "stake_amount": 0,
        "freqai_beats_baselines": None,
        "performance_claim": NO_PERFORMANCE_CLAIM,
        "baseline_claim": NO_BASELINE_CLAIM,
        "backend": used,
        "train_origin_count": len(x_rows),
        "python_fallback": PYTHON_FALLBACK_ID,
        "model_feature_names": list(MODEL_FEATURE_NAMES),
        "declared_versions": dict(DECLARED_VERSIONS),
        "availability": availability_at(visible, cutoff),
        "notes": (
            "Journal-ready research payload for horizons h=1..10 using "
            f"{FEATURE_SCHEMA_VERSION}. Watcher may append this before outcomes exist. No live orders."
        ),
    }
    return payload


def attach_simple_return_aliases(horizon: dict[str, Any]) -> dict[str, Any]:
    """ForecastFan draws q10/q50/q90_cum_return (simple). Quantiles are log returns."""
    pairs = (
        ("q10_cum_log_return", "q10_cum_return"),
        ("q50_cum_log_return", "q50_cum_return"),
        ("q90_cum_log_return", "q90_cum_return"),
        ("expected_cum_log_return", "expected_cum_return"),
    )
    for log_key, simple_key in pairs:
        raw = horizon.get(log_key)
        if raw is None or horizon.get(simple_key) is not None:
            continue
        horizon[simple_key] = math.exp(float(raw)) - 1.0
    return horizon


def attach_simple_return_aliases_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for row in payload.get("horizons") or []:
        if isinstance(row, dict):
            attach_simple_return_aliases(row)
    return payload


def assert_quantile_order(payload: Mapping[str, Any]) -> None:
    rows = payload.get("horizons") or []
    if len(rows) != 10:
        raise ValueError("payload must contain horizons h=1..10")
    seen: set[int] = set()
    for row in rows:
        horizon = int(row["h"])
        seen.add(horizon)
        q10 = float(row["q10_cum_log_return"])
        q50 = float(row["q50_cum_log_return"])
        q90 = float(row["q90_cum_log_return"])
        if not (q10 <= q50 <= q90):
            raise ValueError(f"crossed quantiles at h={horizon}")
    if seen != set(HORIZONS):
        raise ValueError("payload horizons must be exactly 1..10")


def iter_horizon_pairs(payload: Mapping[str, Any]) -> Iterable[tuple[int, float, float, float]]:
    for row in payload["horizons"]:
        yield (
            int(row["h"]),
            float(row["q10_cum_log_return"]),
            float(row["q50_cum_log_return"]),
            float(row["q90_cum_log_return"]),
        )
