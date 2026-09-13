"""WAVE2-36: later-horizon closes must not appear as features at T."""

from __future__ import annotations

import inspect

import pytest

from packages.harness.synthesis import build_analysis
from packages.journal import ForecastJournal
from packages.models import evaluate_baselines

from tests.leakage.wave2.support import (
    forbidden_feature_paths,
    jsonable,
    make_5m,
    mutate_after,
    snapshot_at,
    try_import_assembler,
)

BASELINE_METRIC_KEYS = {"zero", "drift20", "sample_count"}


def test_journal_and_baseline_payloads_omit_future_close_feature_columns(tmp_path):
    xs = make_5m(360, start=10.0, step=0.002)
    t = 300
    as_of = xs[t - 1].open_time
    snap = snapshot_at(xs, as_of)
    payload = {
        "analysis": build_analysis(snap),
        "snapshot": snap.to_dict(),
        "baselines": evaluate_baselines(xs[:t], horizons=10),
    }
    hits = forbidden_feature_paths(payload)
    assert hits == [], f"future-horizon close columns used as features: {hits}"

    for horizon, block in payload["baselines"].items():
        assert horizon in {str(i) for i in range(1, 11)}
        assert set(block) <= BASELINE_METRIC_KEYS
        assert "close" not in block
        assert "future_close" not in block
        assert "features" not in block

    journal = ForecastJournal(tmp_path / "wave2-36-targets.db")
    journal.append_forecast(
        "wave2-36-targets",
        "AVAXUSDT",
        as_of.isoformat(),
        "wave2-36-leakage",
        jsonable(payload),
    )
    stored = journal.get_forecast("wave2-36-targets")["payload"]
    assert forbidden_feature_paths(stored) == []
    journal.close()


def test_optional_feature_assembler_ignores_mutated_future_or_skips():
    assemble = try_import_assembler()
    if assemble is None:
        pytest.skip("optional WAVE-2 feature assembler is not importable yet")

    xs = make_5m(360, start=10.0, step=0.002)
    t = 280
    as_of = xs[t - 1].open_time
    mutated = mutate_after(xs, t)
    params = inspect.signature(assemble).parameters
    try:
        if {"candles", "as_of"} <= set(params):
            before = assemble(candles=xs, as_of=as_of)
            after = assemble(candles=mutated, as_of=as_of)
        elif "candles" in params:
            before = assemble(candles=xs[:t])
            after = assemble(candles=mutated[:t])
        else:
            pytest.skip("feature assembler signature is not callable from this probe")
    except TypeError:
        pytest.skip("feature assembler signature is not callable from this probe")

    before_j = jsonable(before)
    after_j = jsonable(after)
    assert before_j == after_j
    hits = forbidden_feature_paths(before_j)
    assert hits == [], f"assembler leaked future-close feature columns: {hits}"
