# Prediction Improvement Loop

This is the operating playbook for making AVAX forecasts **measurably better** than baselines, then keeping pressure on residual error until the system is useful as **decision support for a leveraged AVAX operator**.

It does **not** place trades. Constitution §17: v1 is read-only analysis and simulation. "Leverage trading" here is the **economic test**, not a live-order mandate. If live execution is ever wanted, the repository owner must amend the Constitution in a separate human-governed process.

Related: [`Continuous-Improvement-Directive.md`](Continuous-Improvement-Directive.md) (evidence-to-code cycle), [`Simulation-Accuracy.md`](Simulation-Accuracy.md), [`Dogfooding-Directive.md`](Dogfooding-Directive.md), [`Watcher-Directive.md`](Watcher-Directive.md), [`Information-Gaps.md`](Information-Gaps.md), [`Prediction-Journal.md`](Prediction-Journal.md).

This page is the **source-discovery and access-request** playbook. Promotion still follows the Continuous Improvement Directive and Watcher gates. It does not replace them.

## Success definition

Constitution §20 still governs. Success is **not** "predict every 5m candle" and **not** a single attractive backtest.

A cycle succeeds when **all** of the following are true:

1. Forecasts were journaled **before** outcomes were known.
2. Scoring is walk-forward (or shadow-live), with `sample_count`, metric name, and data manifest.
3. The challenger beats the ticket's **pre-declared** gate versus `baseline.zero` and `baseline.drift20` (and the incumbent, if one exists).
4. September 2026 failed-breakout process checks still pass (5m bounce does not rewrite 4H).
5. Uncertainty is reported. Abstentions are counted. No invented probabilities.
6. Residual errors are named and become the next ticket. History is not rewritten.

Leverage-aware add-on (simulation only): after fees, assumed funding, and a liquidation barrier, the challenger must not look good only because it was "right on direction" while a 10x account would have been stopped out.

## The loop (do not skip)

```text
observe journal + dogfood
    → diagnose (code, state, model, or missing information)
    → name the InformationGap
    → discover sources (public first)
    → AccessRequest to the owner if a key / paid API / ToS decision is required
    → ImprovementTicket with a frozen metrics gate
    → implement in a bounded write scope
    → walk-forward / replay / leakage tests
    → ImprovementOutcome: promote | reject | hold | blocked-on-access
    → next ticket from residual error
```

If the system is **not** accurately predicting AVAX, the required action is another pass through this loop — not a narrative that "the market was irrational," not a quieter metric, and not a moved invalidation.

Kill switch: if `POST /api/v1/agents/kill-switch` is engaged, stop implementing. Journaled forecasts and this playbook stay.

## Phase A — Observe

At each review (dogfood session, matured journal window, or Watcher sweep), collect:

| artifact | question |
| --- | --- |
| Prediction journal | Which horizons missed? Direction, size, or timing? |
| Context snapshot | Did 4H/1D stay coherent? Was a bounce called a reversal? |
| Data health | Stale, gapped, fixture-only, or live? |
| Cross-market slice | Was AVAX moving with BTC/ETH or decoupling? |
| Operator notes | What fact did a human wish they had at `as_of`? |
| Code scan | What can the repo not ingest, represent, or score yet? |

Tag every finding with the dogfood taxonomy: `DATA`, `STATE`, `MODEL`, `HARNESS`, `UI`, `EVAL`, `OPS`, plus `GAP` when the failure is missing information rather than a bad algorithm.

## Phase B — Diagnose the codebase

Re-scan. The list below is the **current** known debt, not a complete forever-list.

### Product / forecast

- Honest slice (PR #8) journals `baseline.drift20` only. No FreqAI walk-forward, no calibrated `p_close_above_origin`.
- Zero-model direction now abstains; that is correct, not skill.
- Fixture walk-forward MAE can be numerically tiny on a smooth synthetic grind. Do not treat rounded zeros as edge.
- Thesis ledger is still copy, not objects with immutable invalidation.

### Data the repo does not yet ingest

| family | status | why it matters for AVAX leverage |
| --- | --- | --- |
| AVAX/BTC/ETH 5m OHLCV | partial (Binance Vision + fixture) | backbone |
| Funding / mark / index | missing | carry and squeeze risk |
| Open interest + liquidations | missing | cascade and stop-run context |
| Order book / CVD | missing | short-horizon pressure |
| Stablecoin / AVAX on-chain flows | missing | inventory and exchange premium |
| Labeled market-maker / desk wallets | missing | inventory, spoof-vs-real flow (public chain only) |
| News / governance / unlocks | missing | jumps the 5m model cannot see |
| Gold, oil, US10Y, DXY | missing | risk-on/off and liquidity regime |
| Equities / MAG7 beta | missing | crypto risk appetite |
| Options / implied vol (BTC or AVAX if listed) | missing | crash premium |

A missing family is an `InformationGap`, not permission to hallucinate a print.

### How to diagnose on a new pass

1. Trace one live or fixture forecast from candle ingest → snapshot → features → journal → score.
2. List every feature the model **could not have known** and every feature it **should have known but the code never loaded**.
3. Open or update rows in [`Information-Gaps.md`](Information-Gaps.md).
4. Prefer the cheapest public source that is timestamp-safe. Escalate to an AccessRequest only when public data is insufficient or ToS/auth blocks ingest.

## Phase C — Discover sources, then ask for access

Agents **must not** invent API keys, scrape behind logins, or paste guessed wallet labels as fact.

Discovery order:

1. **Already in-repo** — Binance Vision, fixture, journal.
2. **Public, no key** — exchange REST/WS public endpoints, Binance Vision monthly zips, GDELT, official RSS, Snowtrace-style explorers with documented APIs, government/macro series (FRED, EIA) where license allows.
3. **Public, key required** — register-for-free tiers (CryptoCompare, CryptoPanic, some on-chain indexers).
4. **Paid / privileged** — Coinglass, Nansen, Arkham, Dune plus, Polygon, Tardis, news wires. **Stop and ask.**
5. **Human-only** — OTC color, private desk maps, anything non-public. **Stop and ask.** Never train on it until the owner says the license allows it.

### AccessRequest (ask the owner)

Write a record that validates against `packages/contracts/improvement/access-request.schema.json` and a short note under `wiki/improvement/access-requests/`.

The request must say:

- what decision the forecast cannot make without this source;
- candidate vendor/API and docs URL;
- whether a free tier exists;
- exact scopes needed (read-only);
- leakage / ToS / retention risk;
- what we will **not** do with it (no order placement, no credential reuse);
- how we will snapshot and checksum the data.

Until the owner replies `granted` | `denied` | `deferred`, the dependent ticket stays `blocked-on-access`. The agent may implement adapters behind a flag using **fixtures only**.

Owner reply goes on the same request (`decided_at`, `decision`, `notes`). Do not treat silence as permission.

## Phase D — Plan (ImprovementTicket)

Every implementation needs a ticket that validates against `improvement-ticket.schema.json`.

Required fields:

- `id` — `IMP-NNN`
- `residual` — the named error cluster this ticket attacks
- `hypothesis` — why the change should help **out of sample**
- `write_scope` / `forbidden_scope`
- `metrics_gate` — frozen **before** looking at challenger results
- `regressions` — must include September 2026 process checks when state or features change
- `depends_on_gaps` / `depends_on_access`

A ticket that says "improve accuracy" without a metric, window, and baseline is incomplete. Watcher rejects it.

### Metrics gate template

```text
target: AVAXUSDT 5m, horizons 1..10
validation: walk_forward
windows: predeclared (not chosen after seeing scores)
primary: signed_direction_accuracy or Brier vs baseline.drift20
secondary: MAE/RMSE of cum log return; q10-q90 coverage if distributions exist
leverage_sim: fee + funding + 10x isolated liq barrier (research only)
n_min: enough matured samples to be worth talking about
must_not: degrade bear/high-vol slices; flip 4H on 5m bounce
```

Exact numbers live on the ticket, not in this sentence.

## Phase E — Implement

Small mergeable increments. One residual per ticket. Shared schemas have one owner.

Implementation may include:

- ingest adapters + manifests;
- Context Engine fields (regime, zones, thesis objects);
- leakage-safe features with `known_at`;
- model/baseline challengers;
- evaluator slices (BTC-decoupled, news-window, funding-extreme);
- UI that shows uncertainty and source freshness.

Implementation may **not** include:

- `CONSTITUTION.md` edits;
- live order routing;
- in-sample-only claims;
- deleting or weakening regressions to make a chart prettier.

## Phase F — Track outcomes

After tests and a walk-forward (or shadow-live) run, write `ImprovementOutcome`:

| decision | meaning |
| --- | --- |
| `promote` | gate hit; incumbent replaced or ensemble weight updated; SHA recorded |
| `reject` | gate missed or leakage/regression failed; keep incumbent; say why |
| `hold` | mixed; needs more mature samples; not a silent promote |
| `blocked-on-access` | stopped at Phase C; owner action required |

Outcomes are append-only. A later success does not rewrite a prior reject.

File human-readable copies under `wiki/improvement/outcomes/` when the result should survive as operational memory. Machine copies may live under `artifacts/improvement/` (gitignored runtime).

## Leverage-aware simulation (not trading)

When scoring "would this have helped a leveraged operator?":

1. Use only information available at `forecasted_at`.
2. Apply explicit fee and slippage assumptions from the ticket.
3. Accrue funding using **then-published** funding rates if ingested; otherwise mark the score `funding_assumed` and do not pretend it is exact.
4. Define a liquidation / stop barrier (e.g. isolated 10x, maintenance margin). If adverse excursion hits the barrier before the horizon, the path is a **full simulated loss**, even if later candles would have recovered.
5. Report `sample_count`, `abstentions`, and interval estimates. Do not publish a win rate alone.
6. Never send an order. Never store exchange trading API keys in this loop.

## Cross-market and alternative-data playbook

These families are **competing hypotheses**, not privileged oracles. Each must survive ablation: AVAX-only vs +BTC/ETH vs +macro vs +news vs +on-chain.

### Crypto microstructure

- BTC and ETH regime, vol expansion, AVAX/BTC decoupling ([`Context-Engine-Directive.md`](Context-Engine-Directive.md) already requires BTC).
- Perp funding, OI, liquidation bursts — squeeze vs grind.
- Exchange basis and stablecoin inflow — premium/discount.

### Macro (gold, bonds, oil, dollar)

- Gold and oil: risk and inflation impulse; often slower than 5m AVAX. Use as **regime priors**, not 5m triggers, unless walk-forward shows otherwise.
- US10Y / real yields / DXY: liquidity and crypto beta.
- Timestamp alignment: use the last **closed** macro bar known at AVAX `as_of`. A 1D gold bar that has not closed is not a 5m feature.

### News and narratives

- Headlines need `published_at` ≤ `as_of`. Correction timestamps too.
- Governance, unlocks, outages, ETF flows, regulation.
- Treat NLP sentiment as a feature with provenance, never as a confidence percent.

### Market-making and labeled wallets

- Watch **public** C-Chain / exchange-hot-wallet clusters only.
- Labels are hypotheses (`source=nansen|manual|heuristic`, `known_at`). A mislabeled MM wallet is worse than no wallet feature.
- Features: inventory delta, CEX deposit/withdraw bursts, wash-like cycling. Not "this wallet will dump" as a prophecy.
- Ask the owner before paying for label vendors or publishing third-party attributions.

## Agent roles in this loop

| lane | job |
| --- | --- |
| 00 Watcher | reject fake gates, leakage, execution creep; serialize tickets |
| 01 / 14 | ingest + cross-market |
| 04 / 06 | baselines, walk-forward runner |
| 09–15 | context, thesis, BTC/macro state |
| 25–30 | harness explanations bound to journal IDs |
| 36–39 | red-team residuals, source honesty, replication |

Numbers are lanes. One writer per path.

## First tickets after this playbook

Suggested order (each still needs its own contract):

1. **IMP-001** — ingest live BTC/ETH beside AVAX; expose decoupling features; walk-forward vs AVAX-only.
2. **IMP-002** — funding + OI + liquidations (AccessRequest if the chosen vendor needs a key).
3. **IMP-003** — thesis ledger objects with immutable invalidation.
4. **IMP-004** — FreqAI / tabular challenger with frozen gate vs drift20.
5. **IMP-005** — gold / DXY / US10Y as daily regime priors (FRED or equivalent; ask if using a paid vendor).
6. **IMP-006** — news window features with strict `published_at`.
7. **IMP-007** — public MM/hot-wallet watchlist (labels only after AccessRequest or owner-supplied list).

Do not start IMP-007 labels from model memory. Ask.

## What agents must say when they are stuck

Use this exact shape in the owner-facing summary:

```text
I cannot truthfully improve AVAX forecasts here because: <gap_id>.
Public options: <urls or "none honest">.
I need from you: <grant | key | paid plan | labeled wallet list | "skip this family">.
Until then the ticket stays blocked-on-access and forecasts will keep <current limitation>.
```
