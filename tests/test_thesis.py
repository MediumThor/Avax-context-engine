from datetime import datetime, timezone

import pytest

from packages.context_engine.thesis import (
    EvidenceItem,
    ImmutableInvalidationError,
    PriceObservation,
    ThesisClosedError,
    ThesisLedger,
    ThesisRule,
    september_failed_breakout_bear,
)

SEPTEMBER = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)

# Scenario levels from the founding September 2026 notes. Tests consume them;
# they do not rewrite benchmark fixture files.
FAILED_BREAKOUT = 8.20
FAILED_SUPPORT = 8.00
RELIEF_CLOSE = 7.58
RELIEF_HIGH = 7.72


def _bear_rules():
    return [
        ThesisRule(
            id="bear-confirm-accept-below-8",
            kind="close_below",
            price=FAILED_SUPPORT,
            timeframe="4h",
            description="4H acceptance below failed ~8 support",
        )
    ], [
        ThesisRule(
            id="bear-invalidate-reclaim-820",
            kind="close_above",
            price=FAILED_BREAKOUT,
            timeframe="4h",
            description="4H reclaim of the failed-breakout region",
        )
    ]


def _open_bear(ledger: ThesisLedger, **kwargs):
    confirm, invalidate = _bear_rules()
    defaults = dict(
        symbol="AVAXUSDT",
        direction="bear",
        kind="failed_breakout_continuation",
        created_at=SEPTEMBER,
        confirmation_rules=confirm,
        invalidation_rules=invalidate,
        evidence=["repeated failure near 8.15-8.20"],
        counter_evidence=["5m bounce risk"],
    )
    defaults.update(kwargs)
    return ledger.open(**defaults)


def test_hypothesis_contract_fields_present():
    thesis = _open_bear(ThesisLedger())
    payload = thesis.to_dict()
    for key in (
        "evidence",
        "counter_evidence",
        "confirmation_rules",
        "invalidation_rules",
        "status",
        "version",
        "id",
        "symbol",
        "direction",
        "kind",
        "created_at",
        "closed_at",
        "closure_reason",
    ):
        assert key in payload
    assert payload["status"] == "active"
    assert payload["version"] == 1
    assert payload["direction"] == "bear"
    assert payload["closed_at"] is None
    assert thesis.evidence[0].text.startswith("repeated failure")
    assert thesis.invalidation_rules[0].price == FAILED_BREAKOUT


def test_open_requires_confirmation_and_invalidation():
    ledger = ThesisLedger()
    confirm, invalidate = _bear_rules()
    with pytest.raises(ValueError, match="confirmation_rules"):
        ledger.open(
            symbol="AVAXUSDT",
            direction="bear",
            kind="x",
            created_at=SEPTEMBER,
            confirmation_rules=(),
            invalidation_rules=invalidate,
        )
    with pytest.raises(ValueError, match="invalidation_rules"):
        ledger.open(
            symbol="AVAXUSDT",
            direction="bull",
            kind="x",
            created_at=SEPTEMBER,
            confirmation_rules=confirm,
            invalidation_rules=(),
        )


def test_in_place_setattr_on_active_thesis_is_rejected():
    thesis = _open_bear(ThesisLedger())
    with pytest.raises(Exception):
        thesis.status = "closed"  # type: ignore[misc]
    with pytest.raises(Exception):
        thesis.invalidation_rules[0].price = 7.50  # type: ignore[misc]


def test_mutate_invalidation_on_active_thesis_is_rejected():
    ledger = ThesisLedger()
    thesis = _open_bear(ledger)
    original = thesis.invalidation_fingerprint
    with pytest.raises(ImmutableInvalidationError):
        thesis.with_invalidation_rules(
            [ThesisRule("moved", "close_above", 7.80, "4h", "moved lower")]
        )
    with pytest.raises(ImmutableInvalidationError, match="cannot move invalidation"):
        ledger.move_invalidation(thesis.id, "bear-invalidate-reclaim-820", 7.80)
    with pytest.raises(ImmutableInvalidationError, match="cannot replace"):
        ledger.replace_invalidation_rules(
            thesis.id,
            [ThesisRule("moved", "close_above", 7.80, "4h")],
        )
    live = ledger.get(thesis.id)
    assert live.status == "active"
    assert live.invalidation_rules[0].price == FAILED_BREAKOUT
    assert live.invalidation_fingerprint == original
    rejected = [e for e in ledger.events() if e.action == "rejected_invalidation_move"]
    assert len(rejected) >= 2


def test_close_on_fire_works_and_leaves_rules_frozen():
    ledger = ThesisLedger()
    thesis = _open_bear(ledger)
    fingerprint = thesis.invalidation_fingerprint
    reclaim = PriceObservation(
        at=datetime(2026, 9, 14, 0, 0, tzinfo=timezone.utc),
        timeframe="4h",
        open=8.10,
        high=8.31,
        low=8.08,
        close=8.25,
    )
    closed = ledger.fire(thesis.id, reclaim)
    assert closed.status == "closed"
    assert closed.closure_reason == "invalidation_fired"
    assert closed.fired_rule_ids == ("bear-invalidate-reclaim-820",)
    assert closed.invalidation_rules[0].price == FAILED_BREAKOUT
    assert closed.invalidation_fingerprint == fingerprint
    assert closed.closed_at == reclaim.at
    stored = ledger.get(thesis.id)
    assert stored.status == "closed"
    assert stored.invalidation_rules[0].price == FAILED_BREAKOUT
    assert any(e.action == "invalidated" for e in ledger.events())


def test_non_triggering_observation_does_not_close():
    ledger = ThesisLedger()
    thesis = _open_bear(ledger)
    still = ledger.fire(
        thesis.id,
        PriceObservation(
            at=SEPTEMBER,
            timeframe="4h",
            open=7.40,
            high=7.55,
            low=7.30,
            close=7.42,
        ),
    )
    assert still.status == "active"
    assert still.closed_at is None
    assert still.invalidation_rules[0].price == FAILED_BREAKOUT


def test_five_minute_relief_does_not_satisfy_four_hour_invalidation():
    ledger = ThesisLedger()
    thesis = _open_bear(ledger)
    bounce = PriceObservation(
        at=datetime(2026, 9, 13, 16, 5, tzinfo=timezone.utc),
        timeframe="5m",
        open=7.40,
        high=8.25,
        low=7.38,
        close=8.22,
    )
    still = ledger.fire(thesis.id, bounce)
    assert still.status == "active"
    assert still.fired_rule_ids == ()
    assert still.invalidation_rules[0].price == FAILED_BREAKOUT


def test_changed_reasoning_closes_old_version_and_opens_successor():
    ledger = ThesisLedger()
    old = _open_bear(ledger)
    at = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    new_invalidation = [
        ThesisRule(
            id="bear-invalidate-reclaim-850",
            kind="close_above",
            price=8.50,
            timeframe="4h",
            description="revised reclaim — new version only",
        )
    ]
    successor = ledger.revise(old.id, at=at, invalidation_rules=new_invalidation)
    prior = ledger.get(old.id)
    assert prior.status == "closed"
    assert prior.closure_reason == "superseded"
    assert prior.version == 1
    assert prior.invalidation_rules[0].price == FAILED_BREAKOUT
    assert prior.superseded_by == successor.id
    assert successor.status == "active"
    assert successor.version == 2
    assert successor.lineage_id == prior.lineage_id
    assert successor.supersedes == prior.id
    assert successor.invalidation_rules[0].price == 8.50
    assert successor.id != prior.id
    versions = ledger.lineage(prior.lineage_id)
    assert [t.version for t in versions] == [1, 2]


def test_revise_without_rule_change_is_rejected():
    ledger = ThesisLedger()
    thesis = _open_bear(ledger)
    with pytest.raises(ValueError, match="no rule change"):
        ledger.revise(thesis.id, at=SEPTEMBER)


def test_add_evidence_does_not_change_version_or_invalidation():
    ledger = ThesisLedger()
    thesis = _open_bear(ledger)
    updated = ledger.add_evidence(thesis.id, EvidenceItem("lower high confirmed", SEPTEMBER, "4h"))
    assert updated.version == 1
    assert updated.status == "active"
    assert updated.invalidation_rules[0].price == FAILED_BREAKOUT
    assert updated.evidence[-1].text == "lower high confirmed"


def test_closed_thesis_cannot_be_revised_or_refired():
    ledger = ThesisLedger()
    thesis = _open_bear(ledger)
    ledger.fire(
        thesis.id,
        PriceObservation(
            at=datetime(2026, 9, 14, 4, 0, tzinfo=timezone.utc),
            timeframe="4h",
            open=8.10,
            high=8.28,
            low=8.05,
            close=8.22,
        ),
    )
    with pytest.raises(ThesisClosedError):
        ledger.revise(
            thesis.id,
            at=datetime(2026, 9, 14, 8, 0, tzinfo=timezone.utc),
            invalidation_rules=[ThesisRule("x", "close_above", 8.80, "4h")],
        )
    with pytest.raises(ThesisClosedError):
        ledger.fire(
            thesis.id,
            PriceObservation(
                at=datetime(2026, 9, 14, 8, 0, tzinfo=timezone.utc),
                timeframe="4h",
                open=8.20,
                high=8.40,
                low=8.10,
                close=8.30,
            ),
        )
    with pytest.raises(ThesisClosedError):
        ledger.add_evidence(thesis.id, "hindsight rewrite")


def test_competing_bull_and_bear_theses_coexist():
    ledger = ThesisLedger()
    bear = _open_bear(ledger)
    bull = ledger.open(
        symbol="AVAXUSDT",
        direction="bull",
        kind="relief_reclaim",
        created_at=SEPTEMBER,
        confirmation_rules=[ThesisRule("bull-c", "close_above", FAILED_BREAKOUT, "4h")],
        invalidation_rules=[ThesisRule("bull-i", "close_below", FAILED_SUPPORT, "4h")],
        evidence=["bounce toward 8"],
    )
    active = ledger.active(symbol="AVAXUSDT")
    assert {t.direction for t in active} == {"bull", "bear"}
    assert bear.id != bull.id


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        _open_bear(ThesisLedger(), created_at=datetime(2026, 9, 13, 12, 0))


def test_september_relief_bounce_does_not_rewrite_fired_bear_invalidation():
    """September 2026 spirit: once the bear reclaim invalidation fires, a later
    bounce cannot move that version's price. Fixture files are not edited.
    """
    ledger = ThesisLedger()
    bear = september_failed_breakout_bear(ledger, created_at=SEPTEMBER)
    assert bear.invalidation_rules[0].price == FAILED_BREAKOUT

    relief = PriceObservation(
        at=datetime(2026, 9, 16, 14, 5, tzinfo=timezone.utc),
        timeframe="5m",
        open=7.40,
        high=RELIEF_HIGH,
        low=7.35,
        close=RELIEF_CLOSE,
    )
    after_bounce = ledger.fire(bear.id, relief)
    assert after_bounce.status == "active"
    assert after_bounce.invalidation_rules[0].price == FAILED_BREAKOUT

    with pytest.raises(ImmutableInvalidationError):
        ledger.move_invalidation(bear.id, "bear-invalidate-reclaim-820", 7.80)

    fired_at = datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc)
    closed = ledger.fire(
        bear.id,
        PriceObservation(
            at=fired_at,
            timeframe="4h",
            open=8.05,
            high=8.28,
            low=8.01,
            close=8.24,
        ),
    )
    assert closed.status == "closed"
    assert closed.closure_reason == "invalidation_fired"
    fired_price = closed.invalidation_rules[0].price
    fired_fp = closed.invalidation_fingerprint
    assert fired_price == FAILED_BREAKOUT

    later_bounce = PriceObservation(
        at=datetime(2026, 9, 18, 3, 10, tzinfo=timezone.utc),
        timeframe="15m",
        open=7.90,
        high=8.10,
        low=7.85,
        close=8.02,
    )
    with pytest.raises(ThesisClosedError, match="do not move"):
        ledger.fire(bear.id, later_bounce)
    with pytest.raises(ImmutableInvalidationError):
        ledger.move_invalidation(bear.id, "bear-invalidate-reclaim-820", 8.50)
    with pytest.raises(ImmutableInvalidationError):
        closed.with_invalidation_rules(
            [ThesisRule("rewritten", "close_above", 7.60, "4h")]
        )

    frozen = ledger.get(bear.id)
    assert frozen.status == "closed"
    assert frozen.closure_reason == "invalidation_fired"
    assert frozen.invalidation_rules[0].price == FAILED_BREAKOUT
    assert frozen.invalidation_rules[0].price == fired_price
    assert frozen.invalidation_fingerprint == fired_fp
    assert frozen.closed_at == fired_at
    assert ledger.active(direction="bear") == ()


def test_bull_thesis_cannot_move_invalidation_lower_after_eight_fails():
    ledger = ThesisLedger()
    bull = ledger.open(
        symbol="AVAXUSDT",
        direction="bull",
        kind="reclaim_eight",
        created_at=SEPTEMBER,
        evidence=["recovery into ~8"],
        confirmation_rules=[ThesisRule("bull-c", "close_above", FAILED_BREAKOUT, "4h")],
        invalidation_rules=[ThesisRule("bull-i", "close_below", FAILED_SUPPORT, "4h")],
    )
    broken = ledger.fire(
        bull.id,
        PriceObservation(
            at=datetime(2026, 9, 13, 20, 0, tzinfo=timezone.utc),
            timeframe="4h",
            open=8.05,
            high=8.10,
            low=7.88,
            close=7.92,
        ),
    )
    assert broken.closure_reason == "invalidation_fired"
    assert broken.invalidation_rules[0].price == FAILED_SUPPORT
    with pytest.raises(ImmutableInvalidationError):
        ledger.move_invalidation(bull.id, "bull-i", 7.40)
    assert ledger.get(bull.id).invalidation_rules[0].price == FAILED_SUPPORT
