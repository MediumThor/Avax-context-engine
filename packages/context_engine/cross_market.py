"""Timestamp-aligned BTC/ETH/AVAX cross-market context.

Constitution §5: features at T may use only closes known at T.
A missing candle is ``unknown``. This module does not interpolate,
forward-fill, or join non-adjacent bars as if they were consecutive.

BTC is the mandatory reference. ETH and a native AVAXBTC series are
optional. This module does not execute trades.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from math import log, sqrt
from typing import Literal, Mapping, Sequence

from .models import Candle

SCHEMA_VERSION = "avax.cross_market.v1"
DEFAULT_WINDOW = 24
DEFAULT_SYNC_ABS_LOGRET = 0.001
VOL_EXPAND_MULT = 1.5
VOL_COMPRESS_MULT = 0.75
REGIME_ABS_LOGRET = 0.005

TIMEFRAME_MINUTES: Mapping[str, int] = {
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
}

Health = Literal["valid", "degraded", "unknown"]
MoveFlag = Literal[
    "synchronized_breakout",
    "synchronized_breakdown",
    "decoupled",
    "quiet",
    "unknown",
]
VolRegime = Literal["compressed", "normal", "expanded", "unknown"]
ReturnRegime = Literal["bullish", "bearish", "neutral", "unknown"]


class CrossMarketError(ValueError):
    """Invalid cross-market inputs (naive timestamps, bad window, mixed TF)."""


def _require_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None:
        raise CrossMarketError(f"{name} must be timezone-aware")


def log_return(close_now: float, close_prev: float) -> float | None:
    if close_now <= 0 or close_prev <= 0:
        return None
    return log(close_now / close_prev)


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0.0 or var_y == 0.0:
        return None
    cov = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    return cov / sqrt(var_x * var_y)


def ols_beta(dependent: Sequence[float], factor: Sequence[float]) -> float | None:
    n = len(dependent)
    if n < 3 or n != len(factor):
        return None
    mean_y = sum(dependent) / n
    mean_x = sum(factor) / n
    var_x = sum((x - mean_x) ** 2 for x in factor)
    if var_x == 0.0:
        return None
    cov = sum((dependent[i] - mean_y) * (factor[i] - mean_x) for i in range(n))
    return cov / var_x


def classify_move(
    focal_logret: float | None,
    reference_logret: float | None,
    sync_abs_logret: float = DEFAULT_SYNC_ABS_LOGRET,
) -> MoveFlag:
    if focal_logret is None or reference_logret is None:
        return "unknown"
    if abs(focal_logret) < sync_abs_logret or abs(reference_logret) < sync_abs_logret:
        return "quiet"
    same_sign = (focal_logret > 0) == (reference_logret > 0)
    if same_sign and focal_logret > 0:
        return "synchronized_breakout"
    if same_sign and focal_logret < 0:
        return "synchronized_breakdown"
    return "decoupled"


def bar_step(timeframe: str) -> timedelta:
    try:
        minutes = TIMEFRAME_MINUTES[timeframe]
    except KeyError as exc:
        raise CrossMarketError(f"unsupported timeframe: {timeframe}") from exc
    return timedelta(minutes=minutes)


def expected_stamps(as_of: datetime, count: int, step: timedelta) -> list[datetime]:
    """Oldest-first exact grid ``[as_of-(count-1)*step, ..., as_of]``."""
    if count < 1:
        raise CrossMarketError("count must be >= 1")
    return [as_of - step * offset for offset in range(count - 1, -1, -1)]


def _known_closed(candles: Sequence[Candle], as_of: datetime) -> dict[datetime, Candle]:
    """Index closed candles whose ``open_time`` is at or before ``as_of``.

    Duplicate timestamps keep the last closed print. Missing timestamps are
    absent from the map — callers must not invent them.
    """
    out: dict[datetime, Candle] = {}
    timeframe: str | None = None
    for candle in candles:
        _require_aware("Candle.open_time", candle.open_time)
        if not candle.is_closed:
            continue
        if candle.open_time > as_of:
            continue
        if timeframe is None:
            timeframe = candle.timeframe
        elif candle.timeframe != timeframe:
            raise CrossMarketError("mixed timeframes in one series")
        out[candle.open_time] = candle
    return out


def _last_stamp(index: Mapping[datetime, Candle], as_of: datetime) -> datetime | None:
    stamps = [stamp for stamp in index if stamp <= as_of]
    if not stamps:
        return None
    return max(stamps)


def _window_logret(index: Mapping[datetime, Candle], start: datetime, end: datetime) -> float | None:
    if start not in index or end not in index:
        return None
    return log_return(index[end].close, index[start].close)


def _consecutive_logrets(
    index: Mapping[datetime, Candle],
    stamps: Sequence[datetime],
) -> list[float] | None:
    if any(stamp not in index for stamp in stamps):
        return None
    out: list[float] = []
    for i in range(1, len(stamps)):
        value = log_return(index[stamps[i]].close, index[stamps[i - 1]].close)
        if value is None:
            return None
        out.append(value)
    return out


@dataclass(frozen=True, slots=True)
class PairState:
    focal: str
    reference: str
    as_of: datetime
    known_at: datetime
    health: Health
    log_return_focal: float | None
    log_return_reference: float | None
    relative_strength: float | None
    relative_strength_window: float | None
    correlation: float | None
    beta: float | None
    move_flag: MoveFlag
    evidence: tuple[str, ...]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["as_of"] = self.as_of.isoformat()
        payload["known_at"] = self.known_at.isoformat()
        payload["evidence"] = list(self.evidence)
        return payload


@dataclass(frozen=True, slots=True)
class CrossMarketState:
    as_of: datetime
    known_at: datetime
    timeframe: str
    window: int
    health: Health
    avax_btc: PairState
    avax_eth: PairState
    eth_btc: PairState
    avaxbtc_log_return: float | None
    btc_regime: ReturnRegime
    btc_volatility: VolRegime
    btc_realized_vol: float | None
    synchronized_breakout: bool | None
    synchronized_breakdown: bool | None
    decoupled: bool | None
    evidence: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "as_of": self.as_of.isoformat(),
            "known_at": self.known_at.isoformat(),
            "timeframe": self.timeframe,
            "window": self.window,
            "health": self.health,
            "avax_btc": self.avax_btc.to_dict(),
            "avax_eth": self.avax_eth.to_dict(),
            "eth_btc": self.eth_btc.to_dict(),
            "avaxbtc_log_return": self.avaxbtc_log_return,
            "btc_regime": self.btc_regime,
            "btc_volatility": self.btc_volatility,
            "btc_realized_vol": self.btc_realized_vol,
            "synchronized_breakout": self.synchronized_breakout,
            "synchronized_breakdown": self.synchronized_breakdown,
            "decoupled": self.decoupled,
            "evidence": list(self.evidence),
        }


def _unknown_pair(
    focal: str,
    reference: str,
    as_of: datetime,
    known_at: datetime,
    reason: str,
) -> PairState:
    return PairState(
        focal=focal,
        reference=reference,
        as_of=as_of,
        known_at=known_at,
        health="unknown",
        log_return_focal=None,
        log_return_reference=None,
        relative_strength=None,
        relative_strength_window=None,
        correlation=None,
        beta=None,
        move_flag="unknown",
        evidence=(reason,),
    )


def pair_state(
    focal: Mapping[datetime, Candle],
    reference: Mapping[datetime, Candle],
    *,
    eval_ts: datetime,
    step: timedelta,
    window: int,
    sync_abs_logret: float,
    focal_symbol: str,
    reference_symbol: str,
) -> PairState:
    """Pair metrics at ``eval_ts`` using exact timestamp alignment only."""
    if eval_ts not in focal or eval_ts not in reference:
        return _unknown_pair(
            focal_symbol,
            reference_symbol,
            eval_ts,
            eval_ts,
            "missing_aligned_candle",
        )

    prev = eval_ts - step
    one_bar_ok = prev in focal and prev in reference
    log_focal = log_return(focal[eval_ts].close, focal[prev].close) if one_bar_ok else None
    log_ref = log_return(reference[eval_ts].close, reference[prev].close) if one_bar_ok else None
    if not one_bar_ok:
        rs_1 = None
        move = "unknown"
        one_bar_reason = "missing_prior_aligned_candle"
    elif log_focal is None or log_ref is None:
        rs_1 = None
        move = "unknown"
        one_bar_reason = "non_positive_close"
    else:
        rs_1 = log_focal - log_ref
        move = classify_move(log_focal, log_ref, sync_abs_logret)
        one_bar_reason = None

    start = eval_ts - step * window
    focal_w = _window_logret(focal, start, eval_ts)
    ref_w = _window_logret(reference, start, eval_ts)
    rs_w = None if focal_w is None or ref_w is None else focal_w - ref_w

    stamps = expected_stamps(eval_ts, window + 1, step)
    focal_rets = _consecutive_logrets(focal, stamps)
    ref_rets = _consecutive_logrets(reference, stamps)
    if focal_rets is None or ref_rets is None:
        corr = None
        beta = None
        window_reason = "gap_or_short_window"
    else:
        corr = pearson(focal_rets, ref_rets)
        beta = ols_beta(focal_rets, ref_rets)
        window_reason = None if corr is not None and beta is not None else "undefined_corr_or_beta"

    if one_bar_reason is not None:
        health: Health = "unknown"
    elif window_reason is not None:
        health = "degraded"
    else:
        health = "valid"

    evidence: list[str] = []
    if one_bar_reason:
        evidence.append(one_bar_reason)
    if window_reason:
        evidence.append(window_reason)
    if move != "unknown" and move != "quiet":
        evidence.append(f"{focal_symbol}_{reference_symbol}_{move}")
    if rs_1 is not None and abs(rs_1) >= sync_abs_logret:
        evidence.append("relative_strength_nonzero")

    return PairState(
        focal=focal_symbol,
        reference=reference_symbol,
        as_of=eval_ts,
        known_at=eval_ts,
        health=health,
        log_return_focal=log_focal,
        log_return_reference=log_ref,
        relative_strength=rs_1,
        relative_strength_window=rs_w,
        correlation=corr,
        beta=beta,
        move_flag=move,
        evidence=tuple(evidence),
    )


def _realized_vol(returns: Sequence[float]) -> float | None:
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / len(returns)
    return sqrt(variance)


def _btc_vol_regime(
    btc: Mapping[datetime, Candle],
    eval_ts: datetime,
    step: timedelta,
    window: int,
) -> tuple[VolRegime, float | None, tuple[str, ...]]:
    recent_stamps = expected_stamps(eval_ts, window + 1, step)
    recent = _consecutive_logrets(btc, recent_stamps)
    vol = _realized_vol(recent) if recent is not None else None
    if recent is None or vol is None:
        return "unknown", None, ("btc_vol_gap_or_short",)

    baseline_end = eval_ts - step * window
    baseline_stamps = expected_stamps(baseline_end, window + 1, step)
    baseline_rets = _consecutive_logrets(btc, baseline_stamps)
    baseline = _realized_vol(baseline_rets) if baseline_rets is not None else None
    if baseline is None or baseline == 0.0:
        return "unknown", vol, ("btc_vol_no_baseline",)

    if vol > baseline * VOL_EXPAND_MULT:
        return "expanded", vol, ("btc_volatility_expanded",)
    if vol < baseline * VOL_COMPRESS_MULT:
        return "compressed", vol, ("btc_volatility_compressed",)
    return "normal", vol, ("btc_volatility_normal",)


def _btc_regime(
    btc: Mapping[datetime, Candle],
    eval_ts: datetime,
    step: timedelta,
    window: int,
) -> ReturnRegime:
    start = eval_ts - step * window
    value = _window_logret(btc, start, eval_ts)
    if value is None:
        return "unknown"
    if value > REGIME_ABS_LOGRET:
        return "bullish"
    if value < -REGIME_ABS_LOGRET:
        return "bearish"
    return "neutral"


def _native_avaxbtc_logret(
    avaxbtc: Mapping[datetime, Candle],
    eval_ts: datetime,
    step: timedelta,
) -> float | None:
    prev = eval_ts - step
    if eval_ts not in avaxbtc or prev not in avaxbtc:
        return None
    return log_return(avaxbtc[eval_ts].close, avaxbtc[prev].close)


def _flag_bool(move: MoveFlag, target: MoveFlag) -> bool | None:
    if move == "unknown":
        return None
    return move == target


def build_cross_market(
    avax: Sequence[Candle],
    btc: Sequence[Candle],
    eth: Sequence[Candle] | None = None,
    avaxbtc: Sequence[Candle] | None = None,
    *,
    as_of: datetime,
    window: int = DEFAULT_WINDOW,
    sync_abs_logret: float = DEFAULT_SYNC_ABS_LOGRET,
) -> CrossMarketState:
    """Build leakage-safe cross-market state at ``as_of``.

    Alignment is exact on ``open_time``. A missing candle on any required
    leg marks the dependent feature unknown. Future and unclosed bars are
    ignored. No interpolation.
    """
    _require_aware("as_of", as_of)
    if window < 3:
        raise CrossMarketError("window must be >= 3")
    if sync_abs_logret <= 0:
        raise CrossMarketError("sync_abs_logret must be > 0")

    avax_idx = _known_closed(avax, as_of)
    btc_idx = _known_closed(btc, as_of)
    eth_idx = _known_closed(eth or (), as_of)
    avaxbtc_idx = _known_closed(avaxbtc or (), as_of)

    eval_ts = _last_stamp(avax_idx, as_of)
    if eval_ts is None:
        empty_at = as_of
        unknown = _unknown_pair("AVAXUSDT", "BTCUSDT", as_of, empty_at, "no_closed_avax")
        empty_eth = _unknown_pair("AVAXUSDT", "ETHUSDT", as_of, empty_at, "no_closed_avax")
        empty_eth_btc = _unknown_pair("ETHUSDT", "BTCUSDT", as_of, empty_at, "no_closed_avax")
        return CrossMarketState(
            as_of=as_of,
            known_at=empty_at,
            timeframe="unknown",
            window=window,
            health="unknown",
            avax_btc=unknown,
            avax_eth=empty_eth,
            eth_btc=empty_eth_btc,
            avaxbtc_log_return=None,
            btc_regime="unknown",
            btc_volatility="unknown",
            btc_realized_vol=None,
            synchronized_breakout=None,
            synchronized_breakdown=None,
            decoupled=None,
            evidence=("no_closed_avax",),
        )

    sample = avax_idx[eval_ts]
    step = bar_step(sample.timeframe)
    avax_symbol = sample.symbol or "AVAXUSDT"
    btc_symbol = next(iter(btc_idx.values())).symbol if btc_idx else "BTCUSDT"
    eth_symbol = next(iter(eth_idx.values())).symbol if eth_idx else "ETHUSDT"

    avax_btc = pair_state(
        avax_idx,
        btc_idx,
        eval_ts=eval_ts,
        step=step,
        window=window,
        sync_abs_logret=sync_abs_logret,
        focal_symbol=avax_symbol,
        reference_symbol=btc_symbol,
    )
    avax_eth = pair_state(
        avax_idx,
        eth_idx,
        eval_ts=eval_ts,
        step=step,
        window=window,
        sync_abs_logret=sync_abs_logret,
        focal_symbol=avax_symbol,
        reference_symbol=eth_symbol,
    )
    eth_btc = pair_state(
        eth_idx,
        btc_idx,
        eval_ts=eval_ts,
        step=step,
        window=window,
        sync_abs_logret=sync_abs_logret,
        focal_symbol=eth_symbol,
        reference_symbol=btc_symbol,
    )

    if eval_ts not in btc_idx:
        # Do not mix a lagged BTC print with AVAX at eval_ts.
        btc_regime: ReturnRegime = "unknown"
        btc_vol: VolRegime = "unknown"
        btc_rv = None
        vol_evidence: tuple[str, ...] = (
            ("missing_btc",) if not btc_idx else ("btc_not_aligned_at_eval",)
        )
    else:
        btc_regime = _btc_regime(btc_idx, eval_ts, step, window)
        btc_vol, btc_rv, vol_evidence = _btc_vol_regime(btc_idx, eval_ts, step, window)

    native_rs = _native_avaxbtc_logret(avaxbtc_idx, eval_ts, step)

    move = avax_btc.move_flag
    if avax_btc.health == "unknown":
        health: Health = "unknown"
    elif avax_btc.health == "degraded" or avax_eth.health == "unknown":
        health = "degraded"
    else:
        health = "valid"

    evidence = list(avax_btc.evidence)
    evidence.extend(vol_evidence)
    if avax_eth.health == "unknown":
        evidence.append("eth_unavailable_or_unaligned")
    if native_rs is None and avaxbtc:
        evidence.append("native_avaxbtc_unaligned")
    if btc_regime != "unknown":
        evidence.append(f"btc_regime_{btc_regime}")

    return CrossMarketState(
        as_of=as_of,
        known_at=eval_ts,
        timeframe=sample.timeframe,
        window=window,
        health=health,
        avax_btc=avax_btc,
        avax_eth=avax_eth,
        eth_btc=eth_btc,
        avaxbtc_log_return=native_rs,
        btc_regime=btc_regime,
        btc_volatility=btc_vol,
        btc_realized_vol=btc_rv,
        synchronized_breakout=_flag_bool(move, "synchronized_breakout"),
        synchronized_breakdown=_flag_bool(move, "synchronized_breakdown"),
        decoupled=_flag_bool(move, "decoupled"),
        evidence=tuple(dict.fromkeys(evidence)),
    )
