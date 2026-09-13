# Task Contract Template

Copy this into an issue, task file, or agent prompt before implementation.

```md
Task: <single observable outcome>
Agent: <00-39>
Branch: agent/<nn>-<slug>
Priority: P0/P1/P2/P3
Source main commit: <sha>
Dependency gate: G0-G7

Why:
<problem being solved>

Inputs:
- <docs>
- <contracts>
- <data/fixtures>
- <forecast/context/error-case IDs>

Allowed write scope:
- <paths>

Forbidden write scope:
- CONSTITUTION.md
- <other stable/shared paths>

Dependencies:
- <accepted interfaces/tasks + versions/commit SHAs>

Implementation requirements:
1. ...

Acceptance tests:
- command: ...
  expected: ...

Metrics gate:
- baseline: ...
- required result: ...

Historical regressions:
- ...

Recursive-learning evidence:
- learning candidate: <id or none>
- evaluation plan: <frozen id or none>
- known failed approaches: <ids or none>

Docs to update:
- ...

Completion report must contain:
- files changed
- test results
- metrics before/after
- limitations
- next task

Finish criteria:
<binary observable completion state>
```

The task owner branches from the recorded `main` commit. If a dependency contract changes before completion, stop and rebase/recontract rather than silently coding against a stale or imagined interface.

## Watcher assignment format

Watcher should prepend:

```md
Watcher owner: Agent 00
Review mode: normal | strict-quant | strict-schema | UI | rlh-loop
Competing task group: none | <group-id>
Integration dependency: <task-id or none>
Target main gate: <tests/checks required after merge>
```
