import type { MarketPayload, ShadowJournalStatus } from './types'

const base = import.meta.env.VITE_API_BASE ?? ''

export async function fetchMarket(symbol = 'AVAXUSDT', asOf?: string | null): Promise<MarketPayload> {
  const params = new URLSearchParams()
  if (asOf) params.set('as_of', asOf)
  const qs = params.toString()
  const res = await fetch(`${base}/api/v1/market/${symbol}${qs ? `?${qs}` : ''}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<MarketPayload>
}

export async function drainShadowJournal(
  symbol = 'AVAXUSDT',
  budget = 200,
  rounds = 20,
): Promise<ShadowJournalStatus> {
  const params = new URLSearchParams({ symbol, budget: String(budget), rounds: String(rounds) })
  const res = await fetch(`${base}/api/v1/journal/catchup?${params}`, { method: 'POST' })
  if (res.status === 423) {
    throw new Error('Kill switch blocks journal drain. No rows written.')
  }
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<ShadowJournalStatus>
}
