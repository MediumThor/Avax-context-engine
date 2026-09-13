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
}

export interface ForecastHorizon {
  h: number
  expected_cum_log_return: number
  drift20_cum_log_return?: number
  zero_cum_log_return?: number
  /** Simple-return path when a calibrated model exists. Absent on drift20. */
  expected_cum_return?: number | null
  q10_cum_return?: number | null
  q50_cum_return?: number | null
  q90_cum_return?: number | null
  p_close_above_origin: number | null
  confidence_source: string
}

export interface MarketPayload {
  symbol: string
  source: string
  as_of: string
  health: { status: DataHealth; age_seconds: number; last_close: string }
  last_price: number
  snapshot: { timeframes: Record<string, TimeframeState>; cross_market?: Record<string, unknown> }
  interpretation: string
  forecast: { forecast: { horizons: ForecastHorizon[]; model_id: string; notes: string }; journaled: boolean }
  metrics: { available: boolean; validation?: string; horizons?: Record<string, { sample_count: number; drift20: { mae: number; signed_direction: { accuracy: number | null; sample_count: number } } }> }
  candles: Candle[]
  replay: boolean
  replay_hint_as_of?: string | null
  execution_enabled: boolean
}
