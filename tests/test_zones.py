from datetime import datetime, timedelta, timezone

import pytest

from packages.context_engine.models import Candle, Pivot
from packages.context_engine.zones import (
    AcceptanceConfig,
    ImmutableZoneBoundsError,
    ZoneSpec,
    ZoneTracker,
    as_range,
    specs_from_pivots,
    track_zones,
)

T0 = datetime(2026, 9, 1, tzinfo=timezone.utc)

# September 2026 founding-regression spirit levels (tests only; not fixture edits).
RESISTANCE_LOW = 8.15
RESISTANCE_HIGH = 8.20
SUPPORT_LOW = 7.94
SUPPORT_HIGH = 8.06
RELIEF_CLOSE = 7.58
RELIEF_HIGH = 7.72
ATR = 0.12


def bar(
    i: int,
    o: float,
    h: float,
    l: float,
    c: float,
    *,
    vol: float = 1000.0,
    tf: str = "1h",
    closed: bool = True,
) -> Candle:
    return Candle(
        "AVAXUSDT",
        tf,
        T0 + timedelta(hours=i),
        o,
        h,
        l,
        c,
        vol,
        is_closed=closed,
    )


def resistance(**kwargs) -> ZoneSpec:
    defaults = dict(lower=RESISTANCE_LOW, upper=RESISTANCE_HIGH, role="resistance", id="z-r-815-820")
    defaults.update(kwargs)
    return ZoneSpec(**defaults)


def support(**kwargs) -> ZoneSpec:
    defaults = dict(lower=SUPPORT_LOW, upper=SUPPORT_HIGH, role="support", id="z-s-794-806")
    defaults.update(kwargs)
    return ZoneSpec(**defaults)


def test_zones_are_ranges_not_thin_lines():
    lo, hi = as_range(8.0, 8.0, ref_price=8.0)
    assert hi > lo
    spec = ZoneSpec(lower=8.17, upper=8.17, role="resistance")
    assert spec.upper > spec.lower
    payload = track_zones([bar(0, 8.0, 8.05, 7.95, 8.01)], [spec]).current()[0].to_dict()
    assert payload["upper"] > payload["lower"]
    assert payload["kind"] == "resistance"


def test_clustered_pivots_become_ranges_with_provenance():
    pivots = [
        Pivot(2, 4, T0, T0 + timedelta(hours=2), 8.00, "low"),
        Pivot(6, 8, T0 + timedelta(hours=4), T0 + timedelta(hours=6), 8.02, "low"),
        Pivot(12, 14, T0 + timedelta(hours=10), T0 + timedelta(hours=12), 9.10, "high"),
    ]
    specs = specs_from_pivots(pivots, current_price=8.40, timeframes=("1h", "4h"))
    assert specs
    assert all(spec.upper > spec.lower for spec in specs)
    assert any(spec.role == "support" for spec in specs)
    assert all("pivot_cluster" in spec.sources or "swing_cluster" in spec.sources for spec in specs)
    live = track_zones([bar(0, 8.40, 8.45, 8.35, 8.42)], specs).current()
    assert live[0].provenance
    assert live[0].known_at <= live[0].provenance[0].at or live[0].known_at == live[0].created_at


def test_wick_through_is_probe_not_acceptance():
    candles = [
        bar(0, 8.00, 8.06, 7.96, 8.04),
        bar(1, 8.04, 8.28, 8.02, 8.12),  # wick through 8.20, close still below
        bar(2, 8.12, 8.14, 8.06, 8.08),
    ]
    zone = track_zones(candles, [resistance()], atrs=[ATR, ATR, ATR]).get("z-r-815-820")
    assert zone.interaction == "rejected"
    assert zone.status == "active"
    assert zone.outcome == "held"
    assert zone.accepted_through is False
    assert not any(event.to_state == "accepted" for event in zone.provenance)
    assert any("probe" in event.cause for event in zone.provenance)


def test_close_beyond_is_penetration_not_acceptance():
    candles = [
        bar(0, 8.05, 8.10, 8.00, 8.08),
        bar(1, 8.10, 8.22, 8.08, 8.21),  # close beyond, 0.01 < 0.5*ATR
    ]
    zone = track_zones(candles, [resistance()], atrs=[ATR, ATR]).get("z-r-815-820")
    assert zone.interaction == "penetrated"
    assert zone.status == "active"
    assert zone.accepted_through is False
    assert zone.closes_beyond == 1


def test_acceptance_via_close_count():
    config = AcceptanceConfig(close_count=2, atr_multiple=0.5, mode="close_count")
    candles = [
        bar(0, 8.05, 8.10, 8.00, 8.08),
        bar(1, 8.10, 8.22, 8.08, 8.21),
        bar(2, 8.21, 8.24, 8.18, 8.22),
    ]
    zone = track_zones(candles, [resistance()], config=config, atrs=[ATR] * 3).get("z-r-815-820")
    assert zone.interaction == "accepted"
    assert zone.status == "broken"
    assert zone.outcome == "accepted_through"
    assert zone.accepted_through is True


def test_acceptance_via_atr_distance_on_single_close():
    config = AcceptanceConfig(close_count=3, atr_multiple=0.5, mode="either")
    candles = [
        bar(0, 8.05, 8.10, 8.00, 8.08),
        bar(1, 8.10, 8.40, 8.08, 8.36),  # 8.36 >= 8.20 + 0.06
    ]
    zone = track_zones(candles, [resistance()], config=config, atrs=[ATR, ATR]).get("z-r-815-820")
    assert zone.interaction == "accepted"
    assert zone.outcome == "accepted_through"


def test_failed_breakout_after_penetration_without_acceptance():
    candles = [
        bar(0, 8.00, 8.06, 7.96, 8.04),
        bar(1, 8.04, 8.22, 8.02, 8.21),  # penetrated
        bar(2, 8.16, 8.18, 8.06, 8.10),  # close back below the range
    ]
    zone = track_zones(candles, [resistance()], atrs=[ATR, ATR, ATR]).get("z-r-815-820")
    assert zone.interaction == "reclaimed"
    assert zone.status == "reclaimed"
    assert zone.outcome == "failed_breakout"
    assert zone.accepted_through is False
    assert zone.lower == RESISTANCE_LOW
    assert zone.upper == RESISTANCE_HIGH


def test_successful_reclaim_after_accepted_breakdown():
    config = AcceptanceConfig(close_count=2, atr_multiple=0.5, mode="either")
    candles = [
        bar(0, 8.20, 8.24, 8.12, 8.16),
        bar(1, 8.10, 8.12, 7.90, 7.91),  # close beyond support, not ATR-far
        bar(2, 7.90, 7.92, 7.78, 7.80),  # second close beyond → accepted
        bar(3, 7.85, 8.04, 7.82, 8.00),  # retest from below (inside)
        bar(4, 8.00, 8.12, 7.96, 8.10),  # origin close 1
        bar(5, 8.10, 8.22, 8.06, 8.18),  # origin close 2 → successful reclaim
    ]
    zone = track_zones(candles, [support()], config=config, atrs=[ATR] * 6).get("z-s-794-806")
    assert zone.interaction == "reclaimed"
    assert zone.status == "reclaimed"
    assert zone.outcome == "successful_reclaim"
    assert zone.accepted_through is True
    assert any(event.to_state == "accepted" for event in zone.provenance)
    assert any(event.to_state == "retesting" for event in zone.provenance)
    assert zone.lower == SUPPORT_LOW
    assert zone.upper == SUPPORT_HIGH


def test_accepted_resistance_lost_is_failed_breakout_not_reclaim_success():
    config = AcceptanceConfig(close_count=2, mode="close_count")
    candles = [
        bar(0, 8.05, 8.10, 8.00, 8.08),
        bar(1, 8.10, 8.22, 8.08, 8.21),
        bar(2, 8.21, 8.24, 8.18, 8.22),  # accepted through
        bar(3, 8.18, 8.20, 8.00, 8.04),  # back through / retest
        bar(4, 8.04, 8.06, 7.96, 8.00),
        bar(5, 8.00, 8.02, 7.90, 7.94),  # second origin close
    ]
    zone = track_zones(candles, [resistance()], config=config, atrs=[ATR] * 6).get("z-r-815-820")
    assert zone.outcome == "failed_breakout"
    assert zone.interaction == "reclaimed"


def test_retest_from_opposite_side_after_acceptance():
    config = AcceptanceConfig(close_count=2, mode="close_count")
    candles = [
        bar(0, 8.20, 8.24, 8.12, 8.16),
        bar(1, 8.10, 8.12, 7.90, 7.91),
        bar(2, 7.90, 7.92, 7.78, 7.80),
        bar(3, 7.82, 8.02, 7.78, 7.98),
    ]
    zone = track_zones(candles, [support()], config=config, atrs=[ATR] * 4).get("z-s-794-806")
    assert zone.interaction == "retesting"
    assert zone.status == "broken"
    assert zone.outcome == "accepted_through"


def test_bounds_are_immutable_on_spec_and_live_zone():
    spec = resistance()
    with pytest.raises(ImmutableZoneBoundsError, match="frozen"):
        spec.with_bounds(7.40, 7.60)
    tracker = track_zones([bar(0, 8.00, 8.06, 7.96, 8.04)], [spec], atrs=[ATR])
    live = tracker.get("z-r-815-820")
    with pytest.raises(Exception):
        live.lower = 7.50  # type: ignore[misc]
    with pytest.raises(ImmutableZoneBoundsError):
        live.with_bounds(7.40, 7.60)
    with pytest.raises(ImmutableZoneBoundsError):
        tracker.relocate("z-r-815-820", 7.40, 7.60)
    assert tracker.get("z-r-815-820").lower == RESISTANCE_LOW
    assert tracker.get("z-r-815-820").upper == RESISTANCE_HIGH


def test_retired_is_terminal_and_does_not_resurrect():
    config = AcceptanceConfig(close_count=1, atr_multiple=0.5, retire_atr=2.0, mode="close_count")
    candles = [
        bar(0, 8.05, 8.10, 8.00, 8.08),
        bar(1, 8.20, 8.70, 8.18, 8.60),  # accepted and far beyond → retired
        bar(2, 8.10, 8.22, 8.00, 8.05),  # later pullback must not revive
    ]
    zone = track_zones(candles, [resistance()], config=config, atrs=[ATR, ATR, ATR]).get("z-r-815-820")
    assert zone.interaction == "retired"
    assert zone.status == "retired"
    assert zone.lower == RESISTANCE_LOW
    assert not any(event.to_state == "testing" and event.from_state == "retired" for event in zone.provenance)


def test_unfinished_candle_does_not_mutate_state():
    spec = resistance()
    tracker = ZoneTracker([spec])
    tracker.ingest(bar(0, 8.00, 8.06, 7.96, 8.04), ATR)
    before = tracker.get("z-r-815-820").to_dict()
    tracker.ingest(bar(1, 8.04, 8.28, 8.02, 8.22, closed=False), ATR)
    assert tracker.get("z-r-815-820").to_dict() == before


def test_future_candle_perturbation_does_not_change_past():
    candles = [
        bar(0, 8.00, 8.06, 7.96, 8.04),
        bar(1, 8.04, 8.18, 8.00, 8.12),
        bar(2, 8.12, 8.14, 8.06, 8.08),
        bar(3, 8.08, 8.22, 8.06, 8.21),
        bar(4, 8.16, 8.18, 8.04, 8.10),
    ]
    atrs = [ATR] * 5
    prefix = track_zones(candles[:3], [resistance()], atrs=atrs[:3]).get("z-r-815-820")
    mutated = list(candles)
    mutated[4] = bar(4, 9.00, 9.50, 8.90, 9.40)
    after = track_zones(mutated[:3], [resistance()], atrs=atrs[:3]).get("z-r-815-820")
    assert prefix.interaction == after.interaction
    assert prefix.tests == after.tests
    assert prefix.lower == after.lower == RESISTANCE_LOW
    assert prefix.upper == after.upper == RESISTANCE_HIGH
    assert [e.to_dict() for e in prefix.provenance] == [e.to_dict() for e in after.provenance]


def test_replay_is_deterministic():
    candles = [
        bar(0, 8.00, 8.06, 7.96, 8.04),
        bar(1, 8.04, 8.28, 8.02, 8.12),
        bar(2, 8.12, 8.22, 8.08, 8.21),
        bar(3, 8.16, 8.18, 8.04, 8.10),
    ]
    a = track_zones(candles, [resistance()], atrs=[ATR] * 4).get("z-r-815-820").to_dict()
    b = track_zones(candles, [resistance()], atrs=[ATR] * 4).get("z-r-815-820").to_dict()
    assert a == b


def test_september_failed_eight_spirit_no_moving_invalidation():
    config = AcceptanceConfig(close_count=2, atr_multiple=0.5, mode="either")
    candles = [
        bar(0, 8.10, 8.14, 8.06, 8.12),
        bar(1, 8.12, 8.22, 8.08, 8.13),  # wick into 8.15-8.20, close below
        bar(2, 8.13, 8.16, 8.08, 8.10),  # rejected
        bar(3, 8.10, 8.24, 8.08, 8.14),  # another probe, still not accepted
        bar(4, 8.12, 8.15, 8.00, 8.02),
        bar(5, 8.00, 8.04, 7.88, 7.91),  # support penetrated
        bar(6, 7.90, 7.92, 7.76, 7.80),  # support accepted
        bar(7, 7.70, 8.02, 7.50, RELIEF_CLOSE),  # wick into ~$8, close 7.58 — not a reclaim
    ]
    atrs = [ATR] * len(candles)
    tracker = track_zones(candles, [resistance(), support()], config=config, atrs=atrs)
    resist = tracker.get("z-r-815-820")
    supp = tracker.get("z-s-794-806")

    assert RELIEF_HIGH < SUPPORT_LOW
    assert resist.lower == RESISTANCE_LOW and resist.upper == RESISTANCE_HIGH
    assert resist.accepted_through is False
    assert resist.interaction in {"rejected", "testing", "approaching"}
    assert resist.status == "active"

    assert supp.interaction in {"accepted", "retesting"}
    assert supp.status == "broken"
    assert supp.outcome == "accepted_through"
    assert supp.lower == SUPPORT_LOW
    assert supp.upper == SUPPORT_HIGH
    assert supp.accepted_through is True

    with pytest.raises(ImmutableZoneBoundsError):
        tracker.relocate("z-s-794-806", 7.40, 7.60)
    assert tracker.get("z-s-794-806").lower == SUPPORT_LOW
    assert tracker.get("z-s-794-806").upper == SUPPORT_HIGH
    assert tracker.get("z-s-794-806").interaction in {"accepted", "retesting"}
    assert tracker.get("z-s-794-806").outcome != "successful_reclaim"


def test_contract_fields_and_append_only_provenance():
    candles = [
        bar(0, 8.00, 8.06, 7.96, 8.04),
        bar(1, 8.04, 8.18, 8.02, 8.12),
        bar(2, 8.12, 8.14, 8.06, 8.08),
    ]
    zone = track_zones(candles, [resistance()], atrs=[ATR] * 3).get("z-r-815-820")
    payload = zone.to_dict()
    for key in (
        "id",
        "lower",
        "upper",
        "kind",
        "role",
        "status",
        "interaction",
        "timeframes",
        "sources",
        "strength",
        "tests",
        "test_count",
        "last_test_at",
        "created_at",
        "known_at",
        "provenance",
    ):
        assert key in payload
    assert payload["upper"] > payload["lower"]
    assert isinstance(payload["provenance"], list)
    assert payload["provenance"]
    states = [event["to_state"] for event in payload["provenance"]]
    assert states[0] == "approaching"
    assert "testing" in states
    with pytest.raises(Exception):
        zone.provenance[0].to_state = "accepted"  # type: ignore[misc]


def test_all_required_interaction_states_are_reachable():
    config = AcceptanceConfig(close_count=2, retire_atr=1.5, mode="close_count")
    seen: set[str] = set()

    def collect(candles: list[Candle], spec: ZoneSpec) -> None:
        tracker = ZoneTracker([spec], config=config)
        for i, candle in enumerate(candles):
            tracker.ingest(candle, ATR)
            seen.add(tracker.current()[0].interaction)

    collect(
        [
            bar(0, 8.00, 8.06, 7.96, 8.04),
            bar(1, 8.04, 8.18, 8.02, 8.12),
            bar(2, 8.12, 8.14, 8.06, 8.08),
            bar(3, 8.10, 8.22, 8.08, 8.21),
            bar(4, 8.16, 8.18, 8.04, 8.10),
        ],
        resistance(),
    )
    collect(
        [
            bar(0, 8.20, 8.24, 8.12, 8.16),
            bar(1, 8.10, 8.12, 7.90, 7.91),
            bar(2, 7.90, 7.92, 7.78, 7.80),
            bar(3, 7.82, 8.02, 7.78, 7.98),
            bar(4, 8.00, 8.12, 7.96, 8.10),
            bar(5, 8.10, 8.22, 8.06, 8.18),
        ],
        support(),
    )
    retire_tracker = ZoneTracker(
        [resistance(id="z-r-retire")],
        config=AcceptanceConfig(close_count=1, retire_atr=1.5, mode="close_count"),
    )
    for candle in (
        bar(0, 8.05, 8.10, 8.00, 8.08),
        bar(1, 8.20, 8.90, 8.18, 8.80),
    ):
        retire_tracker.ingest(candle, ATR)
        seen.add(retire_tracker.current()[0].interaction)
    for state in (
        "approaching",
        "testing",
        "rejected",
        "penetrated",
        "accepted",
        "retesting",
        "reclaimed",
        "retired",
    ):
        assert state in seen, f"missing interaction {state}: {sorted(seen)}"


def test_htf_plateau_becomes_frozen_range():
    from packages.context_engine.zones import plateau_specs

    highs = [bar(i, 8.10, 8.192, 8.00, 8.11) for i in range(5)]
    specs = plateau_specs(highs, timeframe="4h", min_run=3)
    assert specs
    assert specs[0].role == "resistance"
    assert specs[0].upper > specs[0].lower
    assert specs[0].known_at == highs[2].open_time


def test_spec_does_not_open_before_known_at():
    later = T0 + timedelta(hours=3)
    spec = resistance(id="z-late", known_at=later, created_at=later)
    tracker = ZoneTracker([spec])
    tracker.ingest(bar(0, 8.10, 8.14, 8.06, 8.12), ATR)
    tracker.ingest(bar(1, 8.12, 8.16, 8.08, 8.11), ATR)
    assert tracker.current() == ()
    tracker.ingest(bar(3, 8.10, 8.14, 8.06, 8.12), ATR)
    assert tracker.current()[0].id == "z-late"
    assert tracker.current()[0].known_at <= later
