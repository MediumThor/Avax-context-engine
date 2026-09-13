from __future__ import annotations

from packages.context_engine import ContextEngine
from packages.context_engine.analogs import retrieve_analogs
from packages.fixtures import sept_2026_failed_breakout
from tests.test_freqai_quantiles import make_5m, mutate_after


def test_analogs_require_matured_h10_and_ignore_future():
    candles = make_5m(200)
    as_of = candles[160].close_time()
    before = retrieve_analogs(candles, as_of, k=5, step=5)
    assert before
    for row in before:
        assert row["known_at"] <= as_of.isoformat()
        assert "Not a forecast" in row["note"]
    after = retrieve_analogs(mutate_after(candles, 161), as_of, k=5, step=5)
    assert before == after


def test_snapshot_includes_analogs_patterns_fib():
    candles = sept_2026_failed_breakout()[:900]
    snap = ContextEngine().build_snapshot(candles)
    payload = snap.to_dict()
    assert payload["analogs"]
    assert all(row["known_at"] <= snap.as_of.isoformat() for row in payload["analogs"])
    assert "pattern_hypotheses" in payload
    assert "fib_levels" in payload
    for hyp in payload["pattern_hypotheses"]:
        assert hyp.get("score_provenance") == "evidence_count_v1"
        assert "confidence" not in hyp
    for level in payload["fib_levels"]:
        assert level.get("is_guaranteed_support") is False
        assert level.get("status") == "candidate"


def test_snapshot_future_perturbation_leaves_analogs_unchanged():
    candles = sept_2026_failed_breakout()[:500]
    as_of = candles[420].close_time()
    engine = ContextEngine()
    before = engine.build_snapshot(candles, as_of=as_of).to_dict()["analogs"]
    mutated = list(candles)
    nxt = mutated[421]
    mutated[421] = nxt.__class__(
        nxt.symbol,
        nxt.timeframe,
        nxt.open_time,
        99.0,
        120.0,
        80.0,
        110.0,
        9_999.0,
    )
    after = engine.build_snapshot(mutated, as_of=as_of).to_dict()["analogs"]
    assert before == after
