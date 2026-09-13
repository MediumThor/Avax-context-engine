import { useEffect, useMemo, useState } from 'react'
import { MarketChart } from './components/MarketChart'
import { AgentKillSwitch } from './components/AgentKillSwitch'
import { ForecastFan } from './components/ForecastFan'
import { ContextOverlays } from './components/ContextOverlays'
import { AccuracyPanel, type AccuracySlice } from './components/AccuracyPanel'
import { fetchKillSwitch, type KillSwitchState } from './api/killSwitch'
import { fetchMarket } from './api/market'
import type { MarketPayload, StructuralZone, TimeframeState } from './api/types'
import './styles.css'

const TF_ORDER = ['1w', '1d', '4h', '1h', '15m', '5m']

function readAsOf(): string | null {
  return new URLSearchParams(window.location.search).get('as_of')
}

export default function App() {
  const [kill, setKill] = useState<KillSwitchState | null>(null)
  const [killError, setKillError] = useState<string | null>(null)
  const [market, setMarket] = useState<MarketPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const asOf = useMemo(() => readAsOf(), [])

  useEffect(() => {
    fetchKillSwitch()
      .then(setKill)
      .catch((err: unknown) => setKillError(err instanceof Error ? err.message : 'kill switch unreachable'))
  }, [])

  useEffect(() => {
    setLoading(true)
    fetchMarket('AVAXUSDT', asOf)
      .then(setMarket)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'market unavailable'))
      .finally(() => setLoading(false))
  }, [asOf])

  const severed = Boolean(kill?.engaged)
  const health = market?.health.status ?? 'unknown'
  const live = health === 'live' && !severed
  const regimes = TF_ORDER.map((tf) => market?.snapshot.timeframes[tf]).filter(
    (state): state is TimeframeState => Boolean(state),
  )
  const last = market?.candles.at(-1)
  const overlayZones = useMemo(() => {
    if (!market) return []
    const seen = new Set<string>()
    const zones: { id: string; lower: number; upper: number; role: StructuralZone['role']; strength: number; test_count: number; timeframes: string[] }[] = []
    for (const state of Object.values(market.snapshot.timeframes)) {
      for (const zone of [...(state.support_zones ?? []), ...(state.resistance_zones ?? [])]) {
        if (seen.has(zone.id)) continue
        seen.add(zone.id)
        zones.push({
          id: zone.id,
          lower: zone.lower,
          upper: zone.upper,
          role: zone.role,
          strength: zone.strength,
          test_count: zone.test_count,
          timeframes: [state.timeframe],
        })
      }
    }
    return zones
  }, [market])
  const accuracySlices: AccuracySlice[] = useMemo(() => {
    const horizons = market?.metrics.horizons
    if (!horizons) return []
    return Object.entries(horizons).map(([h, block]) => ({
      horizon: Number(h),
      n: block.sample_count ?? null,
      mae: block.drift20?.mae ?? null,
      rmse: block.drift20?.rmse ?? null,
      brier: null,
      ece: null,
      coverage: null,
      baseline_delta:
        block.zero?.mae != null && block.drift20?.mae != null ? block.drift20.mae - block.zero.mae : null,
    }))
  }, [market])

  function openReplay() {
    const hint = market?.replay_hint_as_of
    if (!hint) return
    const url = new URL(window.location.href)
    url.searchParams.set('as_of', hint)
    window.location.assign(url.toString())
  }

  function exitReplay() {
    const url = new URL(window.location.href)
    url.searchParams.delete('as_of')
    window.location.assign(url.toString())
  }

  return (
    <main className={`shell ${severed ? 'severed' : ''}`}>
      <header className="topbar">
        <div>
          <span className="eyebrow">AVAX / USDT · main</span>
          <h1>Context Engine</h1>
        </div>
        <div className={`health ${severed ? 'severedHealth' : live ? '' : 'staleHealth'}`}>
          <span className="dot" />
          {severed
            ? 'AGENTS SEVERED · READ ONLY'
            : health === 'live'
              ? `LIVE · as of ${market?.as_of ?? ''}`
              : health === 'fixture'
                ? `FIXTURE · as of ${market?.as_of ?? ''}`
                : health === 'stale'
                  ? `STALE · as of ${market?.as_of ?? ''}`
                  : 'DATA UNAVAILABLE'}
        </div>
      </header>
      {severed && (
        <div className="banner" role="status">
          Recursive Learning Harness agents are severed. Market context and journaled forecasts remain; no agent may continue until reset.
        </div>
      )}
      {market?.replay && (
        <div className="banner replay" role="status">
          Replay at {market.as_of}. Future candles after this timestamp are hidden. <button type="button" className="quiet" onClick={exitReplay}>Exit replay</button>
        </div>
      )}
      <AgentKillSwitch state={kill} error={killError} onChange={setKill} />
      <section className="workspace">
        <div className="chartPanel">
          <div className="chartHeader">
            <strong>{market ? `$${market.last_price.toFixed(2)}` : '—'}</strong>
            {last && market && (
              <span className={last.close >= market.candles[0].close ? 'bullish' : 'negative'}>
                5m
              </span>
            )}
            <span className="muted">{market?.source ?? ''}</span>
          </div>
          {loading && <p className="pad muted">Loading market state…</p>}
          {error && <p className="pad killError">{error}</p>}
          {market && <MarketChart candles={market.candles} className="chart" />}
          {market && (
            <ContextOverlays
              zones={overlayZones}
              priceMin={Math.min(...market.candles.map((c) => c.low))}
              priceMax={Math.max(...market.candles.map((c) => c.high))}
              aria-label="Structural zones from the Context Engine snapshot"
            />
          )}
        </div>
        <aside className="rail">
          <section className="card">
            <h2>Regime stack</h2>
            {regimes.map((state) => (
              <div className="row" key={state.timeframe}>
                <span>{state.timeframe}</span>
                <b className={state.regime}>{state.regime}</b>
              </div>
            ))}
            <p className="muted">{market?.interpretation || 'Waiting for snapshot.'}</p>
          </section>
          <section className="card">
            <h2>Forecast · next 10</h2>
            <p className="muted">
              {severed
                ? 'Harness degraded. Baseline numbers stay journaled; no new loop will run.'
                : market?.forecast.forecast.notes || 'Baseline drift20. No calibrated probability.'}
            </p>
            {market && (
              <ForecastFan
                horizons={market.forecast.forecast.horizons}
                originClose={market.last_price}
                symbol={market.symbol}
                forecastedAt={market.as_of}
                health={market.forecast.journaled ? 'degraded' : 'unknown'}
                emptyReason="Quantile envelope is not drawn until q10/q50/q90 are journaled. Drift path is a point forecast, not a distribution."
              />
            )}
          </section>
          <section className="card">
            <h2>Walk-forward scores</h2>
            <AccuracyPanel
              slices={accuracySlices}
              baselineName="drift20 vs zero"
              baselineDeltaMetric="mae"
              modelId={market?.forecast.forecast.model_id ?? 'baseline.drift20'}
              coverageInterval="q10–q90 (not scored)"
            />
          </section>
          <section className="card">
            <h2>Thesis</h2>
            <div className="thesis bear">
              <b>Higher-timeframe {market?.snapshot.timeframes['4h']?.regime ?? 'unknown'}</b>
              <p>{market?.interpretation || 'Invalidation is not a 5m bounce.'}</p>
            </div>
            <div className="thesis bull">
              <b>5m {market?.snapshot.timeframes['5m']?.regime ?? 'unknown'}</b>
              <p>Countertrend only unless a higher-timeframe reclaim is journaled.</p>
            </div>
          </section>
          <section className="card">
            <h2>Replay</h2>
            <p className="muted">September 2026 failed-breakout process check: 4H must hold through the 5m bounce.</p>
            {market?.replay_hint_as_of && !market.replay && (
              <button type="button" className="ghost" onClick={openReplay}>
                Replay pre-bounce
              </button>
            )}
          </section>
        </aside>
      </section>
    </main>
  )
}
