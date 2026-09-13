import { useEffect, useMemo, useState } from 'react'
import { MarketChart } from './components/MarketChart'
import { AgentKillSwitch } from './components/AgentKillSwitch'
import { ForecastFan } from './components/ForecastFan'
import { ContextOverlays } from './components/ContextOverlays'
import { ContextEvidence } from './components/ContextEvidence'
import { AccuracyPanel, type AccuracySlice } from './components/AccuracyPanel'
import { fetchKillSwitch, type KillSwitchState } from './api/killSwitch'
import { fetchChartCandles, fetchMarket } from './api/market'
import type { Candle, MarketPayload, StructuralZone, TimeframeState } from './api/types'
import { TimeframeSwitcher, isChartTimeframe, type ChartTimeframe } from './components/TimeframeSwitcher'
import './styles.css'

const TF_ORDER = ['1w', '1d', '4h', '1h', '15m', '5m']
const LIVE_POLL_MS = 20_000

function readAsOf(): string | null {
  return new URLSearchParams(window.location.search).get('as_of')
}

function readTf(): ChartTimeframe {
  const raw = new URLSearchParams(window.location.search).get('tf')
  return isChartTimeframe(raw) ? raw : '5m'
}

function writeTf(tf: ChartTimeframe) {
  const url = new URL(window.location.href)
  if (tf === '5m') url.searchParams.delete('tf')
  else url.searchParams.set('tf', tf)
  window.history.replaceState({}, '', url)
}

export default function App() {
  const [kill, setKill] = useState<KillSwitchState | null>(null)
  const [killError, setKillError] = useState<string | null>(null)
  const [market, setMarket] = useState<MarketPayload | null>(null)
  const [chartCandles, setChartCandles] = useState<Candle[] | null>(null)
  const [chartTf, setChartTf] = useState<ChartTimeframe>(readTf)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const asOf = useMemo(() => readAsOf(), [])

  useEffect(() => {
    fetchKillSwitch()
      .then(setKill)
      .catch((err: unknown) => setKillError(err instanceof Error ? err.message : 'kill switch unreachable'))
  }, [])

  useEffect(() => {
    let cancelled = false
    async function load(initial: boolean) {
      if (initial) setLoading(true)
      try {
        const payload = await fetchMarket('AVAXUSDT', asOf)
        if (!cancelled) {
          setMarket(payload)
          setError(null)
        }
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'market unavailable')
      } finally {
        if (!cancelled && initial) setLoading(false)
      }
    }
    void load(true)
    if (asOf) return () => {
      cancelled = true
    }
    const timer = window.setInterval(() => {
      void load(false)
    }, LIVE_POLL_MS)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [asOf])

  useEffect(() => {
    let cancelled = false
    async function loadChart() {
      try {
        const body = await fetchChartCandles('AVAXUSDT', chartTf, asOf)
        if (!cancelled) {
          setChartCandles(body.candles)
          setError(null)
        }
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'chart unavailable')
      }
    }
    void loadChart()
    if (asOf) return () => {
      cancelled = true
    }
    const timer = window.setInterval(() => {
      void loadChart()
    }, LIVE_POLL_MS)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [asOf, chartTf])

  function selectTf(tf: ChartTimeframe) {
    if (tf === chartTf) return
    writeTf(tf)
    setChartTf(tf)
  }

  const severed = Boolean(kill?.engaged)
  const health = market?.health.status ?? 'unknown'
  const live = health === 'live' && !severed
  const regimes = TF_ORDER.map((tf) => market?.snapshot.timeframes[tf]).filter(
    (state): state is TimeframeState => Boolean(state),
  )
  const displayed = chartCandles ?? market?.candles ?? []
  const last = displayed.at(-1)
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
      n: block.probability?.sample_count ?? block.sample_count ?? null,
      mae: block.drift20?.mae ?? null,
      rmse: block.drift20?.rmse ?? null,
      brier: block.probability?.brier ?? null,
      ece: block.probability?.ece ?? null,
      coverage: block.interval?.coverage ?? null,
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
              ? `LIVE · $${market?.last_price.toFixed(2) ?? ''} · ${market?.source ?? 'binance-vision'}`
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
            {last && displayed[0] && (
              <span className={last.close >= displayed[0].close ? 'bullish' : 'negative'}>
                {chartTf === '15m' || chartTf === '5m' ? chartTf : chartTf.toUpperCase()}
              </span>
            )}
            <span className="muted">
              {market?.source ?? ''}
              {market?.price_source === 'ticker' ? ' · last trade' : ''}
            </span>
            <TimeframeSwitcher value={chartTf} onChange={selectTf} />
          </div>
          {loading && <p className="pad muted">Loading market state…</p>}
          {error && <p className="pad killError">{error}</p>}
          {displayed.length > 0 && <MarketChart candles={displayed} className="chart" />}
          {displayed.length > 0 && (
            <ContextOverlays
              zones={overlayZones}
              priceMin={Math.min(...displayed.map((c) => c.low))}
              priceMax={Math.max(...displayed.map((c) => c.high))}
              aria-label="Structural zones from the Context Engine snapshot"
            />
          )}
        </div>
        <aside className="rail">
          <section className="card">
            <h2>Regime stack</h2>
            {regimes.map((state) => (
              <button
                type="button"
                className={`row tfRow ${chartTf === state.timeframe ? 'selected' : ''}`}
                key={state.timeframe}
                onClick={() => isChartTimeframe(state.timeframe) && selectTf(state.timeframe)}
                aria-pressed={chartTf === state.timeframe}
              >
                <span>{state.timeframe === '15m' || state.timeframe === '5m' ? state.timeframe : state.timeframe.toUpperCase()}</span>
                <b className={state.regime}>{state.regime}</b>
              </button>
            ))}
            <p className="muted">{market?.interpretation || 'Waiting for snapshot.'}</p>
          </section>
          <section className="card">
            <h2>Forecast · next 10</h2>
            <p className="muted">
              {severed
                ? 'Harness degraded. Journaled forecast stays as written; no new loop will run.'
                : market?.forecast.forecast.notes || 'No journaled forecast yet.'}
            </p>
            {market && (
              <ForecastFan
                horizons={market.forecast.forecast.horizons}
                originClose={market.last_price}
                symbol={market.symbol}
                forecastedAt={market.as_of}
                health={
                  !market.forecast.journaled
                    ? 'unknown'
                    : market.forecast.forecast.horizons.some(
                          (row) =>
                            typeof row.q10_cum_return === 'number' ||
                            typeof row.q10_cum_log_return === 'number',
                        )
                      ? 'valid'
                      : 'degraded'
                }
                emptyReason="Quantile envelope is not drawn until q10/q50/q90 are journaled. A drift20 point path is not a distribution."
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
              coverageInterval="q10–q90 residual vs drift20"
            />
          </section>
          <section className="card">
            <h2>Thesis</h2>
            {(market?.snapshot.theses ?? []).length === 0 && (
              <p className="muted">{market?.interpretation || 'No competing theses at this as_of.'}</p>
            )}
            {(market?.snapshot.theses ?? []).map((thesis) => (
              <div className={`thesis ${thesis.direction === 'bear' ? 'bear' : 'bull'}`} key={thesis.id}>
                <b>
                  {thesis.timeframe} {thesis.direction} · {thesis.status}
                </b>
                <p>
                  {thesis.kind} · {thesis.regime_relation ?? 'unknown'} · {thesis.note}
                </p>
                {(thesis.invalidation_rules ?? []).map((rule) => (
                  <p key={rule.id}>
                    Invalidation ({rule.timeframe}): {rule.kind} {rule.price.toFixed(3)} — frozen at open
                  </p>
                ))}
              </div>
            ))}
          </section>
          {market && (
            <ContextEvidence
              analogs={market.snapshot.analogs ?? []}
              patterns={market.snapshot.pattern_hypotheses ?? []}
              fibLevels={market.snapshot.fib_levels ?? []}
            />
          )}
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
