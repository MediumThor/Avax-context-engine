import sqlite3
from packages.journal import ForecastJournal


def test_forecast_is_append_only(tmp_path):
    journal=ForecastJournal(tmp_path/"journal.db")
    journal.append_forecast("f1","AVAXUSDT","2026-01-01T00:00:00Z","m1",{"h":[1,2,3]})
    try:
        journal.append_forecast("f1","AVAXUSDT","2026-01-01T00:00:00Z","m1",{"h":[9]})
        assert False,"duplicate should fail"
    except sqlite3.IntegrityError:
        pass
    assert journal.get_forecast("f1")["payload"]=={"h":[1,2,3]}
    journal.close()
