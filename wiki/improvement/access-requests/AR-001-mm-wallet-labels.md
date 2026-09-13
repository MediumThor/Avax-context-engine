# Access request AR-001 — market-maker and desk wallet labels

```text
I cannot truthfully improve AVAX forecasts here because: GAP-MM-LABELS.
Public options: raw C-Chain explorer APIs without reliable desk labels; heuristic clustering that we must not present as fact.
I need from you: a read-only address list you trust, or a Nansen/Arkham/Dune grant, or "skip this family".
Until then the ticket stays blocked-on-access and forecasts will keep ignoring labeled inventory flow.
```

- **Request id:** AR-001
- **Gap:** GAP-MM-LABELS
- **Why it changes a leveraged-operator decision:** Exchange-hot-wallet and MM inventory bursts often precede AVAX perp squeezes. Unlabeled flow is just noise; invented labels are worse than no feature.
- **Candidate source + docs URL:** owner-supplied CSV; or Nansen / Arkham / Dune (vendor docs after you pick one)
- **Free tier?** owner list = yes; vendors = paid / limited
- **Scopes:** read-only address → label → `labeled_at`
- **ToS / leakage / retention risk:** third-party attributions may be non-redistributable; store vendor + as-of, not scraped HTML
- **Will not do:** place orders; deanonymize private people; backfill labels before `labeled_at`
- **Snapshot plan:** checksum of the allow-list; each label has `known_at`
- **Owner decision:** pending
- **Decided at:**
