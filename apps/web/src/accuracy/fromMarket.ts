import type { MarketPayload } from '../api/types'
import type { AccuracySlice } from '../components/AccuracyPanel'

export function accuracySlicesFromMarket(market: MarketPayload | null): AccuracySlice[] {
  const horizons = market?.metrics.horizons
  if (!horizons) return []
  return Object.entries(horizons).map(([h, block]) => {
    const journaledPoint = block.drift20?.source === 'journal'
    const sameSource =
      !journaledPoint || block.zero?.source === 'journal' || block.zero?.source === block.drift20?.source
    return {
      horizon: Number(h),
      n:
        block.q50?.sample_count ??
        (journaledPoint ? block.drift20?.sample_count : null) ??
        block.probability?.sample_count ??
        block.sample_count ??
        null,
      mae: block.drift20?.mae ?? null,
      rmse: block.drift20?.rmse ?? null,
      brier: block.probability?.brier ?? null,
      ece: block.probability?.ece ?? null,
      coverage: block.interval?.coverage ?? null,
      baseline_delta:
        sameSource && block.zero?.mae != null && block.drift20?.mae != null
          ? block.drift20.mae - block.zero.mae
          : null,
      challenger_mae: block.q50?.mae ?? null,
      challenger_delta: block.q50_mae_minus_drift20_mae ?? null,
      htf_mae: block.htf_regime?.mae ?? null,
      htf_delta: block.htf_mae_minus_drift20_mae ?? null,
      htf_n: block.htf_regime?.sample_count ?? null,
      live_n: block.probability_held_out_live?.sample_count ?? null,
      live_brier: block.probability_held_out_live?.brier ?? null,
      live_ece: block.probability_held_out_live?.ece ?? null,
    }
  })
}
