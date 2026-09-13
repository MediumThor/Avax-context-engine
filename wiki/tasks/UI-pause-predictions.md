# Task contract: Pause prediction agents (header button)

```md
Task: Expose a compact header button that pauses prediction agents (new live forecast journal writes + RLH loops) using the accepted kill-switch API.
Agent: 17
Branch: cursor/pause-predictions-ui-d94c
Priority: P1
Source main commit: c9a56c27682ec408e001a5a6ed92ab15f5df74ee
Dependency gate: G0 / G6 shell

Why:
The operator asked to pause prediction agents and to have a UI button for that action. The accepted kill-switch API already blocks new loops and live forecast journal writes, but the control is a bulky "Kill all agents" card that displaces the chart instead of a header pause button.

Inputs:
- wiki/UI-Directive.md (sticky header + confirmation sheet)
- wiki/Agent-Roster.md / packages/harness/kill_switch.py
- services/api/runtime.py persist gate (`is_engaged`)

Allowed write scope:
- apps/web/src/components/AgentKillSwitch.tsx
- apps/web/src/App.tsx
- apps/web/src/styles.css
- packages/harness/kill_switch.py (effects list only: document pause_new_forecasts)
- tests/test_kill_switch.py
- wiki/tasks/UI-pause-predictions.md
- wiki/UI-Directive.md
- wiki/Agent-Roster.md
- wiki/Recursive-Learning-Contracts.md
- wiki/Navigation-Directive.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/
- enabling trade execution
- weakening journal immutability or leakage tests
- artifacts/watcher/kill-switch.json (do not ship an engaged default)

Dependencies:
- Existing GET/POST /api/v1/agents/kill-switch and /reset
- PrototypeRuntime.forecast persist gate

Implementation requirements:
1. Compact sticky-header control labeled "Pause predictions" / "Resume predictions".
2. Phone confirmation uses a focused sheet/dialog; do not keep a permanently expanded kill card.
3. Pause uses the kill-switch engage path (halts loops, freezes promotion, blocks new forecast journal writes).
4. Resume uses the logged reset path. Journals and Constitution stay intact.
5. Do not claim an unconnected external process was forcibly terminated.

Acceptance tests:
- command: python -m pytest -q tests/test_kill_switch.py
  expected: all pass, including persist-blocked and loop 423
- command: browser verify at 360px and desktop that the header button pauses and resumes
  expected: confirmation sheet, banner, forecast copy updates; chart remains visible

Metrics gate:
- none (operability control)

Historical regressions:
- kill switch still blocks POST /api/v1/loops/run with 423
- journal rows written before pause are not deleted

Docs to update:
- wiki/UI-Directive.md
- wiki/Agent-Roster.md
- wiki/Recursive-Learning-Contracts.md
- wiki/Navigation-Directive.md

Finish criteria:
Header pause button is the operator control; pause blocks new prediction writes/loops; resume is a second confirmed, logged action.
```
