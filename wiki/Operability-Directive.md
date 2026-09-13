# Operability Directive

## Goal

A living system must be observable, reproducible and recoverable. Operability is part of the product, not a deployment afterthought.

## Local developer experience

One documented command should bring up the complete local stack after dependencies are installed, preferably through Docker Compose:

- web UI;
- API gateway;
- Context Engine;
- evaluator;
- AI harness;
- database/cache if required;
- Freqtrade/FreqAI service or adapter target.

Provide a second minimal mode for fast UI/context development using fixture data.

## Environment policy

- `.env.example` documents required variables.
- No secrets committed.
- Exchange credentials are unnecessary for read-only public candle ingestion when public endpoints suffice.
- Any future authenticated source uses least privilege.
- Real trading keys are explicitly unsupported in v1.

## Health contracts

Every service exposes health information including:
- process health;
- version/commit;
- dependency health;
- data freshness;
- last successful state update;
- last successful forecast;
- last successful journal write.

Aggregate health must be available through `/health` and UI.

## Logging

Structured JSON logs in services. Include:
- timestamp UTC;
- service;
- version;
- correlation/request ID;
- symbol/timeframe when relevant;
- snapshot/model IDs when relevant;
- severity;
- event code.

Never log secrets or raw auth headers.

## Metrics

At minimum collect:
- candle ingestion lag;
- missing/duplicate candle count;
- context update latency;
- forecast latency;
- harness latency;
- journal write failures;
- model age;
- evaluation backlog;
- API error rate;
- UI data age.

## Persistence

Separate immutable/raw and derived state:

- raw market observations are append-only;
- context snapshots are versioned;
- predictions are append-only;
- outcomes append to predictions by ID rather than replacing forecasts;
- derived caches may be rebuilt.

## Recovery

The system must be able to rebuild context state from raw candle history. A corrupted cache cannot be a catastrophic event.

Document:
- clean rebuild;
- model rollback;
- context schema migration;
- upstream Freqtrade pin upgrade/downgrade;
- prediction-journal verification.

## Version visibility

The UI system page must expose:
- app commit SHA;
- Context Engine schema version;
- feature schema version;
- incumbent model IDs;
- Freqtrade upstream commit;
- Lightweight Charts package version;
- data-source identifiers.

## Release gates

A release candidate is promotable only when:
- build/lint/typecheck pass;
- unit/integration tests pass;
- leakage suite passes;
- benchmark smoke suite passes;
- September 2026 regression replay passes;
- UI smoke/accessibility pass;
- migration/rebuild path works;
- docs match contracts.

## Degraded modes

If forecasts fail but market data/context remain valid, UI should show structure without forecast rather than crash.

If Context Engine fails, model-only output must be explicitly marked context-degraded.

If source data is stale, forecasts are stale and must not be presented as current.
