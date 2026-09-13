# Recursive Learning Harness Directive

## Mission

The Recursive Learning Harness (RLH) is the custom Internal AI Harness operating as a **causal encoder + all-token recurrent loop**. It is inspired by the Recurrent Looped Transformer (RLT) pattern: encode observed tokens once, then apply the **same complete-state transition** to every subsequent token — observed market facts and generated reasoning alike — while carrying hidden state and a sliding-window memory.

RLH is not a replacement for the deterministic Context Engine, FreqAI models, or the quantitative evaluator. It does not invent candles, zones, or calibrated probabilities. It does not execute trades.

It exists so the system can:

1. freeze what was knowable at timestamp `T`;
2. loop a single inspectable reasoning transition to a bounded depth;
3. journal every loop before outcomes exist;
4. replay the identical transition later;
5. measure whether extra depth improved decision quality;
6. let Watcher and QA agents continuously correct the loop.

This is the living improvement surface for explanation, challenge, analog retrieval, and experiment proposal. Forecast numbers still come from the Forecast Engine.

## Source pattern (RLT) and what we adopt

Reference: Yifan Zhang, *Recurrent Looped Transformer*, technical report, 12 September 2026  
Project page: https://yifanzhang-pro.github.io/recurrent-looped-tranformer/

The operator screenshot is the two-block diagram:

```text
01 ENCODER                         02 ALL-TOKEN RECURRENCE
Parallel causal encoding           Prompt and response use the same transition
of observed tokens                 last prompt token e_{T-1} → H_T
x_1 … x_T                          H_t → D_φ (L_D layers) → predict x_{t+1}
Causal encoder E_θ                 Read prefix, append new-token memory
Encoder KV memory M^E              Context KV + State + SWA KV
Available before decoder replay    Merge uses SWA unless layer uses cached KV
```

RLT's own paper is explicit: **infinite depth is an extensible temporal path, not infinite work inside one token.** Realized reasoning gains must be measured. We adopt that honesty.

| RLT idea | AVAX adoption | Constitution bound |
| --- | --- | --- |
| Causal encoder over known tokens | Context Engine + leakage-safe feature snapshot | No future candles in `M_≤T` |
| Global encoder KV memory | Frozen `EncoderMemory` at forecast time | Immutable after journal write |
| Same transition for prompt and response | One `LoopStep` for ingest and emit | No "generation may cheat" path |
| Recurrent state `s_t` | Working synthesis / thesis scratch | Cannot overwrite higher-TF regime |
| Decoder SWA cache `C_t^D` | Last `W` loop tokens | Bounded memory, replayable |
| Depth grows with sequence | Across candles, `H` continues; inside a candle, depth is budgeted | Halt is mandatory |
| One transition for prefill, generate, train, replay | Live, replay, training, current-policy score share `D_φ` | Journal + replay hashes |
| Complete state `(s_t, C_t^D)` | `RecurrentState` + `SlidingWindowKV` | Detaching either breaks replay |

We do **not** vendor RLT weights, claim superintelligence, or treat extra loops as automatically smarter. Architecture novelty is an experiment until evaluation says otherwise.

## Placement in the product loop

```text
closed candles
    → causal encoder (Context Engine + features) → EncoderMemory M_≤T
    → forecast ensemble (FreqAI / baselines) → ForecastPackage
    → RLH recurrent loop D_φ over LoopTokens
         each step: Merge → retrieve/challenge/synthesize/halt
    → journal ForecastPackage + LoopTrace (before next candle)
    → UI shows state, uncertainty, loop depth, halt reason
    → outcomes mature → Recursive Evaluator scores depth vs quality
    → Watcher opens bounded improvement tasks
    → challenger harness versions compete on frozen fixtures
```

Freqtrade/FreqAI remains the quant backbone. RLH remains custom.

## Tokens

A token is a typed, timestamped, content-addressed record. It is not free prose.

### Observed tokens (encoder inputs)

Only information available at `as_of`:

- closed OHLCV candles and their hashes;
- Context Engine snapshot and state-transition IDs;
- validated zones and `known_at` pivots;
- active hypotheses with immutable invalidation rules;
- ForecastPackage outputs (model IDs, quantiles, calibration refs);
- data-health and freshness;
- prior **journaled** loop traces and outcomes that matured before `as_of`.

Screenshots are auxiliary operator input, never encoder tokens.

### Loop tokens (recurrent path)

Produced or consumed by `D_φ`:

| kind | purpose |
| --- | --- |
| `ENCODE_CHECK` | prove `M_≤T` is frozen and leakage-safe |
| `RETRIEVE` | structured tool call + tool result |
| `SYNTHESIZE` | update working bull/bear/forecast summary |
| `CHALLENGE` | required counter-thesis / invalidation audit |
| `FORECAST_REFINE` | restate calibrated model output; never invent p-values |
| `INVALIDATION_CHECK` | test whether a thesis already died |
| `ANALOG` | chronology-safe analog search |
| `NO_CHANGE` | declare the new 5m candle immaterial |
| `HALT` | stop with reason, budget remaining, and citations |
| `JOURNAL` | bind the trace to forecast + snapshot IDs |

Prompt-side ingest of a new observed token and response-side emission of a reasoning token **call the same `LoopStep`**. That is the all-token recurrence rule.

## The one transition

Formal objects live in [`Recursive-Loop-Spec.md`](Recursive-Loop-Spec.md). The operator-facing rule is:

```text
H_0 = (s_star, empty SWA)
H_t = D_φ( Merge(e_t, s_{t-1}); M_≤T, C_{t-1}^D, t )
emit optional loop token
maybe halt
```

`D_φ` is versioned (`harness_version`). Changing `D_φ` invalidates old caches for **exact** current-policy replay. Old traces remain historical artifacts and may be scored off-policy, never edited.

### What must stay the same across modes

| Mode | Encoder | Recurrent loop |
| --- | --- | --- |
| Live 5m close | Causal batch of known tokens at `T` | Advance `H` through budgeted steps, then halt |
| Replay at `T` | Rebuild `M_≤T` from raw candles + engine version | Rebuild complete `H` and SWA; do not peek at `>T` |
| Harness eval fixture | Frozen snapshot | Same tools, same halt policy |
| Current-policy score | Rebuild under **current** `D_φ` | Score each recorded action before consuming it |
| Training / SFT-like | Causal batch | Loss only on allowed emit tokens; all context tokens still update state |
| Shadow challenger | Same `M_≤T` as incumbent | Isolated `D_φ` version; journaled separately |

If live and replay diverge, the harness is broken. Watcher treats that as an emergency stop for promotion.

## Memory banks

See [`Recursive-Memory-Model.md`](Recursive-Memory-Model.md).

1. **Context KV / EncoderMemory `M_≤T`** — frozen market facts. Hierarchical. A 5m token may update only the 5m slice. It may not rewrite 4H/1D/1W regime.
2. **Recurrent state `s_t`** — working synthesis. Scratch, not truth. Truth is snapshot + journal.
3. **SWA KV `C_t^D`** — last `W` loop tokens. Default `W=16`. Prevents unbounded prose memory.

Merge reads SWA for recent reasoning and cached encoder KV for facts. If those conflict, facts win and the discrepancy is a loop event.

## Halt policy (mandatory)

Unbounded looping is a Constitution violation (fake certainty, wasted operability, possible leakage through retries). Every live loop has a budget.

Halt when **any** of these fire:

1. `max_depth` reached (production default 8; research may raise this only on experimental branches);
2. `NO_CHANGE` — no new evidence versus previous journaled synthesis;
3. required `CHALLENGE` completed and no unresolved invalidation remains;
4. tool/data health is `unknown` or stale — emit degraded synthesis and halt;
5. contradiction between encoder facts and a proposed claim;
6. attempt to quote an uncalibrated confidence percentage;
7. attempt to move an invalidation after the fact;
8. compute / latency budget exhausted;
9. Watcher abort.

Halt is a first-class token. The UI must show `halt_reason`, `depth_used`, and citations. "We kept thinking" is not a quality metric.

## Journal and learning

Every eligible forecast writes, in order:

1. `EncoderMemory` hash
2. `ForecastPackage`
3. `LoopTrace` (all steps, tool IOs, halt)
4. durable commit

Outcomes later attach to the forecast **and** to any intermediate `FORECAST_REFINE` tokens that restated the ensemble. Intermediate refinements may be scored for depth-ablation. They must not mutate the original ForecastPackage.

Recursive learning means:

- score whether depth `k` beat depth `k-1` on predefined metrics;
- promote halt-policy or tool-policy changes only when out-of-sample fixtures improve;
- turn repeated loop failures into regression fixtures;
- never retrain on the same journal outcomes used as the unseen test.

## Watcher and subagent control

Agent 00 monitors RLH continuously using [`Recursive-Watcher-Protocol.md`](Recursive-Watcher-Protocol.md).

The operator kill switch (UI + `POST /api/v1/agents/kill-switch`) severs every in-flight recursive agent and blocks new loops. Journaled traces stay. Trading stays off.

Lanes 25-30 own implementation. Lanes 36-39 try to break it. Ready-to-launch contracts are in [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md).

The operator kill switch (UI + `POST /api/v1/agents/kill-switch`) severs every in-flight recursive agent and blocks new loops. Journaled traces stay. Trading stays off.

No agent may:

- let the loop write Context Engine state except through the deterministic engine;
- treat LLM prose as encoder memory;
- report a single accuracy number from extra loops;
- delete or weaken the September 2026 failed-breakout fixture to make depth look useful;
- reset recurrent state at the "we are now explaining" boundary.

## Acceptance for RLH v1

RLH v1 is complete when:

- `LoopStep` is one function for ingest and emit;
- encoder memory is frozen before the first decoder step;
- every production loop halts with a typed reason;
- live and replay traces match on frozen fixtures;
- challenge step is mandatory for directional synthesis;
- 5m steps cannot overwrite 4H encoder memory;
- September 2026 replay produces a coherent bearish higher-TF reading through relief bounces;
- depth-ablation artifacts exist and do not claim in-sample victory;
- UI can show depth, halt, and citations from the journal, not from a fresh invented story.
