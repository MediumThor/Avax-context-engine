# Freqtrade / FreqAI license boundary

This directory is an **adapter**, not a fork.

- Upstream: https://github.com/freqtrade/freqtrade.git
- Pinned commit: `c064be5325ad6941a2789add795434e6a13dffe9`
- Upstream license: GNU General Public License v3.0 (GPL-3.0)
- Local pin record: [`pin.json`](pin.json)
- Repository lock (read-only from this task): [`../../upstream.lock.json`](../../upstream.lock.json)

`scripts/bootstrap_freqtrade.sh` clones the **complete** upstream repository into `vendor/freqtrade` (gitignored) and checks out the pin. After checkout it writes `vendor/freqtrade/.avax-upstream-manifest.json` recording the commit and the upstream LICENSE path.

Do not copy large upstream source trees into `packages/`. Keep custom Context Engine, evaluator, harness, and UI behind this adapter.

Review GPL obligations before distributing a combined derivative work. This adapter does not enable live trading or order execution.
