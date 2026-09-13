# RLH-00 — Recursive watcher

```md
Task: Own Watcher artifacts and review RLH-wave-1 completions. Do not implement harness features.
Agent: 00
Branch: cursor/agent-00-rlh-watch-ee66
Model: Grok 4.6
Priority: P0

Watcher owner: Agent 00
Review mode: rlh-loop
Competing task group: none
Integration dependency: none

Why:
Many agents writing in parallel will drift without a single reviewer of locks, leakage, and false accuracy claims.

Inputs:
- CONSTITUTION.md
- wiki/Recursive-Watcher-Protocol.md
- wiki/Agent-Roster.md
- artifacts/watcher/active-tasks.json

Allowed write scope:
- artifacts/watcher/**
- wiki/Agent-Roster.md
- wiki/Recursive-Watcher-Protocol.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- services/**

Acceptance tests:
- artifacts/watcher/recursive-health.json remains valid JSON
- no two active tasks share a write path
- completion reviews use the RLH reprompt template

Finish criteria:
Wave-1 locks stay exclusive. First replay canary is defined once Agent 27 lands a hash.
```
