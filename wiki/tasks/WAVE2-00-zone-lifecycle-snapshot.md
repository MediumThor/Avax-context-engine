# WAVE2-00 — Zone lifecycle drives build_snapshot

```md
Task: Wire ZoneTracker into ContextEngine.build_snapshot so each timeframe's support/resistance is a walked lifecycle, not a static cluster at T.
Agent: 00
Branch: cursor/zone-lifecycle-snapshot-8771
Priority: P0
Source main commit: 6b0fb4b

Why:
WAVE2-11 built chronological zone lifecycle but forbade engine.py. Snapshots still used cluster_zones at the last close, so status/provenance never reached the journal, harness, or UI. Constitution §8/§9 require persistent structure with frozen bounds.

Allowed write scope:
- packages/context_engine/zones.py
- packages/context_engine/engine.py
- packages/context_engine/models.py
- tests/test_engine_zones.py
- tests/test_zones.py
- apps/web/src/api/types.ts
- apps/web/src/App.tsx
- wiki/tasks/WAVE2-00-zone-lifecycle-snapshot.md
- wiki/Context-Engine-Directive.md
- wiki/Market-State-Spec.md
- wiki/Data-Contracts.md
- wiki/Build-Roadmap.md
- wiki/Agent-Build-Plan.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py
- packages/context_engine/structure.py (import only)

Implementation requirements:
1. Seed zone specs from confirmed pivots using price at formation known_at, not T's close.
2. ZoneTracker opens a spec only when the observing bar is at or after known_at.
3. Each timeframe walks only its own closed resampled bars. 5m cannot accept a 4h zone.
4. Bounds stay frozen. September ~$8 overlap is not a successful reclaim after the relief bounce.
5. Snapshot StructuralZone carries status, interaction, known_at, outcome.
6. Future-bar perturbation at T does not change zone lifecycle.

Acceptance tests:
- tests/test_zones.py still green
- tests/test_engine_zones.py: lifecycle fields, bounce does not reclaim ~$8, future perturbation hash-stable
- WAVE2 unconfirmed pivot still absent

Finish criteria:
build_snapshot zones are tracked objects. No confidence claim. No forecast rewrite.
```
