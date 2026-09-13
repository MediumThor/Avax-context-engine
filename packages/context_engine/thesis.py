"""Immutable-versioned bull/bear thesis ledger.

Constitution §3: every active thesis carries explicit confirmation and
invalidation before later candles arrive. Invalidation rules are frozen for a
version. Once a rule fires, the thesis is closed. Changed reasoning closes the
old version and opens a new one — it does not rewrite the dead version.

5m observations cannot satisfy or rewrite a higher-timeframe invalidation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Literal, Mapping, Sequence
import hashlib
import json
import uuid

Direction = Literal["bull", "bear"]
ThesisStatus = Literal["active", "closed"]
ClosureReason = Literal["invalidation_fired", "superseded", "retired"]
RuleKind = Literal["close_above", "close_below", "high_above", "low_below"]
EventAction = Literal[
    "opened",
    "closed",
    "invalidated",
    "superseded",
    "evidence_appended",
    "rejected_invalidation_move",
]


class ImmutableInvalidationError(Exception):
    """Raised when an agent tries to move invalidation on an existing version."""


class ThesisClosedError(Exception):
    """Raised when a closed thesis is asked to accept new reasoning or a re-fire."""


class ThesisNotFoundError(KeyError):
    """Raised when a thesis id is not in the ledger."""


def _require_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _new_token() -> str:
    return uuid.uuid4().hex[:12]


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    text: str
    observed_at: datetime | None = None
    timeframe: str | None = None
    source: str | None = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "timeframe": self.timeframe,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class ThesisRule:
    """A priced, timeframe-scoped confirmation or invalidation condition."""

    id: str
    kind: RuleKind
    price: float
    timeframe: str
    description: str = ""

    def __post_init__(self) -> None:
        if self.kind not in {"close_above", "close_below", "high_above", "low_below"}:
            raise ValueError(f"unsupported rule kind: {self.kind}")
        if not self.timeframe:
            raise ValueError("rule timeframe is required")
        if self.price != self.price:  # NaN
            raise ValueError("rule price must be finite")

    def fires_on(self, observation: object) -> bool:
        """True only when the observation timeframe matches this rule."""
        timeframe = getattr(observation, "timeframe", None)
        if timeframe != self.timeframe:
            return False
        close = float(getattr(observation, "close"))
        high = float(getattr(observation, "high", close))
        low = float(getattr(observation, "low", close))
        if self.kind == "close_above":
            return close > self.price
        if self.kind == "close_below":
            return close < self.price
        if self.kind == "high_above":
            return high > self.price
        return low < self.price

    def fingerprint(self) -> str:
        payload = {
            "id": self.id,
            "kind": self.kind,
            "price": self.price,
            "timeframe": self.timeframe,
            "description": self.description,
        }
        return hashlib.sha256(_canonical(payload).encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PriceObservation:
    at: datetime
    timeframe: str
    close: float
    high: float
    low: float
    open: float | None = None

    def __post_init__(self) -> None:
        _require_aware("PriceObservation.at", self.at)
        if self.high < self.low:
            raise ValueError("high must be >= low")


@dataclass(frozen=True, slots=True)
class ThesisEvent:
    at: datetime
    thesis_id: str
    action: EventAction
    detail: str = ""


@dataclass(frozen=True, slots=True)
class Thesis:
    """One immutable version of a bull or bear hypothesis."""

    id: str
    lineage_id: str
    symbol: str
    direction: Direction
    kind: str
    status: ThesisStatus
    version: int
    created_at: datetime
    evidence: tuple[EvidenceItem, ...]
    counter_evidence: tuple[EvidenceItem, ...]
    confirmation_rules: tuple[ThesisRule, ...]
    invalidation_rules: tuple[ThesisRule, ...]
    closed_at: datetime | None = None
    closure_reason: ClosureReason | None = None
    fired_rule_ids: tuple[str, ...] = ()
    supersedes: str | None = None
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        _require_aware("created_at", self.created_at)
        if self.closed_at is not None:
            _require_aware("closed_at", self.closed_at)
        if self.version < 1:
            raise ValueError("version must be >= 1")
        if self.direction not in {"bull", "bear"}:
            raise ValueError("direction must be bull or bear")
        if self.status not in {"active", "closed"}:
            raise ValueError("status must be active or closed")
        if not self.confirmation_rules:
            raise ValueError("thesis requires confirmation_rules")
        if not self.invalidation_rules:
            raise ValueError("thesis requires invalidation_rules")
        if self.status == "active":
            if self.closed_at is not None or self.closure_reason is not None:
                raise ValueError("active thesis cannot carry closure fields")
            if self.fired_rule_ids:
                raise ValueError("active thesis cannot record fired invalidation")
            if self.superseded_by is not None:
                raise ValueError("active thesis cannot be superseded")
        else:
            if self.closed_at is None or self.closure_reason is None:
                raise ValueError("closed thesis requires closed_at and closure_reason")

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def invalidation_fingerprint(self) -> str:
        body = [rule.fingerprint() for rule in self.invalidation_rules]
        return hashlib.sha256(_canonical(body).encode()).hexdigest()

    @property
    def confirmation_fingerprint(self) -> str:
        body = [rule.fingerprint() for rule in self.confirmation_rules]
        return hashlib.sha256(_canonical(body).encode()).hexdigest()

    def matching_invalidations(self, observation: object) -> tuple[ThesisRule, ...]:
        return tuple(rule for rule in self.invalidation_rules if rule.fires_on(observation))

    def matching_confirmations(self, observation: object) -> tuple[ThesisRule, ...]:
        return tuple(rule for rule in self.confirmation_rules if rule.fires_on(observation))

    def with_invalidation_rules(self, _rules: Sequence[ThesisRule | Mapping]) -> Thesis:
        raise ImmutableInvalidationError(
            f"invalidation_rules are immutable for thesis {self.id} version {self.version}; "
            "close this version and open a new one"
        )

    def close(
        self,
        *,
        at: datetime,
        reason: ClosureReason,
        fired_rule_ids: Sequence[str] = (),
        superseded_by: str | None = None,
    ) -> Thesis:
        if self.status != "active":
            raise ThesisClosedError(f"thesis {self.id} is already closed")
        _require_aware("closed_at", at)
        return replace(
            self,
            status="closed",
            closed_at=at,
            closure_reason=reason,
            fired_rule_ids=tuple(fired_rule_ids),
            superseded_by=superseded_by,
        )

    def to_dict(self) -> dict:
        """Hypothesis contract plus lineage / fire metadata."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "direction": self.direction,
            "kind": self.kind,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "evidence": [item.to_dict() for item in self.evidence],
            "counter_evidence": [item.to_dict() for item in self.counter_evidence],
            "confirmation_rules": [rule.to_dict() for rule in self.confirmation_rules],
            "invalidation_rules": [rule.to_dict() for rule in self.invalidation_rules],
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "closure_reason": self.closure_reason,
            "version": self.version,
            "lineage_id": self.lineage_id,
            "fired_rule_ids": list(self.fired_rule_ids),
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
            "invalidation_fingerprint": self.invalidation_fingerprint,
        }


def _as_evidence(item: EvidenceItem | str | Mapping) -> EvidenceItem:
    if isinstance(item, EvidenceItem):
        return item
    if isinstance(item, str):
        return EvidenceItem(text=item)
    if isinstance(item, Mapping):
        observed_at = item.get("observed_at")
        if isinstance(observed_at, str):
            observed_at = datetime.fromisoformat(observed_at)
        return EvidenceItem(
            text=str(item["text"]),
            observed_at=observed_at,
            timeframe=item.get("timeframe"),
            source=item.get("source"),
        )
    raise TypeError(f"unsupported evidence item: {type(item)!r}")


def _as_rule(item: ThesisRule | Mapping) -> ThesisRule:
    if isinstance(item, ThesisRule):
        return item
    if isinstance(item, Mapping):
        return ThesisRule(
            id=str(item["id"]),
            kind=item["kind"],
            price=float(item["price"]),
            timeframe=str(item["timeframe"]),
            description=str(item.get("description", "")),
        )
    raise TypeError(f"unsupported rule: {type(item)!r}")


def _rules(items: Sequence[ThesisRule | Mapping]) -> tuple[ThesisRule, ...]:
    return tuple(_as_rule(item) for item in items)


def _evidence(items: Sequence[EvidenceItem | str | Mapping] | None) -> tuple[EvidenceItem, ...]:
    if not items:
        return ()
    return tuple(_as_evidence(item) for item in items)


@dataclass
class ThesisLedger:
    """Append-only store of competing thesis versions."""

    _theses: dict[str, Thesis] = field(default_factory=dict)
    _order: list[str] = field(default_factory=list)
    _events: list[ThesisEvent] = field(default_factory=list)
    _fingerprints: dict[str, str] = field(default_factory=dict)

    def get(self, thesis_id: str) -> Thesis:
        try:
            return self._theses[thesis_id]
        except KeyError as exc:
            raise ThesisNotFoundError(thesis_id) from exc

    def all(self) -> tuple[Thesis, ...]:
        return tuple(self._theses[tid] for tid in self._order)

    def active(self, *, symbol: str | None = None, direction: Direction | None = None) -> tuple[Thesis, ...]:
        out: list[Thesis] = []
        for thesis in self.all():
            if thesis.status != "active":
                continue
            if symbol is not None and thesis.symbol != symbol:
                continue
            if direction is not None and thesis.direction != direction:
                continue
            out.append(thesis)
        return tuple(out)

    def lineage(self, lineage_id: str) -> tuple[Thesis, ...]:
        return tuple(t for t in self.all() if t.lineage_id == lineage_id)

    def events(self) -> tuple[ThesisEvent, ...]:
        return tuple(self._events)

    def open(
        self,
        *,
        symbol: str,
        direction: Direction,
        kind: str,
        confirmation_rules: Sequence[ThesisRule | Mapping],
        invalidation_rules: Sequence[ThesisRule | Mapping],
        evidence: Sequence[EvidenceItem | str | Mapping] = (),
        counter_evidence: Sequence[EvidenceItem | str | Mapping] = (),
        created_at: datetime | None = None,
        thesis_id: str | None = None,
        lineage_id: str | None = None,
        version: int = 1,
        supersedes: str | None = None,
    ) -> Thesis:
        created = created_at or _utc_now()
        _require_aware("created_at", created)
        lineage = lineage_id or f"{symbol.lower()}-{direction}-{kind}-{_new_token()}"
        ident = thesis_id or f"{lineage}-v{version}"
        if ident in self._theses:
            raise ValueError(f"thesis id already exists: {ident}")
        thesis = Thesis(
            id=ident,
            lineage_id=lineage,
            symbol=symbol,
            direction=direction,
            kind=kind,
            status="active",
            version=version,
            created_at=created,
            evidence=_evidence(evidence),
            counter_evidence=_evidence(counter_evidence),
            confirmation_rules=_rules(confirmation_rules),
            invalidation_rules=_rules(invalidation_rules),
            supersedes=supersedes,
        )
        self._commit(thesis)
        self._events.append(ThesisEvent(created, ident, "opened", f"version={version}"))
        return thesis

    def add_evidence(
        self,
        thesis_id: str,
        item: EvidenceItem | str | Mapping,
        *,
        counter: bool = False,
        at: datetime | None = None,
    ) -> Thesis:
        thesis = self._require_active(thesis_id)
        extra = _as_evidence(item)
        if counter:
            updated = replace(thesis, counter_evidence=thesis.counter_evidence + (extra,))
        else:
            updated = replace(thesis, evidence=thesis.evidence + (extra,))
        self._replace_same_version(updated)
        self._events.append(
            ThesisEvent(at or _utc_now(), thesis_id, "evidence_appended", extra.text)
        )
        return updated

    def close(
        self,
        thesis_id: str,
        *,
        at: datetime,
        reason: ClosureReason = "retired",
        fired_rule_ids: Sequence[str] = (),
        superseded_by: str | None = None,
        detail: str | None = None,
    ) -> Thesis:
        thesis = self._require_active(thesis_id)
        closed = thesis.close(
            at=at,
            reason=reason,
            fired_rule_ids=fired_rule_ids,
            superseded_by=superseded_by,
        )
        self._replace_same_version(closed)
        action: EventAction = (
            "invalidated"
            if reason == "invalidation_fired"
            else "superseded"
            if reason == "superseded"
            else "closed"
        )
        self._events.append(ThesisEvent(at, thesis_id, action, detail or reason))
        return closed

    def fire(self, thesis_id: str, observation: object, *, at: datetime | None = None) -> Thesis:
        """Close the thesis if a same-timeframe invalidation rule is met.

        Does not adjust prices. A non-matching timeframe is a no-op.
        """
        thesis = self._require_active(thesis_id)
        fired = thesis.matching_invalidations(observation)
        if not fired:
            return thesis
        closed_at = at or getattr(observation, "at", None) or _utc_now()
        return self.close(
            thesis_id,
            at=closed_at,
            reason="invalidation_fired",
            fired_rule_ids=[rule.id for rule in fired],
        )

    def revise(
        self,
        thesis_id: str,
        *,
        at: datetime,
        invalidation_rules: Sequence[ThesisRule | Mapping] | None = None,
        confirmation_rules: Sequence[ThesisRule | Mapping] | None = None,
        evidence: Sequence[EvidenceItem | str | Mapping] | None = None,
        counter_evidence: Sequence[EvidenceItem | str | Mapping] | None = None,
        kind: str | None = None,
        reason: str = "reasoning_changed",
    ) -> Thesis:
        """Close the current version and open a successor with new reasoning."""
        old = self._require_active(thesis_id)
        next_invalidation = _rules(invalidation_rules) if invalidation_rules is not None else old.invalidation_rules
        next_confirmation = _rules(confirmation_rules) if confirmation_rules is not None else old.confirmation_rules
        next_kind = kind or old.kind
        unchanged_rules = (
            tuple(r.fingerprint() for r in next_invalidation)
            == tuple(r.fingerprint() for r in old.invalidation_rules)
            and tuple(r.fingerprint() for r in next_confirmation)
            == tuple(r.fingerprint() for r in old.confirmation_rules)
        )
        if unchanged_rules and next_kind == old.kind:
            raise ValueError("no rule change; append evidence or close() instead of revise()")
        successor = self.open(
            symbol=old.symbol,
            direction=old.direction,
            kind=next_kind,
            confirmation_rules=next_confirmation,
            invalidation_rules=next_invalidation,
            evidence=old.evidence if evidence is None else evidence,
            counter_evidence=old.counter_evidence if counter_evidence is None else counter_evidence,
            created_at=at,
            lineage_id=old.lineage_id,
            version=old.version + 1,
            supersedes=old.id,
        )
        self.close(
            old.id,
            at=at,
            reason="superseded",
            superseded_by=successor.id,
            detail=reason,
        )
        return successor

    def move_invalidation(
        self,
        thesis_id: str,
        rule_id: str,
        new_price: float,
        *,
        at: datetime | None = None,
    ) -> Thesis:
        """Explicitly rejected API. Invalidation prices never move in place."""
        thesis = self.get(thesis_id)
        self._events.append(
            ThesisEvent(
                at or _utc_now(),
                thesis_id,
                "rejected_invalidation_move",
                f"{rule_id}->{new_price}",
            )
        )
        raise ImmutableInvalidationError(
            f"cannot move invalidation {rule_id} on thesis {thesis.id} "
            f"version {thesis.version} (status={thesis.status})"
        )

    def replace_invalidation_rules(
        self,
        thesis_id: str,
        rules: Sequence[ThesisRule | Mapping],
    ) -> Thesis:
        """Rejected in-place rewrite. Use revise() to open a new version."""
        thesis = self.get(thesis_id)
        self._events.append(
            ThesisEvent(_utc_now(), thesis_id, "rejected_invalidation_move", "replace_rules")
        )
        raise ImmutableInvalidationError(
            f"cannot replace invalidation_rules on thesis {thesis.id} version {thesis.version}"
        )

    def _require_active(self, thesis_id: str) -> Thesis:
        thesis = self.get(thesis_id)
        if thesis.status != "active":
            raise ThesisClosedError(
                f"thesis {thesis.id} is closed ({thesis.closure_reason}); "
                "do not move its invalidation or reopen it"
            )
        sealed = self._fingerprints.get(thesis.id)
        if sealed is not None and sealed != thesis.invalidation_fingerprint:
            raise ImmutableInvalidationError(
                f"sealed invalidation fingerprint mismatch for {thesis.id}"
            )
        return thesis

    def _commit(self, thesis: Thesis) -> None:
        self._theses[thesis.id] = thesis
        if thesis.id not in self._order:
            self._order.append(thesis.id)
        self._fingerprints[thesis.id] = thesis.invalidation_fingerprint

    def _replace_same_version(self, thesis: Thesis) -> None:
        existing = self.get(thesis.id)
        if existing.invalidation_fingerprint != thesis.invalidation_fingerprint:
            raise ImmutableInvalidationError(
                f"cannot change invalidation_rules on existing version {thesis.id}"
            )
        if existing.confirmation_fingerprint != thesis.confirmation_fingerprint:
            raise ImmutableInvalidationError(
                f"cannot change confirmation_rules on existing version {thesis.id}; use revise()"
            )
        if existing.version != thesis.version:
            raise ValueError("version is immutable for a stored thesis id")
        self._commit(thesis)


__all__ = [
    "ClosureReason",
    "Direction",
    "EvidenceItem",
    "ImmutableInvalidationError",
    "PriceObservation",
    "Thesis",
    "ThesisClosedError",
    "ThesisEvent",
    "ThesisLedger",
    "ThesisNotFoundError",
    "ThesisRule",
    "ThesisStatus",
]
