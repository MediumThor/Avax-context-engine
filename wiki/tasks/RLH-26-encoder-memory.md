# RLH-26 — EncoderMemory builder

```md
Task: Build frozen EncoderMemory at as_of and expose read-only harness tools.
Agent: 26
Base: latest main
Integration target: main
Registered temporary source: cursor/agent-26-rlh-encoder-ee66
Model: Grok 4.6
Priority: P0

Why:
The recurrent loop must not see unfinished parent candles or future data.

Inputs:
- wiki/Recursive-Memory-Model.md
- packages/contracts/recursive/encoder-memory.schema.json
- packages/contracts/recursive/examples/encoder-memory.example.json

Allowed write scope:
- services/harness/encoder/**
- tests/harness/encoder/**

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- services/harness/loop/**
- services/context writes / mutations

Implementation requirements:
1. builder(as_of, snapshot, forecast_package, manifest) -> EncoderMemory with content_hash.
2. Mutating the 5m slice cannot change 4h/1d/1w slices.
3. Unfinished parent candles ignored.
4. Perturbing candles with open_time > as_of must not change content_hash.
5. Tools are read-only. No Context Engine writes.

Acceptance tests:
- future-candle perturbation hash-stable
- unfinished parent ignored
- 5m cannot write 4h
- example payload still schema-valid if emitted

Finish criteria:
Hashed EncoderMemory builder + tests under tests/harness/encoder.
```
