import { useEffect, useMemo, useState } from 'react'
import { MarketChart } from './components/MarketChart'
import { AgentKillSwitch } from './components/AgentKillSwitch'
import { ForecastFan } from './components/ForecastFan'
import { ContextOverlays, type OverlayEvent, type OverlayZone } from './components/ContextOverlays'
import { ContextEvidence } from './components/ContextEvidence'
import { AccuracyPanel } from './components/AccuracyPanel'
import { LoopTraceCard } from './components/LoopTraceCard'
import { ShadowJournalCard } from './components/ShadowJournalCard'
import { fetchKillSwitch, type KillSwitchState } from './api/killSwitch'
import { fetchSystem, type SystemPayload } from './api/health'
import { drainShadowJournal, fetchForecastMetrics, fetchMarket } from './api/market'
import type { MarketPayload, SwingPivot, TimeframeState } from './api/types'
import { accuracySlicesFromMarket } from './accuracy/fromMarket'
import { DestNav } from './nav/DestNav'
import {
  buildHref,
  destRoute,
  hrefNeedsCanonicalize,
  parseLocation,
  type ChartTf,
  type DestId,
  type RouteState,
  type SheetPanel,
  CHART_TFS,
  SHEET_LABELS,
  SHEET_PANELS,
  TF_MINUTES,
} from './nav/destinations'
import { AccuracyView } from './views/AccuracyView'
import { HealthView } from './views/HealthView'
import { MoreView } from './views/MoreView'
import './styles.css'

const TF_ORDER = ['1w', '1d', '4h', '1h', '15m', '5m']

function readRoute(): RouteState {
  return parseLocation(window.location.pathname, window.location.search)
}

export default function App() {
  const [route, setRoute] = useState<RouteState>(() => readRoute())
  const [kill, setKill] = useState<KillSwitchState | null>(null)
  const [killError, setKillError] = useState<string | null>(null)
  const [market, setMarket] = useState<MarketPayload | null>(null)
  const [system, setSystem] = useState<SystemPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [draining, setDraining] = useState(false)
  const [drainError, setDrainError] = useState<string | null>(null)

  function applyRoute(next: RouteState, mode: 'push' | 'replace') {
    const href = buildHref(next)
    if (mode === 'replace') window.history.replaceState({}, '', href)
    else window.history.pushState({}, '', href)
    setRoute(next)
  }

  useEffect(() => {
    const canon = hrefNeedsCanonicalize(window.location.pathname, window.location.search)
    if (canon) {
      window.history.replaceState({}, '', canon)
      setRoute(readRoute())
    }
  }, [])

  useEffect(() => {
    const onPop = () => setRoute(readRoute())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  useEffect(() => {
    fetchKillSwitch()
      .then(setKill)
      .catch((err: unknown) => setKillError(err instanceof Error ? err.message : 'kill switch unreachable'))
  }, [])

  const needsMarket = route.dest === 'market' || route.dest === 'replay' || route.dest === 'accuracy'
  const fetchAsOf = route.dest === 'replay' ? route.asOf : null

  useEffect(() => {
    if (!needsMarket) {
      setLoading(false)
      return
    }
    if (route.dest === 'replay' && !fetchAsOf) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    fetchMarket(route.symbol, fetchAsOf)
      .then(setMarket)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'market unavailable'))
      .finally(() => setLoading(false))
  }, [needsMarket, route.dest, route.symbol, fetchAsOf])

  useEffect(() => {
    if (route.dest !== 'market' || fetchAsOf) return
    if (market?.source !== 'binance-vision') return
    const id = window.setInterval(() => {
      fetchMarket(route.symbol, null)
        .then(setMarket)
        .catch((err: unknown) => setError(err instanceof Error ? err.message : 'market unavailable'))
    }, 20_000)
    return () => window.clearInterval(id)
  }, [route.dest, route.symbol, fetchAsOf, market?.source])

  useEffect(() => {
    if (route.dest !== 'accuracy') return
    fetchForecastMetrics(route.symbol, fetchAsOf, true)
      .then((metrics) => {
        setMarket((prev) => (prev ? { ...prev, metrics } : prev))
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'metrics unavailable'))
  }, [route.dest, route.symbol, fetchAsOf])

  useEffect(() => {
    if (route.dest !== 'more') return
    fetchSystem()
      .then(setSystem)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'system unavailable'))
  }, [route.dest])

  useEffect(() => {
    if (route.dest !== 'replay' || route.asOf) return
    const hint = market?.replay_hint_as_of
    if (!hint) return
    const next = { ...route, asOf: hint }
    window.history.replaceState({}, '', buildHref(next))
    setRoute(next)
  }, [route.dest, route.asOf, route.symbol, route.panel, market?.replay_hint_as_of])

  const severed = Boolean(kill?.engaged)
  const health = market?.health.status ?? 'unknown'
  const live = health === 'live' && !severed
  const shadow = market?.forecast.shadow_journal
  const journalGap = shadow && shadow.remaining > 0 ? shadow.remaining : null
  const regimes = TF_ORDER.map((tf) => market?.snapshot.timeframes[tf]).filter(
    (state): state is TimeframeState => Boolean(state),
  )
  const chartSeries = useMemo(() => {
    if (!market) return []
    const rows = market.chart_candles?.[route.tf]
    return rows && rows.length > 0 ? rows : market.candles
  }, [market, route.tf])
  const tfStep = TF_MINUTES[route.tf] * 60
  const overlayZones = useMemo(() => {
    if (!market) return []
    const zones: OverlayZone[] = []
    const byId = new Map<string, OverlayZone>()
    for (const tf of TF_ORDER) {
      const state = market.snapshot.timeframes[tf]
      if (!state) continue
      for (const zone of [...(state.support_zones ?? []), ...(state.resistance_zones ?? [])]) {
        const existing = byId.get(zone.id)
        if (existing) {
          const tfs = [...(existing.timeframes ?? [])]
          if (!tfs.includes(state.timeframe)) {
            existing.timeframes = [...tfs, state.timeframe]
          }
          continue
        }
        const row: OverlayZone = {
          id: zone.id,
          lower: zone.lower,
          upper: zone.upper,
          role: zone.role,
          strength: zone.strength,
          test_count: zone.test_count,
          status: zone.status,
          known_at: zone.known_at,
          timeframes: [state.timeframe],
          provenance: {
            status: zone.status,
            notes: zone.interaction
              ? `${zone.interaction}${zone.outcome ? ` · ${zone.outcome}` : ''}. Not confidence.`
              : 'Zone lifecycle from closed bars only. Not confidence.',
          },
        }
        byId.set(zone.id, row)
        zones.push(row)
      }
    }
    return zones
  }, [market])
  const chartPivots: SwingPivot[] = useMemo(() => {
    if (!market) return []
    const selectedMins = TF_MINUTES[route.tf]
    const out: SwingPivot[] = []
    const seen = new Set<string>()
    for (const tf of TF_ORDER) {
      const mins = TF_MINUTES[tf as ChartTf]
      if (!mins || mins < selectedMins) continue
      for (const pivot of market.snapshot.timeframes[tf]?.swing_pivots ?? []) {
        const snapped = Math.floor(pivot.time / tfStep) * tfStep
        const key = `${tf}:${snapped}:${pivot.kind}`
        if (seen.has(key)) continue
        seen.add(key)
        out.push({ ...pivot, time: snapped, timeframe: pivot.timeframe ?? tf })
      }
    }
    return out
  }, [market, route.tf, tfStep])
  const overlayEvents: OverlayEvent[] = useMemo(() => {
    if (!market) return []
    const out: OverlayEvent[] = []
    for (const tf of TF_ORDER) {
      const state = market.snapshot.timeframes[tf]
      if (!state) continue
      for (const zone of [...(state.support_zones ?? []), ...(state.resistance_zones ?? [])]) {
        const kind =
          zone.interaction === 'rejected' || zone.outcome === 'failed_breakout'
            ? 'failure'
            : zone.outcome === 'accepted_through'
              ? 'breakout'
              : null
        if (!kind) continue
        const raw = zone.last_test_at ?? zone.known_at
        if (!raw) continue
        const ms = Date.parse(raw)
        if (!Number.isFinite(ms)) continue
        const time = Math.floor(Math.floor(ms / 1000) / tfStep) * tfStep
        out.push({
          id: `${zone.id}:${kind}:${time}`,
          kind,
          price: (zone.lower + zone.upper) / 2,
          time,
          zone_id: zone.id,
          known_at: raw,
          provenance: {
            notes: `${tf} ${zone.interaction ?? 'event'} ${zone.outcome ?? ''}. Not confidence.`.trim(),
          },
        })
      }
    }
    return out
  }, [market, tfStep])
  const accuracySlices = useMemo(() => accuracySlicesFromMarket(market), [market])

  function goDest(dest: DestId) {
    applyRoute(destRoute(dest, route, market?.replay_hint_as_of ?? null), 'push')
  }

  async function drainJournal() {
    if (!market || market.replay || severed || draining) return
    setDraining(true)
    setDrainError(null)
    try {
      await drainShadowJournal(market.symbol)
      const next = await fetchMarket(market.symbol, fetchAsOf)
      setMarket(next)
    } catch (err: unknown) {
      setDrainError(err instanceof Error ? err.message : 'journal drain failed')
    } finally {
      setDraining(false)
    }
  }

  function selectSheet(next: SheetPanel) {
    applyRoute({ ...route, panel: next }, 'replace')
  }

  function selectTf(next: ChartTf) {
    applyRoute({ ...route, tf: next }, 'replace')
  }

  const showMarket = route.dest === 'market' || route.dest === 'replay'
  const sheet = route.panel

  return (
    <main className={`shell dest-${route.dest} ${severed ? 'severed' : ''}`}>
      <header className="topbar">
        <div>
          <span className="eyebrow">AVAX / USDT · main</span>
          <h1>Context Engine</h1>
        </div>
        <div className="topbarMeta">
          <div className={`health ${severed ? 'severedHealth' : live ? '' : 'staleHealth'}`}>
            <span className="dot" />
            {severed
              ? 'PREDICTIONS PAUSED · READ ONLY'
              : health === 'live'
                ? `LIVE · as of ${market?.as_of ?? ''}`
                : health === 'fixture'
                  ? `FIXTURE · as of ${market?.as_of ?? ''}`
                  : health === 'stale'
                    ? `STALE · as of ${market?.as_of ?? ''}`
                    : 'DATA UNAVAILABLE'}
            {!severed && journalGap != null ? ` · journal gap ${journalGap}` : ''}
          </div>
          <AgentKillSwitch state={kill} error={killError} onChange={setKill} />
        </div>
      </header>
      {severed && (
        <div className="banner" role="status">
          Prediction agents are paused. Last journaled forecast remains; no new forecast or loop is written until resume.
        </div>
      )}
      {route.dest === 'replay' && (
        <div className="banner replay" role="status">
          Replay at {market?.as_of ?? route.asOf ?? 'pending hint'}. Future candles after this timestamp are hidden.{' '}
          <button type="button" className="quiet" onClick={() => goDest('market')}>
            Exit replay
          </button>
        </div>
      )}
      <div className="destLayout">
        <DestNav route={route} onNavigate={goDest} journalGap={journalGap} />
        <div className="destBody">
          {route.dest === 'accuracy' && (
            <AccuracyView
              slices={accuracySlices}
              modelId={market?.forecast.forecast.model_id ?? 'baseline.drift20'}
              loading={loading}
              error={error}
              asOf={market?.as_of ?? null}
            />
          )}
          {route.dest === 'health' && <HealthView />}
          {route.dest === 'more' && (
            <MoreView system={system} shadow={shadow} loading={loading} error={error} />
          )}
          {showMarket && (
            <section className="workspace">
              <div className="chartPanel">
                <div className="chartHeader">
                  <strong>{market ? `$${market.last_price.toFixed(2)}` : '—'}</strong>
                  {chartSeries.length > 0 && (
                    <span className={chartSeries.at(-1)!.close >= chartSeries[0].close ? 'bullish' : 'negative'}>
                      {route.tf}
                    </span>
                  )}
                  <span className="muted">{market?.source ?? ''}</span>
                </div>
                <nav className="tfSwitch" aria-label="Chart timeframe">
                  {CHART_TFS.map((tf) => {
                    const state = market?.snapshot.timeframes[tf]
                    return (
                      <button
                        key={tf}
                        type="button"
                        className={state ? state.regime : undefined}
                        aria-pressed={route.tf === tf}
                        onClick={() => selectTf(tf)}
                      >
                        {tf}
                        {state ? ` ${state.regime}` : ''}
                      </button>
                    )
                  })}
                </nav>
                {loading && <p className="pad muted">Loading market state…</p>}
                {error && <p className="pad killError">{error}</p>}
                {market && chartSeries.length > 0 && (
                  <MarketChart
                    candles={chartSeries}
                    zones={overlayZones}
                    pivots={chartPivots}
                    events={overlayEvents}
                    className="chart"
                  />
                )}
                {market && chartSeries.length > 0 && (
                  <ContextOverlays
                    zones={overlayZones}
                    events={overlayEvents}
                    priceMin={Math.min(...chartSeries.map((c) => c.low))}
                    priceMax={Math.max(...chartSeries.map((c) => c.high))}
                    timeStart={chartSeries[0]?.time}
                    timeEnd={chartSeries.at(-1)?.time}
                    aria-label="Structural zones from the Context Engine snapshot"
                  />
                )}
              </div>
              <aside className="rail" data-active-sheet={sheet}>
                <nav className="sheetTabs" role="tablist" aria-label="Market analysis">
                  {SHEET_PANELS.map((id) => (
                    <button
                      key={id}
                      type="button"
                      className="sheetTab"
                      role="tab"
                      id={`sheet-tab-${id}`}
                      aria-selected={sheet === id}
                      aria-controls={`sheet-panel-${id}`}
                      onClick={() => selectSheet(id)}
                    >
                      {SHEET_LABELS[id]}
                      {id === 'journal' && journalGap != null && (
                        <span className="sheetBadge" aria-label={`${journalGap} remaining journal origins`}>
                          {journalGap}
                        </span>
                      )}
                    </button>
                  ))}
                </nav>
                <section className="card" data-sheet="context" id="sheet-panel-context" role="tabpanel" aria-labelledby="sheet-tab-context">
                  <h2>Regime stack</h2>
                  {regimes.map((state) => (
                    <button
                      type="button"
                      className="row rowTf"
                      key={state.timeframe}
                      aria-pressed={route.tf === state.timeframe}
                      onClick={() => selectTf(state.timeframe as ChartTf)}
                    >
                      <span>{state.timeframe}</span>
                      <b className={state.regime}>{state.regime}</b>
                    </button>
                  ))}
                  <p className="muted">{market?.interpretation || 'Waiting for snapshot.'}</p>
                </section>
                <section className="card" data-sheet="thesis" id="sheet-panel-thesis" role="tabpanel" aria-labelledby="sheet-tab-thesis">
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
                        {thesis.ledger === 'journaled' ? ' · ledger journaled' : ''}
                      </p>
                      {(thesis.invalidation_rules ?? []).map((rule) => (
                        <p key={rule.id}>
                          Invalidation ({rule.timeframe}): {rule.kind} {rule.price.toFixed(3)} — frozen at open
                        </p>
                      ))}
                    </div>
                  ))}
                </section>
                <section className="card" data-sheet="forecast" id="sheet-panel-forecast" role="tabpanel" aria-labelledby="sheet-tab-forecast">
                  <h2>Forecast · next 10</h2>
                  <p className="muted">
                    {severed
                      ? 'Predictions paused. Journaled forecast stays as written; no new forecast is written until resume.'
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
                <div className="sheetStack" data-sheet="forecast">
                  {market?.forecast.loop && <LoopTraceCard loop={market.forecast.loop} />}
                </div>
                <section className="card" data-sheet="forecast">
                  <h2>Walk-forward scores</h2>
                  <AccuracyPanel
                    slices={accuracySlices}
                    baselineName="drift20 vs zero"
                    baselineDeltaMetric="mae"
                    modelId={market?.forecast.forecast.model_id ?? 'baseline.drift20'}
                    coverageInterval="q10–q90 residual vs drift20"
                  />
                </section>
                <section className="card" data-sheet="context">
                  <h2>Zones</h2>
                  <p className="muted">
                    Lifecycle from closed bars on each timeframe. Bounds are frozen. Status is not confidence.
                  </p>
                  {overlayZones.length === 0 && <p className="muted">No tracked zones at this as_of.</p>}
                  {overlayZones.slice(0, 8).map((zone) => (
                    <div className="row analogRow" key={zone.id}>
                      <span>
                        {(zone.timeframes ?? []).join('/') || 'tf'} {zone.role}
                      </span>
                      <span className="muted">
                        {zone.lower.toFixed(3)}–{zone.upper.toFixed(3)} · {zone.status ?? 'active'}
                        {zone.provenance?.notes ? ` · ${zone.provenance.notes}` : ''}
                      </span>
                    </div>
                  ))}
                </section>
                <section className="card" data-sheet="context">
                  <h2>Swings</h2>
                  <p className="muted">
                    Confirmed window extrema (left/right 3). Price is the extreme, not a forecast. A marker
                    appears on the pane only when that open is in the visible 5m window.
                  </p>
                  {(market?.snapshot.timeframes['5m']?.swing_pivots ?? []).length === 0 && (
                    <p className="muted">No confirmed 5m swings at this as_of.</p>
                  )}
                  {[...(market?.snapshot.timeframes['5m']?.swing_pivots ?? [])].slice(-8).reverse().map((pivot) => (
                    <div className="row analogRow" key={`${pivot.kind}-${pivot.time}`}>
                      <span>
                        5m {pivot.kind} {pivot.price.toFixed(3)}
                      </span>
                      <span className="muted">known {pivot.known_at}</span>
                    </div>
                  ))}
                </section>
                <div className="sheetStack" data-sheet="context">
                  {market && (
                    <ContextEvidence
                      analogs={market.snapshot.analogs ?? []}
                      patterns={market.snapshot.pattern_hypotheses ?? []}
                      fibLevels={market.snapshot.fib_levels ?? []}
                    />
                  )}
                </div>
                <ShadowJournalCard
                  shadow={shadow}
                  replay={Boolean(market?.replay) || route.dest === 'replay'}
                  severed={severed}
                  draining={draining}
                  drainError={drainError}
                  onDrain={drainJournal}
                />
                <section className="card" data-sheet="journal">
                  <h2>Replay</h2>
                  <p className="muted">September 2026 failed-breakout process check: 4H must hold through the 5m bounce.</p>
                  {market?.replay_hint_as_of && route.dest !== 'replay' && (
                    <button type="button" className="ghost" onClick={() => goDest('replay')}>
                      Replay pre-bounce
                    </button>
                  )}
                </section>
              </aside>
            </section>
          )}
        </div>
      </div>
    </main>
  )
}
