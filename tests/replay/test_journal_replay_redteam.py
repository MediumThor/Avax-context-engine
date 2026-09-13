"""WAVE2-37 red team: journal + snapshot replay leakage / journal-before-outcome.

Pytest collects by basename. This file must stay uniquely named — do not rename
to test_replay.py or test_leakage.py.

Required probes target APIs on main:
  ContextEngine.build_snapshot
  ForecastJournal.append_forecast / append_outcome / get_forecast

Optional probes that need packages.context_engine.replay skip when that module
is absent.
"""

from __future__ import annotations

from datetime import timedelta

from packages.context_engine import Candle, ContextEngine

from tests.replay.helpers import (
    canonical_sha256,
    declining_series,
    forecast_payload_at_t,
    higher_tf_view,
    iso_utc,
    make_candle,
    mutate_after,
    outcome_keys_present,
    period_end_5m,
    rising_from,
    try_import_replay,
)


def test_journal_record_at_t_unchanged_when_later_candles_mutated(engine, journal):
    candles = declining_series(384 + 48)
    t_index = 384
    known = candles[:t_index]
    snapshot = engine.build_snapshot(known)
    forecasted_at = iso_utc(period_end_5m(known[-1]))
    payload = forecast_payload_at_t(snapshot, forecasted_at)
    assert not outcome_keys_present(payload)

    digest = journal.append_forecast(
        "wave2-37-mut-later",
        snapshot.symbol,
        forecasted_at,
        "redteam-journal-replay",
        payload,
    )
    before = journal.get_forecast("wave2-37-mut-later")

    mutated = mutate_after(candles, t_index)
    replayed_prefix = engine.build_snapshot(mutated[:t_index])
    after = journal.get_forecast("wave2-37-mut-later")

    assert after["payload"] == payload == before["payload"]
    assert after["sha256"] == digest == before["sha256"]
    assert after["payload"]["regime_4h"] == snapshot.timeframes["4h"].regime
    assert replayed_prefix.to_dict() == snapshot.to_dict()
    future_closes = {c.close for c in mutated[t_index:]}
    assert snapshot.timeframes["4h"].close not in future_closes
    assert after["payload"]["regime_4h_close"] not in future_closes


def test_forecast_written_at_t_has_no_outcome_fields(engine, journal):
    known = declining_series(384)
    snapshot = engine.build_snapshot(known)
    forecasted_at = iso_utc(period_end_5m(known[-1]))
    payload = forecast_payload_at_t(snapshot, forecasted_at)

    digest = journal.append_forecast(
        "wave2-37-before-outcome",
        snapshot.symbol,
        forecasted_at,
        "redteam-journal-before-outcome",
        payload,
    )
    stored = journal.get_forecast("wave2-37-before-outcome")
    assert stored["payload"] == payload
    assert stored["sha256"] == digest
    assert outcome_keys_present(stored["payload"]) == set()
    assert "horizons" in stored["payload"]
    assert [row["h"] for row in stored["payload"]["horizons"]] == list(range(1, 11))
    for row in stored["payload"]["horizons"]:
        assert outcome_keys_present(row) == set()

    later = rising_from(known[-1], n=10)
    later_snapshot = engine.build_snapshot(known + later)
    realized = later_snapshot.timeframes["5m"].close / snapshot.timeframes["5m"].close
    journal.append_outcome(
        "wave2-37-before-outcome",
        1,
        {
            "forecast_id": "wave2-37-before-outcome",
            "schema_version": "1",
            "h": 1,
            "matured_at": iso_utc(period_end_5m(later[-1])),
            "realized_cum_log_return": float(realized - 1.0),
            "realized_close_above_origin": later_snapshot.timeframes["5m"].close
            > snapshot.timeframes["5m"].close,
            "realized_max_favorable_excursion": 0.0,
            "realized_max_adverse_excursion": 0.0,
            "scores": {"abs_error": 0.0},
        },
    )
    after_outcome = journal.get_forecast("wave2-37-before-outcome")
    assert after_outcome["payload"] == payload
    assert after_outcome["sha256"] == digest
    assert outcome_keys_present(after_outcome["payload"]) == set()

    outcome_row = journal.db.execute(
        "SELECT payload_json FROM outcomes WHERE forecast_id=? AND horizon=?",
        ("wave2-37-before-outcome", 1),
    ).fetchone()
    assert outcome_row is not None
    assert "realized_cum_log_return" in outcome_row[0]


def test_unfinished_parent_candles_do_not_change_higher_tf_evidence(engine):
    complete_parents = declining_series(48 * 8)
    baseline = engine.build_snapshot(complete_parents)
    assert "4h" in baseline.timeframes
    baseline_htf = higher_tf_view(baseline)

    unfinished_bounce = make_candle(
        len(complete_parents),
        open_price=complete_parents[-1].close,
        close=complete_parents[-1].close + 3.0,
        is_closed=False,
    )
    overlapping_unfinished = Candle(
        complete_parents[-1].symbol,
        "5m",
        complete_parents[-1].open_time,
        1.0,
        9.0,
        0.5,
        8.5,
        99999.0,
        is_closed=False,
    )
    with_unfinished = engine.build_snapshot(
        complete_parents + [unfinished_bounce, overlapping_unfinished]
    )
    assert with_unfinished.to_dict() == baseline.to_dict()
    assert higher_tf_view(with_unfinished) == baseline_htf

    incomplete_4h = rising_from(complete_parents[-1], n=10, step=0.08)
    assert len(incomplete_4h) < 48
    after_partial = engine.build_snapshot(complete_parents + incomplete_4h)
    assert higher_tf_view(after_partial) == baseline_htf
    assert after_partial.timeframes["4h"].evidence == baseline.timeframes["4h"].evidence
    assert after_partial.timeframes["4h"].regime == baseline.timeframes["4h"].regime
    assert after_partial.timeframes["4h"].as_of == baseline.timeframes["4h"].as_of
    assert after_partial.timeframes["4h"].close == baseline.timeframes["4h"].close


def test_replaying_the_same_raw_series_is_deterministic(engine, journal):
    first_series = declining_series(96)
    second_series = declining_series(96)
    first = engine.build_snapshot(first_series)
    second = engine.build_snapshot(list(first_series))
    third = ContextEngine().build_snapshot(second_series)
    assert first.to_dict() == second.to_dict() == third.to_dict()

    forecasted_at = iso_utc(period_end_5m(first_series[-1]))
    payload_a = forecast_payload_at_t(first, forecasted_at)
    payload_b = forecast_payload_at_t(third, forecasted_at)
    assert payload_a == payload_b
    assert canonical_sha256(payload_a) == canonical_sha256(payload_b)

    digest_a = journal.append_forecast(
        "wave2-37-det-a",
        first.symbol,
        forecasted_at,
        "redteam-deterministic-a",
        payload_a,
    )
    digest_b = journal.append_forecast(
        "wave2-37-det-b",
        third.symbol,
        forecasted_at,
        "redteam-deterministic-b",
        payload_b,
    )
    assert digest_a == digest_b
    assert journal.get_forecast("wave2-37-det-a")["payload"] == journal.get_forecast(
        "wave2-37-det-b"
    )["payload"]


def test_5m_bounce_does_not_rewrite_journaled_4h_regime_at_t(engine, journal):
    decline = declining_series(48 * 8, start_price=12.0, step=-0.02)
    snapshot_at_t = engine.build_snapshot(decline)
    assert snapshot_at_t.timeframes["4h"].regime == "bearish"
    journaled_4h = {
        "regime": snapshot_at_t.timeframes["4h"].regime,
        "as_of": iso_utc(snapshot_at_t.timeframes["4h"].as_of),
        "close": snapshot_at_t.timeframes["4h"].close,
        "evidence": list(snapshot_at_t.timeframes["4h"].evidence),
    }
    forecasted_at = iso_utc(period_end_5m(decline[-1]))
    payload = forecast_payload_at_t(snapshot_at_t, forecasted_at)
    digest = journal.append_forecast(
        "wave2-37-4h-at-t",
        snapshot_at_t.symbol,
        forecasted_at,
        "redteam-4h-parent",
        payload,
    )

    bounce = rising_from(decline[-1], n=12, step=0.08)
    after_bounce = engine.build_snapshot(decline + bounce)
    stored = journal.get_forecast("wave2-37-4h-at-t")

    assert stored["sha256"] == digest
    assert stored["payload"]["regime_4h"] == "bearish"
    assert stored["payload"]["regime_4h"] == journaled_4h["regime"]
    assert stored["payload"]["regime_4h_as_of"] == journaled_4h["as_of"]
    assert stored["payload"]["regime_4h_close"] == journaled_4h["close"]
    assert stored["payload"]["regime_4h_evidence"] == journaled_4h["evidence"]
    assert stored["payload"] == payload
    # Incomplete new 4H parent (12 of 48 five-minute bars) must not rewrite 4H.
    assert after_bounce.timeframes["4h"].regime == "bearish"
    assert after_bounce.timeframes["4h"].as_of == snapshot_at_t.timeframes["4h"].as_of
    assert after_bounce.timeframes["4h"].close == snapshot_at_t.timeframes["4h"].close
    assert after_bounce.timeframes["4h"].evidence == snapshot_at_t.timeframes["4h"].evidence
    last_4h_close = snapshot_at_t.timeframes["4h"].as_of + timedelta(hours=4)
    assert last_4h_close <= period_end_5m(bounce[-1]) < last_4h_close + timedelta(hours=4)


def test_optional_replay_module_as_of_t_ignores_mutated_future_candles():
    replay = try_import_replay()
    candles = declining_series(160)
    as_of = period_end_5m(candles[79])
    original = replay.snapshot_as_of(candles, as_of)
    perturbed = mutate_after(candles, 80)
    after = replay.snapshot_as_of(perturbed, as_of)
    assert after == original
    assert after.payload_sha256 == original.payload_sha256


def test_optional_replay_module_same_series_is_order_independent():
    replay = try_import_replay()
    candles = declining_series(120)
    shuffled = list(reversed(candles))
    first = replay.replay(candles)
    second = replay.replay(shuffled)
    assert first.snapshots == second.snapshots
    if hasattr(replay, "replay_bytes"):
        assert replay.replay_bytes(candles) == replay.replay_bytes(shuffled)
