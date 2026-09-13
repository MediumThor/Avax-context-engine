# replay-parity

Replay integrity regression.

Expected process:

- `rebuild_policy=exact`;
- live LoopTrace hash equals replay hash;
- future candles remain hidden at `as_of` (`reveal_future=false`).

This fixture labels determinism, not forecast accuracy.