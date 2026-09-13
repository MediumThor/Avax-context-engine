# Documentation Standards

## Purpose

These conventions keep architecture, contracts, directives, tests, and agent prompts aligned. They do not override the Constitution.

## Requirement language

- **MUST / MUST NOT** — required for constitutional, safety, contract, or release-gate compliance.
- **SHOULD / SHOULD NOT** — expected default; deviations require a documented reason.
- **MAY** — optional behavior.
- **Target** — planned behavior that is not necessarily implemented.
- **Current** — behavior verified in the repository at the referenced commit.
- **Example** — illustrative data, not a production default or benchmark threshold.

Do not describe a target component as operational until its code and applicable tests exist on the referenced branch.

## Canonical terminology

Use these names consistently:

| Concept | Canonical name |
| --- | --- |
| Product/repository | AVAX Context Engine |
| Deterministic market-state layer | Context Engine |
| Quantitative prediction layer | Forecast Engine |
| LLM/tool reasoning interface | Internal AI Harness |
| Per-forecast recurrent reasoning implementation | Recursive Learning Harness (RLH) |
| Append-only forecast record | Prediction Journal |
| Outcome scoring and comparison | Evaluation Engine |
| Evidence-to-code learning workflow | Continuous improvement |
| Human-facing client | Web App |

Freqtrade/FreqAI is the **quantitative backbone**. It is not the Context Engine or Internal AI Harness.

## Symbols, timeframes, and horizons

- Canonical contract symbols omit separators: `AVAXUSDT`, `BTCUSDT`, `ETHUSDT`, `AVAXBTC`.
- User-facing labels may use exchange-style separators such as `AVAX/USDT`.
- API/schema timeframe values are lowercase: `5m`, `15m`, `1h`, `4h`, `1d`, `1w`.
- UI labels are `5m`, `15m`, `1H`, `4H`, `1D`, `1W`.
- Machine-facing forecast horizons are `h=1..10`; UI copy may show `+1..+10`.
- A horizon is cumulative from forecast origin unless a field explicitly says `individual_candle` or `path`.

## Time semantics

- Internal timestamps are UTC.
- Point-in-time features use only information whose `known_at` is at or before the forecast timestamp.
- `observed_at` identifies when the underlying market event occurred; `known_at` identifies when the system could legally use it.
- Higher-timeframe features use only completed parent candles unless an explicitly named partial-candle namespace is defined and tested.
- Example dates and prices must be labeled as examples or benchmark-specific observations.

## Source-of-truth boundaries

- Implemented, tested schemas are canonical within their declared scope. RLH JSON schemas currently live under `packages/contracts/recursive/`; canonical non-RLH Pydantic/OpenAPI contracts remain a build gate.
- Generated TypeScript types must derive from those contracts rather than diverge manually.
- The wiki explains contract intent; it must be updated in the same change as a semantic contract change.
- Launch prompts summarize accepted specifications. They do not create new architecture or schemas.
- Generated artifacts and mutable prose summaries are never the sole source of historical truth.
- `main` is the durable product state. Agent branches/worktrees, when used, are disposable isolation surfaces.

## Documentation checks

Every documentation change should verify:

1. Relative links resolve.
2. Current and target behavior are clearly distinguished.
3. Contract examples use canonical names and codes.
4. Forecast metrics define target, horizon, window, sample count, and baseline where applicable.
5. No page weakens prediction immutability, chronology, no-execution, or higher-timeframe rules.
6. `CONSTITUTION.md` is unchanged.

When a change affects shared semantics, review at least the relevant contract, directive, testing page, launch prompt, and UI/API consumer documentation.
