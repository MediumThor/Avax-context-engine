export type Regime = 'bullish' | 'bearish' | 'neutral' | 'transition_up' | 'transition_down' | 'unknown'

export interface Candle { time:number; open:number; high:number; low:number; close:number }
export interface StructuralZone { id:string; lower:number; upper:number; role:'support'|'resistance'|'mixed'; strength:number; test_count:number }
export interface ForecastHorizon { h:number; expected_cum_return:number; p_close_above_origin:number; q10_cum_return:number; q50_cum_return:number; q90_cum_return:number }
