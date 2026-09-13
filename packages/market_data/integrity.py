"""Read-only integrity checks for immutable OHLCV series.

Does not write to CandleStore. Manifest checksums reuse CandleStore._payload
so they stay byte-identical to CandleStore.manifest (canonical JSON + ``\\n``
delimited SHA-256).
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Literal, Mapping, Sequence

from packages.context_engine.models import Candle
from packages.market_data.store import CandleStore

FIVE_MINUTES = 5
FIVE_MINUTES_SECONDS = FIVE_MINUTES * 60
IssueKind = Literal[
    "gap",
    "duplicate",
    "ohlc_violation",
    "unaligned",
    "naive_timestamp",
]

_CANDLE_FIELDS = ("symbol", "timeframe", "open_time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True, slots=True)
class IntegrityIssue:
    kind: IssueKind
    open_time: str | None
    detail: str
    index: int | None = None


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    ok: bool
    expected_slots: int
    observed_count: int
    unique_open_times: int
    issues: tuple[IntegrityIssue, ...]

    def of_kind(self, kind: IssueKind) -> tuple[IntegrityIssue, ...]:
        return tuple(issue for issue in self.issues if issue.kind == kind)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("open_time must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat()


def _is_5m_aligned(value: datetime) -> bool:
    aware = _as_utc(value)
    return aware.microsecond == 0 and int(aware.timestamp()) % FIVE_MINUTES_SECONDS == 0


def _floor_5m(value: datetime) -> datetime:
    aware = _as_utc(value)
    epoch = int(aware.timestamp())
    return datetime.fromtimestamp(epoch - (epoch % FIVE_MINUTES_SECONDS), tz=timezone.utc)


def _ceil_5m(value: datetime) -> datetime:
    aware = _as_utc(value)
    epoch = int(aware.timestamp())
    remainder = epoch % FIVE_MINUTES_SECONDS
    if remainder == 0 and aware.microsecond == 0:
        return datetime.fromtimestamp(epoch, tz=timezone.utc)
    return datetime.fromtimestamp(epoch + (FIVE_MINUTES_SECONDS - remainder), tz=timezone.utc)


def expected_5m_grid(start: datetime, end: datetime) -> list[datetime]:
    """Inclusive UTC 5m open-time grid covering ``[start, end]``.

    Unaligned endpoints are snapped onto the exchange 5m grid (ceil start,
    floor end). Returns an empty list when the snapped window is inverted.
    """
    first = _ceil_5m(start)
    last = _floor_5m(end)
    if first > last:
        return []
    step = timedelta(minutes=FIVE_MINUTES)
    grid: list[datetime] = []
    cursor = first
    while cursor <= last:
        grid.append(cursor)
        cursor += step
    return grid


def _record_open_time(record: Candle | Mapping[str, Any]) -> datetime | None:
    raw = record.open_time if isinstance(record, Candle) else record.get("open_time")
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, str):
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed
    return None


def _record_field(record: Candle | Mapping[str, Any], name: str) -> Any:
    if isinstance(record, Candle):
        return getattr(record, name)
    return record.get(name)


def canonical_payload(candle: Candle) -> str:
    """Canonical per-candle JSON used by the immutable store."""
    return CandleStore._payload(candle)


def manifest_sha256(candles: Sequence[Candle], *, chronological: bool = True) -> str:
    """Checksum matching ``CandleStore.manifest`` (sorted load order by default)."""
    series = sorted(candles, key=lambda c: c.open_time) if chronological else list(candles)
    digest = hashlib.sha256()
    for candle in series:
        digest.update(canonical_payload(candle).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def verify_manifest_sha256(
    candles: Sequence[Candle],
    expected_sha256: str,
    *,
    chronological: bool = True,
) -> bool:
    return manifest_sha256(candles, chronological=chronological) == expected_sha256


def find_gaps(records: Sequence[Candle | Mapping[str, Any]]) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []
    times: list[datetime] = []
    for index, record in enumerate(records):
        open_time = _record_open_time(record)
        if open_time is None:
            issues.append(
                IntegrityIssue("gap", None, "record missing open_time", index)
            )
            continue
        if open_time.tzinfo is None:
            issues.append(
                IntegrityIssue(
                    "naive_timestamp",
                    open_time.isoformat(),
                    "open_time is timezone-naive; internal grid is UTC",
                    index,
                )
            )
            continue
        aware = _as_utc(open_time)
        if not _is_5m_aligned(aware):
            issues.append(
                IntegrityIssue(
                    "unaligned",
                    _iso(aware),
                    "open_time is not aligned to the UTC 5m grid",
                    index,
                )
            )
        times.append(aware)
    if not times:
        return issues
    observed = {dt.isoformat() for dt in times if _is_5m_aligned(dt)}
    for slot in expected_5m_grid(min(times), max(times)):
        if slot.isoformat() not in observed:
            issues.append(
                IntegrityIssue(
                    "gap",
                    slot.isoformat(),
                    "missing closed 5m bar on expected UTC grid",
                    None,
                )
            )
    return issues


def find_duplicates(records: Sequence[Candle | Mapping[str, Any]]) -> list[IntegrityIssue]:
    grouped: dict[str, list[int]] = defaultdict(list)
    payloads: dict[str, set[str]] = defaultdict(set)
    for index, record in enumerate(records):
        open_time = _record_open_time(record)
        if open_time is None:
            continue
        key = open_time.isoformat() if open_time.tzinfo else open_time.isoformat()
        grouped[key].append(index)
        if isinstance(record, Candle):
            payloads[key].add(canonical_payload(record))
        else:
            payloads[key].add(
                "|".join(str(_record_field(record, field)) for field in _CANDLE_FIELDS)
            )
    issues: list[IntegrityIssue] = []
    for open_time, indexes in grouped.items():
        if len(indexes) < 2:
            continue
        conflict = len(payloads[open_time]) > 1
        detail = (
            f"open_time appears {len(indexes)} times with conflicting payloads"
            if conflict
            else f"open_time appears {len(indexes)} times"
        )
        issues.append(IntegrityIssue("duplicate", open_time, detail, indexes[0]))
    return issues


def find_ohlc_violations(records: Sequence[Candle | Mapping[str, Any]]) -> list[IntegrityIssue]:
    issues: list[IntegrityIssue] = []
    for index, record in enumerate(records):
        open_time = _record_open_time(record)
        stamp = None
        if isinstance(open_time, datetime):
            stamp = open_time.isoformat() if open_time.tzinfo is None else _iso(open_time)
        values: dict[str, float] = {}
        missing: list[str] = []
        non_finite: list[str] = []
        for name in ("open", "high", "low", "close", "volume"):
            raw = _record_field(record, name)
            if raw is None:
                missing.append(name)
                continue
            try:
                number = float(raw)
            except (TypeError, ValueError):
                non_finite.append(name)
                continue
            if not math.isfinite(number):
                non_finite.append(name)
                continue
            values[name] = number
        problems: list[str] = []
        if missing:
            problems.append("missing " + ", ".join(missing))
        if non_finite:
            problems.append("non-finite " + ", ".join(non_finite))
        if {"open", "high", "low", "close"} <= values.keys():
            open_, high, low, close = values["open"], values["high"], values["low"], values["close"]
            if high < low:
                problems.append("high < low")
            if high < max(open_, close):
                problems.append("high below max(open, close)")
            if low > min(open_, close):
                problems.append("low above min(open, close)")
        if "volume" in values and values["volume"] < 0:
            problems.append("volume is negative")
        if problems:
            issues.append(
                IntegrityIssue("ohlc_violation", stamp, "; ".join(problems), index)
            )
    return issues


def audit_ohlcv(records: Sequence[Candle | Mapping[str, Any]]) -> IntegrityReport:
    """Combine gap, duplicate, alignment, and OHLC checks. Never mutates input."""
    issues = [
        *find_gaps(records),
        *find_duplicates(records),
        *find_ohlc_violations(records),
    ]
    aware_times: list[datetime] = []
    for record in records:
        open_time = _record_open_time(record)
        if isinstance(open_time, datetime) and open_time.tzinfo is not None:
            aware_times.append(_as_utc(open_time))
    expected_slots = len(expected_5m_grid(min(aware_times), max(aware_times))) if aware_times else 0
    unique = {dt.isoformat() for dt in aware_times}
    return IntegrityReport(
        ok=not issues,
        expected_slots=expected_slots,
        observed_count=len(records),
        unique_open_times=len(unique),
        issues=tuple(issues),
    )


def iter_issue_kinds(report: IntegrityReport) -> Iterable[IssueKind]:
    seen: set[IssueKind] = set()
    for issue in report.issues:
        if issue.kind not in seen:
            seen.add(issue.kind)
            yield issue.kind
