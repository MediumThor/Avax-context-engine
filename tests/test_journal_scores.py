from __future__ import annotations

from datetime import datetime, timezone

from packages.journal import ForecastJournal
from packages.models import score_journaled_forecasts


def test_journal_scores_ignore_unmatured_and_future_rows(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    as_of = datetime(2026, 9, 2, tzinfo=timezone.utc)
    journal.get_or_append(
        forecast_id="f-old",
        symbol="AVAXUSDT",
        forecasted_at="2026-09-01T00:00:00+00:00",
        model_id="freqai.quantiles.research.v1",
        payload={
            "forecasted_at": "2026-09-01T00:00:00+00:00",
            "horizons": [
                {
                    "h": 1,
                    "p_close_above_origin": 0.6,
                    "q10_cum_log_return": -0.01,
                    "q90_cum_log_return": 0.01,
                }
            ],
        },
    )
    journal.get_or_append_outcome(
        "f-old",
        1,
        {
            "h": 1,
            "matured_at": "2026-09-01T00:05:00+00:00",
            "realized_close_above_origin": True,
            "realized_cum_log_return": 0.002,
        },
    )
    journal.get_or_append(
        forecast_id="f-future",
        symbol="AVAXUSDT",
        forecasted_at="2026-09-03T00:00:00+00:00",
        model_id="freqai.quantiles.research.v1",
        payload={
            "forecasted_at": "2026-09-03T00:00:00+00:00",
            "horizons": [{"h": 1, "p_close_above_origin": 0.9}],
        },
    )
    scored = score_journaled_forecasts(journal, "AVAXUSDT", as_of=as_of)
    assert scored["horizons"]["1"]["probability"]["sample_count"] == 1
    assert scored["horizons"]["1"]["probability"]["brier"] is None
    journal.close()
