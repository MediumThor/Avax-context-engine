from __future__ import annotations

from packages.journal import ForecastJournal
from packages.models.direction_cal import CALIBRATION_REF, empirical_signed_p
from packages.models.freqai_quantiles import emit_quantile_forecast
from packages.models.outcomes import mature_outcomes
from tests.test_freqai_quantiles import as_of_index, make_5m, mutate_after


def test_empirical_signed_p_needs_bucket_count():
    assert empirical_signed_p([0.1] * 5, [1.0] * 5, 0.2) is None
    p = empirical_signed_p([0.1] * 6 + [-0.2] * 4, [1.0] * 10, 0.3)
    assert p == 0.6


def test_empirical_signed_p_uses_matching_sign_bucket():
    targets = [0.2] * 8 + [-0.3] * 8
    scores = [1.0] * 8 + [-1.0] * 8
    assert empirical_signed_p(targets, scores, 0.4) == 1.0
    assert empirical_signed_p(targets, scores, -0.4) == 0.0


def test_mature_outcomes_do_not_rewrite_forecast(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    candles = make_5m(80)
    origin = 50
    payload = {
        "forecasted_at": candles[origin].close_time().isoformat(),
        "origin_close": candles[origin].close,
        "model_id": "test",
        "horizons": [{"h": 1}],
    }
    digest = journal.append_forecast(
        "f-origin",
        "AVAXUSDT",
        payload["forecasted_at"],
        "test",
        payload,
    )
    before = journal.get_forecast("f-origin")
    stats = mature_outcomes(journal, candles, "AVAXUSDT")
    after = journal.get_forecast("f-origin")
    assert after["sha256"] == digest
    assert after["payload"] == before["payload"]
    assert stats["outcomes_written"] >= 10
    assert journal.has_outcome("f-origin", 1)
    again = mature_outcomes(journal, candles, "AVAXUSDT")
    assert again["outcomes_written"] == 0
    journal.close()


def test_replay_as_of_does_not_mature_future_horizons(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    candles = make_5m(80)
    origin = 50
    payload = {
        "forecasted_at": candles[origin].close_time().isoformat(),
        "origin_close": candles[origin].close,
        "horizons": [],
    }
    journal.append_forecast("f-asof", "AVAXUSDT", payload["forecasted_at"], "test", payload)
    as_of = candles[origin + 2].close_time()
    mature_outcomes(journal, candles, "AVAXUSDT", as_of=as_of)
    assert journal.has_outcome("f-asof", 1)
    assert journal.has_outcome("f-asof", 2)
    assert not journal.has_outcome("f-asof", 3)
    journal.close()


def test_quantile_emits_calibrated_p_from_known_origins():
    candles = make_5m(160)
    payload = emit_quantile_forecast(candles, as_of=as_of_index(candles, 149), backend="python")
    assert payload["calibration_ref"] == CALIBRATION_REF
    for row in payload["horizons"]:
        assert row["p_close_above_origin"] is not None
        assert 0.0 <= row["p_close_above_origin"] <= 1.0
        assert row["confidence_source"] == "calibrated"


def test_future_perturbation_does_not_change_p_at_t():
    candles = make_5m(160)
    origin = 140
    as_of = as_of_index(candles, origin)
    before = emit_quantile_forecast(candles, as_of=as_of, backend="python")
    after = emit_quantile_forecast(mutate_after(candles, origin + 1), as_of=as_of, backend="python")
    assert [row["p_close_above_origin"] for row in before["horizons"]] == [
        row["p_close_above_origin"] for row in after["horizons"]
    ]


def test_runtime_journals_prior_origin_and_matures(tmp_path):
    from services.api.runtime import PrototypeRuntime

    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    out = runtime.forecast("AVAXUSDT")
    assert out["outcomes"]["outcomes_written"] >= 1
    rows = runtime.journal.list_forecasts("AVAXUSDT")
    assert len(rows) >= 2
    matured = [row for row in rows if runtime.journal.list_outcomes(row["id"])]
    assert matured
    first_hash = runtime.journal.get_forecast(matured[0]["id"])["sha256"]
    runtime.forecast("AVAXUSDT")
    assert runtime.journal.get_forecast(matured[0]["id"])["sha256"] == first_hash
    runtime.close()
