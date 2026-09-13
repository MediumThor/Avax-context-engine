# stale-data

Process regression for degraded data health.

Expected process:

- stale or unknown data forces a degraded halt (`halt_reason=stale_or_unknown_data`);
- `confidence_source` stays `insufficient-data`;
- prose must not read as high-conviction forecast despite missing freshness.

This fixture labels health discipline, not hindsight trade quality.