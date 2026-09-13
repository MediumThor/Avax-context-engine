from __future__ import annotations

import pytest

from packages.context_engine import ContextEngine
from packages.context_engine.thesis import ImmutableInvalidationError, ThesisLedger
from packages.fixtures import bounce_start_index, sept_2026_failed_breakout
from tests.test_freqai_quantiles import mutate_after


def test_september_snapshot_keeps_4h_bear_through_5m_bounce():
    candles = sept_2026_failed_breakout()
    idx = bounce_start_index(candles)
    engine = ContextEngine()
    before = engine.build_snapshot(candles[:idx])
    after = engine.build_snapshot(candles)
    bears = [t for t in after.theses if t["direction"] == "bear" and t["timeframe"] == "4h"]
    assert bears
    bear = bears[0]
    assert bear["status"] == "active"
    assert bear["invalidation_rules"][0]["timeframe"] == "4h"
    assert bear["invalidation_rules"][0]["kind"] == "close_above"
    assert bear["note"].startswith("Invalidation frozen")
    assert "confidence" not in bear
    before_bears = [t for t in before.theses if t["direction"] == "bear" and t["timeframe"] == "4h"]
    assert before_bears
    assert before_bears[0]["invalidation_fingerprint"] == bear["invalidation_fingerprint"]
    assert before_bears[0]["invalidation_rules"][0]["price"] == bear["invalidation_rules"][0]["price"]
    relief = [t for t in after.theses if t["kind"] == "ltf_relief"]
    if relief:
        assert relief[0]["regime_relation"] == "countertrend"
        assert relief[0]["invalidation_rules"][0]["timeframe"] == "5m"


def test_snapshot_theses_ignore_future_candles():
    candles = sept_2026_failed_breakout()
    as_of = candles[2000].close_time()
    engine = ContextEngine()
    before = engine.build_snapshot(candles, as_of=as_of).to_dict()["theses"]
    mutated = mutate_after(candles, 2001)
    after = engine.build_snapshot(mutated, as_of=as_of).to_dict()["theses"]
    assert before == after


def test_attached_invalidation_still_cannot_move():
    snap = ContextEngine().build_snapshot(sept_2026_failed_breakout())
    bear = next(t for t in snap.theses if t["direction"] == "bear")
    ledger = ThesisLedger()
    ledger.open(
        symbol=bear["symbol"],
        direction="bear",
        kind=bear["kind"],
        created_at=snap.as_of,
        thesis_id="probe-bear",
        lineage_id="probe-bear",
        confirmation_rules=bear["confirmation_rules"],
        invalidation_rules=bear["invalidation_rules"],
    )
    with pytest.raises(ImmutableInvalidationError):
        ledger.move_invalidation("probe-bear", bear["invalidation_rules"][0]["id"], 6.0)
