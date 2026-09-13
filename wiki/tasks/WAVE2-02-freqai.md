# WAVE2-02 — Freqtrade/FreqAI research adapter

```md
Task: Strengthen the pinned Freqtrade bootstrap/adapter as a research-only, non-forked upstream boundary with no order execution.
Agent: 02
Branch: cursor/freqtrade-adapter-8021
Priority: P0

Why:
Phase 0/3 require a complete pinned Freqtrade clone plus an adapter that preserves upgradeability and GPL boundaries. The scaffold stub clones a pin but does not record license, allows a non-zero stake, uses a futures trading-mode, and has no tests that the adapter refuses execute/order paths.

Inputs:
- CONSTITUTION.md (immutable)
- wiki/ML-FreqAI-Directive.md
- wiki/Open-Source-Dependencies.md
- wiki/Architecture.md
- adapters/freqtrade/*
- scripts/bootstrap_freqtrade.sh
- upstream.lock.json (read-only; pin already recorded on main)

Allowed write scope:
- adapters/freqtrade/**
- scripts/bootstrap_freqtrade.sh
- tests/test_freqtrade_adapter.py
- wiki/tasks/WAVE2-02-freqai.md

Forbidden write scope:
- CONSTITUTION.md
- packages/** (do not copy GPL source here)
- services/harness/**
- apps/web/**
- any exchange order API
- live trading enablement

Dependencies:
- Pinned upstream commit c064be5325ad6941a2789add795434e6a13dffe9
- Watcher WAVE2-parallel lock: Agent 02 owns adapters/freqtrade + bootstrap script

Implementation requirements:
1. Keep pin c064be5325ad6941a2789add795434e6a13dffe9. Do not fork upstream.
2. Bootstrap clones the complete upstream repository, checks out the pin, and records the license.
3. Strategy/config remain research/read-only: dry_run, no stake, no credentials, no entries/exits.
4. Adapter refuses execute/order methods. Tests may mock vendor.
5. Do not claim FreqAI already beats baselines.

Acceptance tests:
- command: python -m pytest -q tests/test_freqtrade_adapter.py
  expected: all tests pass without cloning vendor/freqtrade
- command: python -c "from adapters.freqtrade import FreqtradeResearchAdapter; FreqtradeResearchAdapter().place_order()"
  expected: ResearchOnlyViolation
- bootstrap script contains clone + detach checkout of the pin + license recording
- config dry_run is true and stake_amount is 0

Metrics gate:
- baseline: scaffold stub (dry_run true, stake 100, futures, no tests)
- required result: research-only config + adapter refusals + license/pin recording; no accuracy claim

Historical regressions:
- none for this adapter increment; do not touch September 2026 fixture ownership

Docs to update:
- adapters/freqtrade/README.md
- adapters/freqtrade/LICENSE-NOTICE.md
- wiki/tasks/WAVE2-02-freqai.md

Finish criteria:
Tests green. Pin unchanged. No live trading path. Completion report below. Branch pushed and PR opened to main.
```

Watcher owner: Agent 00
Review mode: normal
Competing task group: none
Integration dependency: none

## Completion report

### What changed

Strengthened the pinned Freqtrade/FreqAI adapter as a research-only, non-forked boundary.

- Documented pin `c064be5325ad6941a2789add795434e6a13dffe9` and GPL-3.0 in `pin.json` + `LICENSE-NOTICE.md`.
- Bootstrap now clones the complete upstream repo (no shallow/sparse clone), checks out the pin, verifies HEAD, and records license via `vendor/freqtrade/.avax-upstream-manifest.json`.
- Config is dry-run, zero stake, spot-only, no credentials, `max_open_trades=0`, `initial_state=stopped`, FreqAI shuffle disabled.
- Strategy still emits no entries/exits. Targets remain `&-cum-ret-1..10` labels.
- `FreqtradeResearchAdapter` refuses execute/order/buy/sell/`freqtrade trade` paths. Tests mock vendor.

No FreqAI-vs-baseline performance claim is made.

### Exact files changed

- `adapters/freqtrade/AvaxContextStrategy.py`
- `adapters/freqtrade/LICENSE-NOTICE.md` (new)
- `adapters/freqtrade/README.md`
- `adapters/freqtrade/__init__.py` (new)
- `adapters/freqtrade/adapter.py` (new)
- `adapters/freqtrade/bootstrap.py` (new)
- `adapters/freqtrade/config.freqai.json`
- `adapters/freqtrade/constants.py` (new)
- `adapters/freqtrade/pin.json` (new)
- `adapters/freqtrade/safety.py` (new)
- `scripts/bootstrap_freqtrade.sh`
- `tests/test_freqtrade_adapter.py` (new)
- `wiki/tasks/WAVE2-02-freqai.md` (new)

### Tests run and results

- `python3 -m pytest -q tests/test_freqtrade_adapter.py` — 11 passed
- `python3 -m pytest -q` — 29 passed (full current suite)
- `bash scripts/check_constitution.sh` — Constitution integrity OK
- Adapter `place_order()` raises `ResearchOnlyViolation`

### Metrics before/after

| check | before (scaffold) | after |
| --- | --- | --- |
| pin | documented in lock only | lock + adapter `pin.json` + bootstrap verify |
| license recording | none | generated vendor manifest + LICENSE-NOTICE |
| dry_run | true | true |
| stake_amount | 100 | 0 |
| trading_mode | futures | spot |
| execute/order refusal tests | none | 11 adapter tests |
| FreqAI beats baselines? | not claimed | explicitly not claimed |

### Known limitations

- Tests mock vendor; they do not clone Freqtrade in CI.
- `stake_amount: 0` is an adapter safety constraint. A later operability agent may need a dummy positive stake if they invoke Freqtrade's own config validator; they must keep `dry_run` and `max_open_trades=0`.
- No FreqAI model was trained. No walk-forward or baseline comparison was run.
- Strategy still imports upstream `IStrategy` / TA-Lib and is only executed after bootstrap.

### Documentation updated

Yes: adapter README, LICENSE-NOTICE, WAVE2-02 task/completion report. `upstream.lock.json` and wiki directives were left unchanged (outside write scope; pin already recorded).

### Contract/schema changed?

No shared API/schema. Adapter-local research-only contract only.

### Recommended next task

Agent 05/06: after bootstrap, run leakage-safe FreqAI backtesting against Agent 04 baselines. Do not promote or claim improvement until walk-forward artifacts exist. Agent 32 can wire Docker/bootstrap into the local stack without enabling `trade`.
