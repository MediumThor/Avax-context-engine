export type Regime = 'bullish' | 'bearish' | 'neutral' | 'transition_up' | 'transition_down' | 'unknown'
export type DataHealth = 'live' | 'stale' | 'fixture' | 'unknown'

export interface Candle {
  time: number
  open: number
  high: number
  low: number
  close: number
}

export interface TimeframeState {
  timeframe: string
  regime: Regime
  swing_state: string
  volatility: string
  close: number
  as_of: string
  support_zones?: StructuralZone[]
  resistance_zones?: StructuralZone[]
}

export interface StructuralZone {
  id: string
  lower: number
  upper: number
  role: 'support' | 'resistance' | 'mixed'
  strength: number
  test_count: number
}

export interface ForecastHorizon {
  h: number
  expected_cum_log_return: number
  drift20_cum_log_return?: number
  zero_cum_log_return?: number
  p_close_above_origin: number | null
  confidence_source?: string
  /** Optional distribution / simple-return fields. Absent until a distribution model is journaled. */
  expected_cum_return?: number | null
  q10_cum_return?: number | null
  q50_cum_return?: number | null
  q90_cum_return?: number | null
  q10_cum_log_return?: number | null
  q50_cum_log_return?: number | null
  q90_cum_log_return?: number | null
}

export interface AnalogMatch {
  origin_close_time: string
  distance: number
  realized_h10_log_return: number
  known_at: string
  note: string
}

export interface PatternHypothesisSummary {
  id: string
  kind: string
  status: string
  timeframe: string
  evidence_score: number
  score_provenance: string
}

export interface ThesisRuleSummary {
  id: string
  kind: string
  price: number
  timeframe: string
  description?: string
}

export interface ThesisSummary {
  id: string
  direction: 'bull' | 'bear'
  kind: string
  status: string
  timeframe: string
  regime_relation?: string
  created_at: string
  closed_at?: string | null
  closure_reason?: string | null
  evidence?: string[]
  counter_evidence?: string[]
  invalidation_rules?: ThesisRuleSummary[]
  confirmation_rules?: ThesisRuleSummary[]
  note?: string
}

export interface FibLevelSummary {
  kind: string
  ratio: number
  price: number
  direction: string
  known_at: string
  status: string
  is_guaranteed_support: boolean
  role?: string
}

export interface MarketPayload {
  symbol: string
  source: string
  as_of: string
  health: { status: DataHealth; age_seconds: number; last_close: string }
  last_price: number
  snapshot: {
    timeframes: Record<string, TimeframeState>
    cross_market?: Record<string, unknown>
    analogs?: AnalogMatch[]
    pattern_hypotheses?: PatternHypothesisSummary[]
    fib_levels?: FibLevelSummary[]
    theses?: ThesisSummary[]
  }
  interpretation: string
  forecast: { forecast: { horizons: ForecastHorizon[]; model_id: string; notes: string }; journaled: boolean }
  metrics: {
    available: boolean
    validation?: string
    horizons?: Record<
      string,
      {
        sample_count: number
        zero?: { mae?: number; rmse?: number }
        drift20: { mae: number; rmse?: number; signed_direction?: { accuracy: number | null; sample_count: number } }
        probability?: { sample_count?: number; brier?: number | null; ece?: number | null }
        interval?: { sample_count?: number; coverage?: number | null }
      }
    >
  }
  candles: Candle[]
  replay: boolean
  replay_hint_as_of?: string | null
  execution_enabled: boolean
}
