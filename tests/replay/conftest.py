"""Pytest fixtures for WAVE2-37. Helpers live in tests/replay/helpers.py."""

from __future__ import annotations

import pytest

from packages.context_engine import ContextEngine
from packages.journal import ForecastJournal


@pytest.fixture
def engine() -> ContextEngine:
    return ContextEngine()


@pytest.fixture
def journal(tmp_path) -> ForecastJournal:
    store = ForecastJournal(tmp_path / "wave2-37-journal.db")
    yield store
    store.close()
