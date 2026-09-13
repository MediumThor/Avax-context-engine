# Operability Directive

## Goal

A living system must be observable, reproducible and recoverable. Operability is part of the product, not a deployment afterthought.

## Local developer experience

One documented command should bring up the complete local stack after dependencies are installed, preferably through Docker Compose:

- Web App;
- API gateway;
- Context Engine;
- Evaluation Engine;
- Internal AI Harness;
- database/cache if required;
- Freqtrade/FreqAI service or adapter target.

Provide a second minimal mode for fast UI/context development using fixture data.

The target full-stack command is `docker compose up --build` from a clean checkout. Phase 0 may wrap it in a shorter task-runner command, but the underlying Compose path must remain documented and reproducible.

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
- last successful journal write;
- last successful `LoopTrace` write;
- last exact-replay canary result.

Aggregate health must be available through `/health` and the Web App.

The recursive agent kill switch is an operability control, not a model parameter. `GET/POST /api/v1/agents/kill-switch` and `POST /api/v1/agents/kill-switch/reset` are the API. Engaged state must appear in `/health`.

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
- loop depth used / halt-reason mix;
- exact-replay mismatch count;
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

The production persistence target uses PostgreSQL for canonical relational records/indexes, a content-addressed filesystem/S3-compatible adapter for complete immutable payloads, and Parquet for bulk research exports. The current SQLite stores remain prototype/test implementations. Local recovery must not require a cloud service.

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

If the Recursive Learning Harness fails replay or journal, UI must mark explanations `harness-degraded` while still showing structure and forecast numbers when those services are healthy. See [`Recursive-Watcher-Protocol.md`](Recursive-Watcher-Protocol.md).

If source data is stale, forecasts are stale and must not be presented as current.
