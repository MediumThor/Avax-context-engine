# AGENTS.md

Read `CONSTITUTION.md` first. It is immutable project law.

## Agent startup protocol

Before editing anything, every agent must:

1. Read `CONSTITUTION.md`.
2. Read `wiki/Home.md`.
3. Read the directive for its subsystem. Harness / loop / explanation work also reads `wiki/Recursive-Learning-Harness.md` and `wiki/Recursive-Agent-Batch.md`.
4. Pull/read the latest `main` state before beginning work.
5. Inspect current code/tests for that subsystem.
6. Write a task contract containing scope, files, assumptions, tests, and finish criteria.
7. Confirm no active agent owns the same write scope.

## Rapid-prototype mainline mode

`main` is the only persistent product branch and the canonical state of the project.

Agents may use isolated local worktrees or temporary branches to avoid concurrent writes, but those are disposable implementation surfaces only. They are never allowed to become a second product state.

Accepted work is integrated into `main` immediately after Watcher review and required tests. New agents always start from the latest `main`. If a temporary branch has diverged, the Watcher reconciles it onto current `main`, reruns the relevant tests, records the resulting main SHA, and then treats the temporary branch as obsolete.

Do not create long-lived `foundation`, `staging`, `integration`, or feature branches for normal development. The purpose of branch isolation is conflict avoidance, not delayed integration.

## Agent numbering

- Agent 00: Watcher / integrator / correction authority.
- Agents 01-08: data, FreqAI, features, modeling, simulation.
- Agents 09-16: Context Engine, structure, regimes, patterns, thesis ledger.
- Agents 17-24: web UI, charts, navigation, UX, accessibility.
- Agents 25-30: internal AI harness / Recursive Learning Harness, tools, memory, explanation layer. Wave 1 roster: `wiki/Agent-Roster.md`.
- Agents 31-35: infrastructure, APIs, observability, CI, reproducibility.
- Agents 36-39: independent QA, dogfooding, red-team, benchmark replication.

Numbers are lanes, not permanent identities. The Watcher may reassign lanes.

## Concurrency rule

No two agents may write the same path concurrently. Shared contracts have one designated owner per active batch. Agents may work in parallel against accepted contracts while the Watcher keeps `main` continuously integrated.

## Required output for every task

Every agent completion report must include:

- what changed;
- exact files changed;
- tests run and results;
- metrics before/after where applicable;
- known limitations;
- documentation updated;
- whether any contract/schema changed;
- the commit SHA containing the accepted work on `main`;
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
- weaken or delete regression cases to make metrics improve;
- leave accepted product work stranded only on a temporary branch.

## Review standard

A task is not complete until code, tests, docs, and operability are coherent on `main`. "Works on my branch" is insufficient. The Watcher is expected to reject incomplete integration.
