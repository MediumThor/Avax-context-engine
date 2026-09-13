"""Snapshot zones are walked lifecycles, not static clusters at T."""

from packages.context_engine import ContextEngine
from packages.fixtures import bounce_start_index, sept_2026_failed_breakout
from tests.test_freqai_quantiles import mutate_after


def _zones(snap, timeframe: str):
    state = snap.timeframes[timeframe]
    return list(state.support_zones) + list(state.resistance_zones)


def _sig(snap) -> list[tuple]:
    rows = []
    for name, state in snap.timeframes.items():
        for zone in _zones(snap, name):
            rows.append(
                (
                    name,
                    zone.id,
                    zone.lower,
                    zone.upper,
                    zone.role,
                    zone.status,
                    zone.interaction,
                    zone.outcome,
                )
            )
    return rows


def test_snapshot_zones_carry_lifecycle_fields():
    snap = ContextEngine().build_snapshot(sept_2026_failed_breakout())
    found = []
    for tf in ("4h", "1h", "1d"):
        found.extend(_zones(snap, tf))
    assert found
    for zone in found:
        assert zone.status in {"active", "broken", "reclaimed", "retired"}
        assert zone.interaction
        assert zone.known_at is not None
        assert zone.known_at <= snap.as_of
        assert zone.source == "zone_lifecycle"
        assert zone.upper > zone.lower


def test_5m_bounce_does_not_reclaim_or_move_eight():
    candles = sept_2026_failed_breakout()
    idx = bounce_start_index(candles)
    engine = ContextEngine()
    before_snap = engine.build_snapshot(candles[:idx])
    after_snap = engine.build_snapshot(candles)
    before = {z.id: z for tf in ("5m", "1h", "4h") for z in _zones(before_snap, tf)}
    after = {z.id: z for tf in ("5m", "1h", "4h") for z in _zones(after_snap, tf)}
    eights = [z for z in after.values() if z.lower <= 8.20 and z.upper >= 7.90]
    assert eights
    for zone in eights:
        assert zone.upper > zone.lower
        assert zone.outcome != "successful_reclaim"
        if zone.id in before:
            assert after[zone.id].lower == before[zone.id].lower
            assert after[zone.id].upper == before[zone.id].upper
        if zone.status == "reclaimed":
            assert zone.outcome == "failed_breakout"
    assert any(z.role == "resistance" and 8.15 <= z.lower for z in eights) or any(
        z.status in {"retired", "broken"} and z.outcome == "accepted_through" for z in eights
    )


def test_future_perturbation_does_not_change_zone_lifecycle():
    candles = sept_2026_failed_breakout()
    cut = len(candles) - 40
    as_of = candles[cut - 1].close_time()
    engine = ContextEngine()
    before = _sig(engine.build_snapshot(candles, as_of=as_of))
    after = _sig(engine.build_snapshot(mutate_after(candles, cut), as_of=as_of))
    assert before == after
    assert before
