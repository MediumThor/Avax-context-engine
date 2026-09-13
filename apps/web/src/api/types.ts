export type Regime = 'bullish' | 'bearish' | 'neutral' | 'transition_up' | 'transition_down' | 'unknown'
export type DataHealth = 'live' | 'stale' | 'fixture' | 'unknown'

export interface Candle {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume?: number
  ema9?: number
  ema20?: number
  ema50?: number
  ema100?: number
  ema200?: number
}

export interface SwingPivot {
  time: number
  known_at: string
  price: number
  kind: 'high' | 'low'
  timeframe?: string
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
  swing_pivots?: SwingPivot[]
}

export interface StructuralZone {
  id: string
  lower: number
  upper: number
  role: 'support' | 'resistance' | 'mixed'
  strength: number
  test_count: number
  status?: string
  interaction?: string | null
  known_at?: string | null
  last_test_at?: string | null
  outcome?: string | null
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
  ledger?: 'journaled' | 'ephemeral'
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

export interface LoopSummary {
  ran: boolean
  reason?: string
  loop_id?: string
  encoder_memory_id?: string
  encoder_memory_hash?: string
  halt_reason?: string
  analog_count?: number
  hypothesis_ids?: string[]
  zone_count?: number
  persisted?: boolean
  note?: string
}

/** Request-path catch-up counts. Remaining is a coverage gap, not accuracy. */
export interface ShadowJournalStatus {
  wrote: number
  remaining: number
  model_id: string
  rounds_used?: number
  budget?: number
  blocked?: boolean
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
  forecast: {
    forecast: { horizons: ForecastHorizon[]; model_id: string; notes: string }
    journaled: boolean
    loop?: LoopSummary
    shadow_journal?: ShadowJournalStatus
  }
  metrics: {
    available: boolean
    validation?: string
    horizons?: Record<
      string,
      {
        sample_count: number
        zero?: { mae?: number; rmse?: number; sample_count?: number; source?: string }
        drift20: {
          mae: number
          rmse?: number
          sample_count?: number
          source?: string
          signed_direction?: { accuracy: number | null; sample_count: number }
        }
        probability?: { sample_count?: number; brier?: number | null; ece?: number | null; source?: string }
        interval?: { sample_count?: number; coverage?: number | null; source?: string }
        q50?: { mae?: number; rmse?: number; sample_count?: number; source?: string }
        q50_mae_minus_drift20_mae?: number | null
      }
    >
    challenger?: {
      model_id?: string
      origin_count?: number
      q50_mae_below_drift20_on_all_scored_horizons?: boolean | null
      notes?: string
    }
    promotion_allowed?: boolean
  }
  candles: Candle[]
  chart_timeframe?: string
  chart_candles?: Partial<Record<string, Candle[]>>
  replay: boolean
  replay_hint_as_of?: string | null
  execution_enabled: boolean
}
