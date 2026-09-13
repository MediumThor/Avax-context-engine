# Task contract: Prediction improvement loop

```md
Task: Publish the operational loop that diagnoses the codebase, names missing market information, requests owner access, implements bounded improvements, and tracks walk-forward outcomes against AVAX forecast quality.
Agent: 00 / 36 / 31 (single writer on this branch)
Branch: cursor/prediction-improvement-loop-ee66
Priority: P0

Why:
SLICE-001 made the UI honest. The product still cannot claim AVAX forecast skill. Agents need one playbook for "find what is wrong or missing → ask for access → implement → measure → keep or reject" without enabling live leverage trades or inventing data.

Allowed write scope:
- wiki/Prediction-Improvement-Loop.md
- wiki/Information-Gaps.md
- wiki/improvement/**
- wiki/Home.md
- wiki/Build-Roadmap.md
- wiki/Agent-Roster.md
- wiki/Simulation-Accuracy.md
- wiki/tasks/IMP-000-improvement-loop-contract.md
- packages/contracts/improvement/**
- tests/contracts/test_improvement_schemas.py
- .cursor/rules/prediction-improvement.mdc

Forbidden:
- CONSTITUTION.md
- enabling trade execution
- fabricating calibrated probabilities
- weakening September 2026 regressions

Acceptance:
- Home and roadmap link the loop
- schemas + examples validate
- access-request path asks the owner instead of inventing sources
- leverage-aware scoring is defined as simulation only
```
