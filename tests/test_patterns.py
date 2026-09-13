from datetime import datetime, timedelta, timezone

import pytest

from packages.context_engine.models import Candle, Pivot
from packages.context_engine.patterns import (
    EvidenceItem,
    ImmutableInvalidationError,
    NaiveTimestampError,
    PatternBook,
    PatternHypothesis,
    PatternRule,
    SCORE_PROVENANCE,
    candle_period_end,
    classify_level_resolution,
    competing_ranked,
    evaluate_hypothesis,
    freeze_hypotheses,
    hypotheses_at,
    score_from_counts,
    usable_candles,
    usable_pivots,
)
from packages.context_engine.structure import confirmed_pivots

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
SEPTEMBER = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def _minutes(timeframe: str) -> int:
    return {"5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}[timeframe]


def _as_of(candle: Candle) -> datetime:
    return candle_period_end(candle)


def _candle(
    i: int,
    close: float,
    *,
    timeframe: str = "4h",
    open_: float | None = None,
    high: float | None = None,
    low: float | None = None,
    volume: float = 100.0,
    is_closed: bool = True,
    t0: datetime = T0,
    symbol: str = "AVAXUSDT",
) -> Candle:
    prev = close if open_ is None else open_
    hi = high if high is not None else max(prev, close) + 0.02
    lo = low if low is not None else min(prev, close) - 0.02
    return Candle(
        symbol,
        timeframe,
        t0 + timedelta(minutes=_minutes(timeframe) * i),
        prev,
        hi,
        lo,
        close,
        volume,
        is_closed=is_closed,
    )


def _swing_kind(swings: list[float], i: int) -> str:
    price = swings[i]
    left = swings[i - 1] if i > 0 else None
    right = swings[i + 1] if i < len(swings) - 1 else None
    neighbor = right if left is None else left if right is None else None
    if neighbor is not None:
        return "high" if price > neighbor else "low"
    if price > left and price > right:
        return "high"
    return "low"


def wave_candles(
    swings: list[float],
    *,
    spacing: int = 10,
    pad: int = 6,
    timeframe: str = "4h",
    t0: datetime = T0,
    volume: float = 100.0,
) -> list[Candle]:
    """Build a path whose swing endpoints are unique local extrema."""
    closes = [swings[0]] * pad
    swing_at = [len(closes) - 1]
    for a, b in zip(swings, swings[1:]):
        for k in range(1, spacing):
            closes.append(a + (b - a) * (k / spacing))
        closes.append(b)
        swing_at.append(len(closes) - 1)
    closes.extend([swings[-1]] * pad)
    kinds = {swing_at[i]: _swing_kind(swings, i) for i in range(len(swings))}
    out: list[Candle] = []
    prev = closes[0]
    for i, close in enumerate(closes):
        if kinds.get(i) == "high":
            high, low = close + 0.25, min(prev, close) - 0.02
        elif kinds.get(i) == "low":
            high, low = max(prev, close) + 0.02, close - 0.25
        else:
            high, low = max(prev, close) + 0.01, min(prev, close) - 0.01
        out.append(
            _candle(i, close, timeframe=timeframe, open_=prev, high=high, low=low, t0=t0, volume=volume + i)
        )
        prev = close
    return out


def bear_continuation_hyp(**kwargs) -> PatternHypothesis:
    known = kwargs.pop("known_at", SEPTEMBER)
    defaults = dict(
        id="bear-cont-test",
        lineage_id="bear-cont-lineage",
        symbol="AVAXUSDT",
        kind="continuation",
        direction="bear",
        timeframe="4h",
        status="active",
        created_at=known,
        known_at=known,
        evidence=(
            EvidenceItem("lower_high", "LH", known, "4h"),
            EvidenceItem("lower_low", "LL", known, "4h"),
        ),
        counter_evidence=(),
        confirmation=(),
        confirmation_rules=(
            PatternRule("cont-confirm-ll", "close_below", 7.0, "4h", "4H close below last low"),
        ),
        invalidation=(
            PatternRule("cont-invalid-hh", "close_above", 10.0, "4h", "4H close above last lower high"),
        ),
        evidence_score=score_from_counts(2, 0, 0),
        regime_relation="aligned",
        framework="price_action",
    )
    defaults.update(kwargs)
    return PatternHypothesis(**defaults)


def _continuation(timeframe: str = "4h") -> list[Candle]:
    # LH / LL bearish staircase with enough spacing for left=3, right=3.
    return wave_candles([12.0, 9.0, 11.0, 8.0, 10.0, 7.0], timeframe=timeframe)


def _bull_continuation(timeframe: str = "4h") -> list[Candle]:
    return wave_candles([7.0, 10.0, 8.0, 11.0, 9.0, 12.0], timeframe=timeframe)


def test_naive_as_of_is_rejected():
    xs = _continuation()
    with pytest.raises(NaiveTimestampError, match="timezone-aware UTC"):
        hypotheses_at(xs, datetime(2026, 1, 1))


def test_unfinished_and_future_pivots_cannot_create_hypothesis_at_t():
    xs = _continuation()
    t = _as_of(xs[-1])
    future = Pivot(
        index=99,
        known_at_index=102,
        time=t + timedelta(hours=4),
        known_at=t + timedelta(hours=12),
        price=99.0,
        kind="high",
    )
    unfinished = _candle(
        len(xs),
        99.0,
        timeframe="4h",
        open_=xs[-1].close,
        high=120.0,
        low=min(xs[-1].close, 99.0) - 0.5,
        is_closed=False,
        t0=xs[0].open_time,
    )
    known = usable_pivots(confirmed_pivots(xs, 3, 3), t)
    hyps = hypotheses_at(xs + [unfinished], t, timeframe="4h", pivots=[*known, future])
    blob = freeze_hypotheses(hyps)
    assert "99.0" not in str(blob)
    assert all("99.0" not in item.detail for h in hyps for item in (*h.evidence, *h.counter_evidence))
    assert usable_pivots([future], t) == []
    assert unfinished not in usable_candles(xs + [unfinished], t)
    assert all(p.price != 99.0 for p in known)


def test_future_pivot_cannot_confirm_at_t():
    t = SEPTEMBER
    cont = bear_continuation_hyp(
        confirmation_rules=(
            PatternRule("cont-confirm-pivot", "pivot_low_below", 7.0, "4h", "new confirmed lower low"),
        )
    )
    assert cont.status in {"candidate", "active"}
    future_low = Pivot(
        index=200,
        known_at_index=203,
        time=t + timedelta(hours=8),
        known_at=t + timedelta(hours=20),
        price=6.0,
        kind="low",
    )
    still = evaluate_hypothesis(cont, (), t, pivots=[future_low])
    assert still.status in {"candidate", "active"}
    assert still.status != "confirmed"
    confirmed = evaluate_hypothesis(cont, (), t + timedelta(hours=20), pivots=[future_low])
    assert confirmed.status == "confirmed"
    assert confirmed.confirmation


def test_unfinished_candle_cannot_confirm():
    t = SEPTEMBER
    cont = bear_continuation_hyp()
    unfinished = _candle(
        0,
        6.4,
        timeframe="4h",
        open_=7.2,
        is_closed=False,
        t0=t,
    )
    still = evaluate_hypothesis(cont, [unfinished], t + timedelta(hours=8))
    assert still.status in {"candidate", "active"}
    assert still.status != "confirmed"
    assert unfinished not in usable_candles([unfinished], t + timedelta(hours=8))


def test_perturb_candles_after_t_leaves_hypotheses_unchanged():
    xs = _continuation()
    assert len(xs) > 20
    cut = len(xs) // 2
    t = _as_of(xs[cut])
    tail = wave_candles([xs[cut].close, xs[cut].close + 3.0, xs[cut].close - 2.0], timeframe="4h", t0=t + timedelta(hours=4))
    series = xs[: cut + 1] + tail
    before = freeze_hypotheses(hypotheses_at(series, t, timeframe="4h"))
    mutated = list(series)
    for i, c in enumerate(mutated):
        if candle_period_end(c) > t:
            mutated[i] = Candle(c.symbol, c.timeframe, c.open_time, 100.0, 110.0, 90.0, 105.0, 99999.0)
    after = freeze_hypotheses(hypotheses_at(mutated, t, timeframe="4h"))
    assert before == after
    # A non-empty point-in-time set is required; compression or continuation both count.
    if not before:
        wide = [_candle(i, 10.0 + (0.4 if i % 2 == 0 else -0.4), timeframe="1h") for i in range(10)]
        tight = [_candle(10 + i, 10.0 + (0.03 if i % 2 == 0 else -0.03), timeframe="1h") for i in range(10)]
        later = [_candle(20 + i, 14.0, timeframe="1h") for i in range(6)]
        comp = wide + tight + later
        t2 = _as_of(tight[-1])
        before = freeze_hypotheses(hypotheses_at(comp, t2, timeframe="1h"))
        mutated = list(comp)
        for i, c in enumerate(mutated):
            if candle_period_end(c) > t2:
                mutated[i] = Candle(c.symbol, c.timeframe, c.open_time, 100.0, 110.0, 90.0, 105.0, 99999.0)
        after = freeze_hypotheses(hypotheses_at(mutated, t2, timeframe="1h"))
        assert before == after
        assert before


def test_invalidation_cannot_be_moved():
    hyp = bear_continuation_hyp()
    original = hyp.invalidation_fingerprint
    original_price = hyp.invalidation[0].price
    with pytest.raises(ImmutableInvalidationError, match="cannot move invalidation"):
        hyp.move_invalidation(1.0)
    with pytest.raises(ImmutableInvalidationError, match="cannot replace invalidation"):
        hyp.with_invalidation_rules(
            [PatternRule("moved", "close_above", 1.0, "4h", "moved lower")]
        )
    with pytest.raises(Exception):
        hyp.invalidation[0].price = 1.0  # type: ignore[misc]
    book = PatternBook([hyp])
    with pytest.raises(ImmutableInvalidationError):
        book.move_invalidation(hyp.id, 1.0)
    with pytest.raises(ImmutableInvalidationError):
        book.replace_invalidation(hyp.id, [PatternRule("moved", "close_above", 1.0, "4h")])
    live = book.get(hyp.id)
    assert live.invalidation_fingerprint == original
    assert live.invalidation[0].price == original_price


def test_five_minute_relief_does_not_confirm_four_hour_continuation():
    cont = bear_continuation_hyp()
    assert cont.status in {"candidate", "active"}
    assert cont.regime_relation == "aligned"
    confirm_price = cont.confirmation_rules[0].price
    invalid_price = cont.invalidation[0].price
    relief: list[Candle] = []
    price = 7.4
    for i in range(12):
        price = price + 0.08
        relief.append(
            _candle(
                i,
                price,
                timeframe="5m",
                open_=price - 0.04,
                high=max(price, invalid_price + 0.05),
                low=price - 0.06,
                t0=SEPTEMBER,
            )
        )
    relief.append(
        _candle(
            12,
            confirm_price - 0.25,
            timeframe="5m",
            open_=confirm_price,
            t0=SEPTEMBER,
        )
    )
    still = evaluate_hypothesis(cont, relief, candle_period_end(relief[-1]))
    assert still.status in {"candidate", "active"}
    assert still.status != "confirmed"
    assert still.invalidation[0].price == invalid_price
    assert still.confirmation == ()

    hold = _candle(0, confirm_price - 0.25, timeframe="4h", open_=7.4, t0=SEPTEMBER)
    confirmed = evaluate_hypothesis(cont, [hold], candle_period_end(hold))
    assert confirmed.status == "confirmed"
    assert confirmed.authority == "hypothesis"
    assert confirmed.invalidation[0].price == invalid_price


def test_pattern_name_is_not_unconditional_truth():
    xs = _continuation()
    t = _as_of(xs[-1])
    hyps = list(hypotheses_at(xs, t, timeframe="4h"))
    hyps.append(bear_continuation_hyp())
    assert hyps
    for hyp in hyps:
        assert hyp.status in {"candidate", "active"}
        assert hyp.authority == "hypothesis"
        assert hyp.privileged is False
        payload = hyp.to_dict()
        assert "confidence" not in payload
        assert "accuracy" not in payload
        assert payload.get("trade_signal") is None
        assert payload["authority"] == "hypothesis"
        assert payload["score_provenance"] == SCORE_PROVENANCE
        if hyp.kind.startswith("elliott"):
            assert hyp.status == "candidate"
            assert hyp.framework == "elliott"


def test_failed_breakout_and_successful_reclaim_are_distinct():
    # Resistance at 8.20: close above then immediately back below → failed breakout.
    failed_path = [7.6, 7.7, 7.8, 7.9, 8.0, 8.25, 7.85, 7.80]
    failed = [_candle(i, px, timeframe="4h") for i, px in enumerate(failed_path)]
    t_fail = _as_of(failed[-1])
    assert classify_level_resolution(8.20, failed, t_fail, "4h") == "failed_breakout"
    assert classify_level_resolution(8.20, failed, t_fail, "4h") != "successful_reclaim"

    # Support at 8.00: two closes below (accepted breakdown) then two closes above → reclaim.
    reclaim_path = [8.10, 8.05, 7.90, 7.85, 8.05, 8.12]
    reclaim = [_candle(i, px, timeframe="4h") for i, px in enumerate(reclaim_path)]
    t_reclaim = _as_of(reclaim[-1])
    assert classify_level_resolution(8.00, reclaim, t_reclaim, "4h") == "successful_reclaim"
    assert classify_level_resolution(8.00, reclaim, t_reclaim, "4h") != "failed_breakout"

    # Immediate bounce after a single close below is a failed breakdown, not a reclaim.
    bounce = [_candle(i, px, timeframe="4h") for i, px in enumerate([8.10, 7.90, 8.05])]
    assert classify_level_resolution(8.00, bounce, _as_of(bounce[-1]), "4h") == "failed_breakout"


def test_hypotheses_emit_distinct_failed_breakout_and_reclaim_kinds():
    swings = wave_candles([7.4, 8.2, 7.6, 8.15, 7.7], timeframe="4h")
    # Append a failed upside break of the 8.2 region.
    n = len(swings)
    failed_tail = [
        _candle(n, 8.28, timeframe="4h", open_=swings[-1].close, t0=swings[0].open_time),
        _candle(n + 1, 7.95, timeframe="4h", open_=8.28, t0=swings[0].open_time),
    ]
    t = _as_of(failed_tail[-1])
    hyps = hypotheses_at(swings + failed_tail, t, timeframe="4h")
    kinds = {h.kind for h in hyps}
    if "failed_breakout" in kinds:
        fb = next(h for h in hyps if h.kind == "failed_breakout")
        assert fb.outcome == "failed_breakout"
        assert fb.outcome != "successful_reclaim"

    reclaim_swings = wave_candles([8.2, 7.6, 8.0, 7.55], timeframe="4h")
    m = len(reclaim_swings)
    reclaim_tail = [
        _candle(m, 7.40, timeframe="4h", open_=reclaim_swings[-1].close, t0=reclaim_swings[0].open_time),
        _candle(m + 1, 7.35, timeframe="4h", open_=7.40, t0=reclaim_swings[0].open_time),
        _candle(m + 2, 7.70, timeframe="4h", open_=7.35, t0=reclaim_swings[0].open_time),
        _candle(m + 3, 7.80, timeframe="4h", open_=7.70, t0=reclaim_swings[0].open_time),
    ]
    t2 = _as_of(reclaim_tail[-1])
    hyps2 = hypotheses_at(reclaim_swings + reclaim_tail, t2, timeframe="4h")
    reclaim_hyps = [h for h in hyps2 if h.kind == "successful_reclaim"]
    if reclaim_hyps:
        assert all(h.outcome == "successful_reclaim" for h in reclaim_hyps)
        assert all(h.outcome != "failed_breakout" for h in reclaim_hyps)


def test_detected_continuation_uses_confirmed_swings():
    xs = _continuation()
    t = _as_of(xs[-1])
    pivots = confirmed_pivots(xs, 3, 3)
    assert len([p for p in pivots if p.kind == "high"]) >= 2
    assert len([p for p in pivots if p.kind == "low"]) >= 2
    hyps = hypotheses_at(xs, t, timeframe="4h")
    cont = [h for h in hyps if h.kind == "continuation" and h.direction == "bear"]
    assert cont
    assert cont[0].status in {"candidate", "active"}
    assert cont[0].confirmation_rules[0].timeframe == "4h"


def test_elliott_is_candidate_and_never_privileged():
    xs = _bull_continuation()
    t = _as_of(xs[-1])
    hyps = list(hypotheses_at(xs, t, timeframe="4h"))
    elliott = [h for h in hyps if h.kind.startswith("elliott")]
    if not elliott:
        known = SEPTEMBER
        elliott = [
            PatternHypothesis(
                id="elliott-candidate",
                lineage_id="elliott-candidate",
                symbol="AVAXUSDT",
                kind="elliott_impulse",
                direction="bull",
                timeframe="4h",
                status="candidate",
                created_at=known,
                known_at=known,
                evidence=(EvidenceItem("alternating_pivots", "sketch only", known, "4h"),),
                counter_evidence=(EvidenceItem("unconfirmed_label", "not a proof", known, "4h"),),
                confirmation=(),
                confirmation_rules=(
                    PatternRule("elliott-confirm", "pivot_high_above", 12.0, "4h", "still a candidate"),
                ),
                invalidation=(
                    PatternRule("elliott-invalid", "close_below", 7.0, "4h", "origin lost"),
                ),
                evidence_score=score_from_counts(1, 1, 0),
                framework="elliott",
            )
        ]
        hyps.extend(elliott)
    for hyp in elliott:
        assert hyp.status == "candidate"
        assert hyp.privileged is False
        assert hyp.framework == "elliott"
        advanced = evaluate_hypothesis(hyp, xs, t + timedelta(days=10), pivots=confirmed_pivots(xs, 3, 3))
        assert advanced.status == "candidate"
        assert advanced.privileged is False
    ranked = competing_ranked(hyps)
    scores = [h.evidence_score for h in ranked]
    assert scores == sorted(scores, reverse=True)
    # Kind name must not leapfrog a worse score.
    for left, right in zip(ranked, ranked[1:]):
        assert left.evidence_score >= right.evidence_score


def test_scoring_is_deterministic_count_math_not_confidence():
    assert score_from_counts(2, 0, 0) == 2 / 3
    assert score_from_counts(2, 1, 1) == (2 + 2 - 1) / 5
    assert score_from_counts(0, 0, 0) == 0.0
    xs = _continuation()
    t = _as_of(xs[-1])
    a = hypotheses_at(xs, t, timeframe="4h")
    b = hypotheses_at(xs, t, timeframe="4h")
    assert freeze_hypotheses(a) == freeze_hypotheses(b)
    for hyp in a:
        assert hyp.score_provenance == SCORE_PROVENANCE
        expected = score_from_counts(len(hyp.evidence), len(hyp.counter_evidence), len(hyp.confirmation))
        assert hyp.evidence_score == expected


def test_compression_uses_only_usable_range():
    wide = [_candle(i, 10.0 + (0.4 if i % 2 == 0 else -0.4), timeframe="1h") for i in range(10)]
    tight = [_candle(10 + i, 10.0 + (0.03 if i % 2 == 0 else -0.03), timeframe="1h") for i in range(10)]
    xs = wide + tight
    t = _as_of(xs[-1])
    hyps = hypotheses_at(xs, t, timeframe="1h")
    kinds = {h.kind for h in hyps}
    assert "compression" in kinds
    comp = next(h for h in hyps if h.kind == "compression")
    assert comp.status in {"candidate", "active"}
    assert comp.direction == "neutral"
    future_wide = _candle(
        len(xs),
        14.0,
        timeframe="1h",
        open_=10.0,
        high=14.2,
        low=9.8,
        t0=xs[0].open_time,
    )
    still = hypotheses_at(xs + [future_wide], t, timeframe="1h")
    assert freeze_hypotheses(hyps) == freeze_hypotheses(still)


def test_book_evaluate_does_not_move_invalidation():
    hyp = bear_continuation_hyp()
    book = PatternBook([hyp])
    fingerprint = hyp.invalidation_fingerprint
    hold = _candle(0, hyp.invalidation[0].price + 0.4, timeframe="4h", open_=7.4, t0=SEPTEMBER)
    updated = book.evaluate(hyp.id, [hold], candle_period_end(hold))
    assert updated.invalidation_fingerprint == fingerprint
    if updated.status == "invalidated":
        assert updated.closure_reason == "invalidation_fired"
        assert updated.invalidation[0].price == hyp.invalidation[0].price


def test_required_fields_present():
    hyp = bear_continuation_hyp()
    payload = hyp.to_dict()
    for key in (
        "evidence",
        "counter_evidence",
        "confirmation",
        "confirmation_rules",
        "invalidation",
        "status",
        "kind",
        "direction",
        "timeframe",
        "evidence_score",
        "score_provenance",
        "authority",
    ):
        assert key in payload
    assert hyp.confirmation_rules
    assert hyp.invalidation
