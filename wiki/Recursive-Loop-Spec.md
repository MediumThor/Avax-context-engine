# Recursive Loop Specification

Status: implementable contract. Schema owner: Agent 25. Watcher: Agent 00.

This page is the executable math/state machine. Human rationale lives in [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md). JSON schemas live in [`../packages/contracts/recursive/`](../packages/contracts/recursive/).

## State

```text
H_t = (s_t, C_t^D)
H_0 = (s_star, empty)
```

- `s_t` — recurrent output (working synthesis). Typed object, not a blob of chat.
- `C_t^D` — layerwise-or-single sliding-window KV of recent loop tokens.
- `M_≤t` — encoder memory restricted to tokens with `known_at <= t`.
- `e_t` — encoder embedding / structured encoding of the current token.
- `D_φ` — versioned loop transition.
- `W` — SWA window. Includes the current token and at most `W-1` historical loop entries.

## Transition

```text
u_t = Merge(e_t, s_{t-1}; M_≤t, C_{t-1}^D)
(s_t, C_t^D, emit_t, halt_t) = D_φ(u_t, t, budget)
```

`Merge` rules:

1. Facts from `M_≤t` outrank `s_{t-1}` and SWA.
2. Parent timeframe slices in `M_≤t` outrank child slices when they conflict on regime.
3. SWA supplies recent *reasoning*, never missing candles.
4. If `e_t` is an observed market token, it may update only the matching timeframe scratch in `s_t`.
5. If `e_t` is a generated loop token, it may not insert new numeric forecasts that are absent from `ForecastPackage`.

`D_φ` must be deterministic given:

- `harness_version`
- `tool_schema_version`
- `encoder_memory_hash`
- `forecast_package_id`
- `rng_seed` if any tool is stochastic (default: no stochastic tools in v1)
- identical tool results

Stochastic LLM sampling, if used, must be recorded (`sampler_id`, `temperature`, `seed`) so replay can either reproduce or mark the step `non_exact`.

## Token index vs market time

Do not confuse them.

| clock | meaning |
| --- | --- |
| `as_of` | Exchange-normalized forecast timestamp (closed 5m) |
| `t` | Loop-token index inside one `LoopTrace` at that `as_of` |
| `known_at` | When a fact became legal to use |

Depth after `t` loop tokens is `t * L_D` logical decoder blocks. `L_D` is the number of internal sublayers inside one `LoopStep` (retrieve, update, emit). Production cares about **halted depth**, not theoretical `t * L_D`.

Across candles, a new `as_of` starts a new `LoopTrace` but may **warm-start** `s_0` from the previous journaled `s_halt` **only as scratch**. Encoder memory is rebuilt from raw observations. Warm-start must not smuggle future-matured outcomes.

## Legal tool surface

`D_φ` may call only the harness tools listed in [`AI-Harness-Directive.md`](AI-Harness-Directive.md):

- `market.get_snapshot`
- `market.get_series`
- `context.get_zones`
- `context.get_structure`
- `context.get_hypotheses`
- `forecast.get_current`
- `forecast.get_history`
- `evaluation.get_metrics`
- `analog.search`
- `system.get_health`
- `learning.get_cases`
- `learning.get_decisions`

Plus RLH-only tools:

- `loop.get_state` — current `s_t`, depth, budget
- `loop.cite` — bind a claim to snapshot/forecast/zone/hypothesis IDs
- `loop.halt` — emit `HaltDecision`

Tools receive `as_of` and must refuse data with `known_at > as_of`. A refused tool call is a successful leakage test, not a retry-with-wider-window event.

Learning tools may return only candidates, decisions, lessons, and evidence that existed by `as_of`. A current-policy research run may opt into newer lessons, but must be labeled as a rebuild and can never replace the historical trace.

## Required step order for directional synthesis

Minimum production path:

```text
1 ENCODE_CHECK
2 RETRIEVE snapshot + health + forecast
3 SYNTHESIZE what_changed / what_did_not_change
4 CHALLENGE opposite case + invalidation audit
5 INVALIDATION_CHECK
6 FORECAST_REFINE (optional; restates ensemble only)
7 HALT
8 JOURNAL
```

A 5m candle that does not change higher-TF state should take the `NO_CHANGE` shortcut after step 2-3 and halt. That is a feature.

## Emission contract

`emit_t`, when present, is a `LoopStep` object. The final user-visible analysis is assembled only from:

- encoder citations;
- forecast package fields;
- halt reason;
- the structured analysis object from [`AI-Harness-Directive.md`](AI-Harness-Directive.md).

Prose is a rendering of that object. If prose and object disagree, the object wins and Watcher files a `HARNESS` defect.

## Gradient / learning analogue

We are not required to run full BPTT through an LLM. The *learning* contract is:

1. **Forward consistency** — replay rebuilds `H_t` and SWA.
2. **Complete credit** — depth-ablation scores every prefix that emitted a `FORECAST_REFINE` or structured analysis.
3. **No detached caches for exact replay** — dropping SWA or encoder memory and claiming the same policy is forbidden.
4. **Current-policy vs off-policy** — scoring an old trace under new `D_φ` is a rebuild, not a reread of cached prose.

Parameter updates (prompt policy, tool policy, halt thresholds, optional local model) invalidate exact cache reuse. Record `harness_version` on every trace.

## Leakage invariants (blocking)

For any fixture timestamp `T`:

1. Perturbing candles with `open_time > T` must not change `encoder_memory_hash` or any `LoopStep` at `T`.
2. Unfinished parent candles must not appear in `M_≤T` except under an explicit `partial=true` namespace, which v1 RLH must ignore.
3. Analog search must cap results at `known_at <= T`.
4. Evaluation metrics used inside a live loop may include only outcomes matured at or before `T`.
5. Warm-start state from `T-1` may not include outcomes that matured after `T-1`.

## Replay package

A replay request (`ReplayPackage`) loads:

- raw observations with `known_at <= T`;
- engine versions;
- `EncoderMemory`;
- `ForecastPackage`;
- full `LoopTrace`;
- optional hidden future candles (UI-gated);
- outcomes separately.

Replay default hides future candles. Revealing them must flip a visible replay flag and must not re-run `D_φ` against those candles unless the operator starts a *new* as-of.

## Versioning

| field | bumps when |
| --- | --- |
| `loop_schema_version` | `LoopTrace` / `LoopStep` fields change |
| `harness_version` | `D_φ`, halt policy, or tool policy changes |
| `encoder_schema_version` | `EncoderMemory` fields change |
| `tool_schema_version` | tool IO schemas change |

Breaking changes require a new schema version and a Watcher-owned migration note. TypeScript types are generated from the JSON schemas, not hand-duplicated.
