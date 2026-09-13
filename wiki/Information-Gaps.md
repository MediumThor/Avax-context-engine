# Information gaps

Living catalog of facts the forecast stack **cannot yet use** at `as_of`. Updated whenever a dogfood miss or codebase scan names a new hole.

Playbook: [`Prediction-Improvement-Loop.md`](Prediction-Improvement-Loop.md). Machine form: `packages/contracts/improvement/information-gap.schema.json`.

Status values: `missing` | `partial` | `blocked-on-access` | `ingested` | `rejected`.

## How to add a row

1. Give it a stable `gap_id` (`GAP-…`).
2. Say which forecast decision it would change.
3. List candidate sources in discovery order (public → keyed → paid → human).
4. File an AccessRequest instead of inventing the series.
5. When ingested, point at the adapter, manifest field, and `known_at` rule.

## Current catalog

| gap_id | family | status | decision it would change | candidate sources | access |
| --- | --- | --- | --- | --- | --- |
| GAP-OHLCV-CEX | AVAX/BTC/ETH 5m | partial | backbone path | Binance Vision (in repo), other CEX public klines | none for Vision |
| GAP-FUNDING | perp funding / mark | missing | carry, squeeze vs grind | Binance futures public premiumIndex; Coinglass (key) | ask if leaving Binance |
| GAP-OI-LIQ | open interest, liquidations | missing | cascade risk, stop runs | Binance futures public; Coinglass/Laevitas (key) | ask for paid |
| GAP-BOOK | L2 / CVD | missing | 5–30m pressure | exchange WS; Tardis (paid) | ask for Tardis |
| GAP-BTC-ETH-LIVE | live BTC/ETH beside AVAX | partial | sync vs decouple | Vision / same client as AVAX | none |
| GAP-MACRO-METAL | gold | missing | risk/inflation regime (slow) | FRED, Stooq, Yahoo (license check); Polygon (key) | ask if paid |
| GAP-MACRO-OIL | WTI / Brent | missing | risk/inflation regime (slow) | EIA, FRED, Stooq; paid vendors | ask if paid |
| GAP-MACRO-RATES | US10Y, DXY, real yield | missing | liquidity / crypto beta | FRED (DGS10, DTWEXBGS); paid FX | ask if paid |
| GAP-NEWS | headlines, unlocks, incidents | missing | jump risk the 5m model cannot see | official RSS, GDELT, CryptoPanic (key), paid wires | ask for CryptoPanic/wires |
| GAP-ONCHAIN-AVAX | C-Chain flows, CEX hot wallets | missing | inventory, exchange premium | Snowtrace/Avascan APIs; Dune (key) | ask for Dune/explorer key |
| GAP-MM-LABELS | market-maker / desk clusters | missing | interpret flow without false attribution | owner-supplied list; Nansen/Arkham (paid) | **always ask** |
| GAP-OPTIONS | BTC/AVAX IV, skew | missing | crash premium | Deribit public; Laevitas (key) | ask if paid |
| GAP-THESIS | ledger objects | missing | immutable invalidation | in-repo (no vendor) | none |
| GAP-CALIBRATION | probabilistic p / quantiles | missing | honest uncertainty | journal + walk-forward; no vendor | none |

## Owner asks currently expected

Use the sentence in the playbook. Concrete asks right now:

1. **Wallet labels (AR-001)** — provide a read-only list of addresses you want watched (hot wallets, known MM clusters), or grant Nansen/Arkham/Dune. Do not let agents invent labels.
2. **News** — approve CryptoPanic or a wire, or say "official RSS only."
3. **Derivatives aggregates** — approve Coinglass/Laevitas or stay on raw Binance public futures.
4. **Macro vendors** — approve FRED-only vs Polygon/Twelve Data.
5. **Historical book** — approve Tardis if 5m book features are in scope.

Denied families stay `rejected` with reason. They are not silent holes.

## Leakage rules for every new source

- Feature `known_at` ≥ source event time and ≤ forecast `as_of`.
- News: `published_at` and later correction time.
- Macro bars: last **closed** bar only.
- Wallet labels: `labeled_at` — a 2026 label must not be applied to 2024 features unless the label existed then.
- No random shuffle. No future candles in aggregates.
