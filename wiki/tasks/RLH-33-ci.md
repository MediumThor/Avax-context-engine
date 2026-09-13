# RLH-33 — CI

```md
Task: GitHub Actions workflow that runs RLH contract tests on PRs touching harness or recursive contracts.
Agent: 33
Branch: cursor/agent-33-rlh-ci-ee66
Model: Grok 4.6
Priority: P1

Why:
Schema drift must fail in CI, not after merge.

Inputs:
- tests/contracts/test_recursive_schemas.py
- wiki/Testing-Directive.md

Allowed write scope:
- .github/workflows/**

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- services/**

Implementation requirements:
1. Workflow name rlh-contracts (or similar).
2. Run python3 tests/contracts/test_recursive_schemas.py on ubuntu-latest.
3. Path filters: packages/contracts/recursive/**, services/harness/**, tests/contracts/**, tests/rlh/**, tests/harness/**, tests/leakage/rlh/**, wiki/Recursive-*.md.
4. Also allow workflow_dispatch / push to main.

Acceptance tests:
- workflow YAML is valid enough to parse
- command in the workflow matches the local passing test

Finish criteria:
PR check exists. No extra unpaid services.
```
