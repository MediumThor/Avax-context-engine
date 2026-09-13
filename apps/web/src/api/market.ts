import type { MarketPayload } from './types'

const base = import.meta.env.VITE_API_BASE ?? ''

export async function fetchMarket(symbol = 'AVAXUSDT', asOf?: string | null): Promise<MarketPayload> {
  const params = new URLSearchParams()
  if (asOf) params.set('as_of', asOf)
  params.set('limit', '576')
  const qs = params.toString()
  const res = await fetch(`${base}/api/v1/market/${symbol}${qs ? `?${qs}` : ''}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<MarketPayload>
}
