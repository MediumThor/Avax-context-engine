# Task Contract Template

Copy this into an issue, task file, or agent prompt before implementation.

```md
Task: <single observable outcome>
Agent: <00-39>
Branch: agent/<nn>-<slug>
Priority: P0/P1/P2/P3

Why:
<problem being solved>

Inputs:
- <docs>
- <contracts>
- <data/fixtures>

Allowed write scope:
- <paths>

Forbidden write scope:
- CONSTITUTION.md
- <other stable/shared paths>

Dependencies:
- <accepted interfaces/tasks>

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

## Watcher assignment format

Watcher should prepend:

```md
Watcher owner: Agent 00
Review mode: normal | strict-quant | strict-schema | UI
Competing task group: none | <group-id>
Integration dependency: <task-id or none>
```
