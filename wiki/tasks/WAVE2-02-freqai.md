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

See the end of this file after implementation.
