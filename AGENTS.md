# AGENTS.md

Read `CONSTITUTION.md` first. It is immutable project law.

## Agent startup protocol

Before editing anything, every agent must:

1. Read `CONSTITUTION.md`.
2. Read `wiki/Home.md`.
3. Read the directive for its subsystem. Harness / loop / explanation work also reads `wiki/Recursive-Learning-Harness.md` and `wiki/Recursive-Agent-Batch.md`.
4. Inspect current code/tests for that subsystem.
5. Write a task contract containing scope, files, assumptions, tests, and finish criteria.
6. Confirm no active agent owns the same write scope.

## Agent numbering

- Agent 00: Watcher / integrator / correction authority.
- Agents 01-08: data, FreqAI, features, modeling, simulation.
- Agents 09-16: Context Engine, structure, regimes, patterns, thesis ledger.
- Agents 17-24: web UI, charts, navigation, UX, accessibility.
- Agents 25-30: internal AI harness / Recursive Learning Harness, tools, memory, explanation layer. Wave 1 roster: `wiki/Agent-Roster.md`..
- Agents 31-35: infrastructure, APIs, observability, CI, reproducibility.
- Agents 36-39: independent QA, dogfooding, red-team, benchmark replication.

Numbers are lanes, not permanent identities. The Watcher may reassign lanes.

## Branch/worktree rule

Agents must work on isolated branches or worktrees named `agent/<nn>-<task>`. Never let multiple agents write the same file concurrently. Shared contracts must be changed by a designated schema owner and reviewed by Agent 00.

## Required output for every task

Every agent completion report must include:

- what changed;
- exact files changed;
- tests run and results;
- metrics before/after where applicable;
- known limitations;
- documentation updated;
- whether any contract/schema changed;
- recommended next task.

## Forbidden behavior

Agents may not:

- change `CONSTITUTION.md`;
- claim accuracy from in-sample results;
- random-shuffle time-series validation;
- use future candles in features;
- silently change prediction targets;
- turn external execution on;
- replace the custom Context Engine with an LLM-only narrative system;
- merge failing work because it appears promising;
- weaken or delete regression cases to make metrics improve.

## Review standard

A task is not complete until code, tests, docs, and operability are all coherent. "Works on my branch" is insufficient. The Watcher is expected to reject incomplete integration.
