import type { Candle, MarketPayload } from './types'
import { CHART_LIMITS, type ChartTimeframe } from '../components/TimeframeSwitcher'

const base = import.meta.env.VITE_API_BASE ?? ''

export async function fetchMarket(
  symbol = 'AVAXUSDT',
  asOf?: string | null,
  timeframe: ChartTimeframe = '5m',
): Promise<MarketPayload> {
  const params = new URLSearchParams()
  if (asOf) params.set('as_of', asOf)
  params.set('timeframe', timeframe)
  params.set('limit', String(CHART_LIMITS[timeframe]))
  const qs = params.toString()
  const res = await fetch(`${base}/api/v1/market/${symbol}?${qs}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<MarketPayload>
}

export async function fetchChartCandles(
  symbol = 'AVAXUSDT',
  timeframe: ChartTimeframe = '5m',
  asOf?: string | null,
): Promise<{ timeframe: string; candles: Candle[] }> {
  const params = new URLSearchParams()
  params.set('timeframe', timeframe)
  params.set('limit', String(CHART_LIMITS[timeframe]))
  if (asOf) params.set('as_of', asOf)
  const res = await fetch(`${base}/api/v1/market/${symbol}/candles?${params}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<{ timeframe: string; candles: Candle[] }>
}
