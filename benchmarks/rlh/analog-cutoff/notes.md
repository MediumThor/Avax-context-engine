# analog-cutoff

Leakage regression for analog search cutoff.

Expected process:

- `analog.search` refuses documents with `known_at` after fixture `as_of`;
- a refused tool call is success for the leakage probe;
- no post-cutoff analog may influence synthesis.

This fixture labels tool as_of discipline, not analog ranking quality.