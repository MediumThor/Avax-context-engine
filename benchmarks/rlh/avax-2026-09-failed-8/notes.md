# avax-2026-09-failed-8

Permanent regression. Exact prices come from the benchmark data dump, not from this note.

Expected process:

- recovery into the ~$8 region can remain a bullish-*pressure* hypothesis only while structure supports it;
- repeated failure near ~$8.15–$8.20 and acceptance below ~$8 flips higher-timeframe state bearish;
- later 5m/15m bounces are relief inside that bear unless explicit reclaim rules fire;
- RLH must say what changed and what did not;
- the loop must not move invalidation lower to save the old bull thesis.

Process coverage for these invariants lives in `tests/harness/challenge/test_challenge.py`. It asserts 4H remains bearish through a 5m relief reading and that an invalidation-edit attempt halts. It is not a hindsight-perfect trade call.
