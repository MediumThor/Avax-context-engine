"""WAVE2-36: candles after T must not change the snapshot or journal payload at T."""

from __future__ import annotations

from packages.context_engine import ContextEngine
from packages.harness.synthesis import build_analysis
from packages.journal import ForecastJournal

from tests.leakage.wave2.support import (
    as_unclosed,
    make_5m,
    mutate_after,
    snapshot_at,
)


def test_mutating_closed_candles_after_t_leaves_snapshot_at_t_unchanged():
    xs = make_5m(360)
    t = 250
    as_of = xs[t - 1].open_time
    mutated = mutate_after(xs, t)
    before = snapshot_at(xs, as_of).to_dict()
    after = snapshot_at(mutated, as_of).to_dict()
    assert before == after
    assert before["as_of"] == as_of


def test_unclosed_future_candles_injected_into_engine_do_not_change_snapshot_at_t():
    xs = make_5m(360)
    t = 250
    # Call the engine directly so is_closed filtering is what is under test.
    before = ContextEngine().build_snapshot(xs[:t])
    injected = xs[:t] + as_unclosed(xs[t:])
    after = ContextEngine().build_snapshot(injected)
    assert before.to_dict() == after.to_dict()


def test_journal_payload_at_t_unchanged_when_future_is_perturbed(tmp_path):
    xs = make_5m(360)
    t = 250
    as_of = xs[t - 1].open_time
    payload = build_analysis(snapshot_at(xs, as_of))
    journal = ForecastJournal(tmp_path / "wave2-36-journal.db")
    digest = journal.append_forecast(
        "wave2-36-t",
        "AVAXUSDT",
        as_of.isoformat(),
        "wave2-36-leakage",
        payload,
    )
    mutated = mutate_after(xs, t)
    replayed = build_analysis(snapshot_at(mutated, as_of))
    stored = journal.get_forecast("wave2-36-t")
    assert replayed == payload
    assert stored["payload"] == payload
    assert stored["sha256"] == digest
    journal.close()
