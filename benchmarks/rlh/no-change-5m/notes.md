# no-change-5m

Process regression for immaterial 5m updates.

Expected process:

- ENCODE_CHECK runs first;
- when the new 5m candle does not materially change encoder facts, the loop halts with `halt_reason=no_change`;
- parent regime is preserved without requiring max_depth exhaustion;
- no directional synthesis or invented forecast language.

This fixture labels halt discipline, not price direction.