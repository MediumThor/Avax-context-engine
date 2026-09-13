import { useEffect, useMemo, useState } from 'react'
import { MarketChart } from './components/MarketChart'
import { AgentKillSwitch } from './components/AgentKillSwitch'
import { fetchKillSwitch, type KillSwitchState } from './api/killSwitch'
import { fetchMarket } from './api/market'
import type { MarketPayload, TimeframeState } from './api/types'
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
  const driftMae = market?.metrics.horizons?.['1']?.drift20.mae
  const driftN = market?.metrics.horizons?.['1']?.sample_count
  const last = market?.candles.at(-1)

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
              <ol className="horizons">
                {market.forecast.forecast.horizons.map((h) => (
                  <li key={h.h}>
                    h{h.h} drift {h.expected_cum_log_return.toFixed(4)} · p unset
                  </li>
                ))}
              </ol>
            )}
            {market?.metrics.available && driftN != null && (
              <p className="muted">
                Walk-forward h=1 drift MAE {driftMae?.toFixed(4)} · n={driftN} · {market.metrics.validation}
              </p>
            )}
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
