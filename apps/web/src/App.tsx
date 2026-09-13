import { useEffect, useMemo, useState } from 'react'
import { MarketChart } from './components/MarketChart'
import { AgentKillSwitch } from './components/AgentKillSwitch'
import { ForecastFan } from './components/ForecastFan'
import { ContextOverlays, type OverlayZone } from './components/ContextOverlays'
import { ContextEvidence } from './components/ContextEvidence'
import { AccuracyPanel, type AccuracySlice } from './components/AccuracyPanel'
import { LoopTraceCard } from './components/LoopTraceCard'
import { ShadowJournalCard } from './components/ShadowJournalCard'
import { fetchKillSwitch, type KillSwitchState } from './api/killSwitch'
import { drainShadowJournal, fetchMarket } from './api/market'
import type { MarketPayload, StructuralZone, TimeframeState } from './api/types'
import './styles.css'

const TF_ORDER = ['1w', '1d', '4h', '1h', '15m', '5m']
const SHEET_PANELS = ['context', 'forecast', 'thesis', 'journal'] as const
type SheetPanel = (typeof SHEET_PANELS)[number]
const SHEET_LABELS: Record<SheetPanel, string> = {
  context: 'Context',
  forecast: 'Forecast',
  thesis: 'Thesis',
  journal: 'Journal',
}

function readAsOf(): string | null {
  return new URLSearchParams(window.location.search).get('as_of')
}

function readSheet(): SheetPanel {
  const raw = new URLSearchParams(window.location.search).get('panel')
  return (SHEET_PANELS as readonly string[]).includes(raw ?? '') ? (raw as SheetPanel) : 'context'
}

export default function App() {
  const [kill, setKill] = useState<KillSwitchState | null>(null)
  const [killError, setKillError] = useState<string | null>(null)
  const [market, setMarket] = useState<MarketPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [sheet, setSheet] = useState<SheetPanel>(() => readSheet())
  const [draining, setDraining] = useState(false)
  const [drainError, setDrainError] = useState<string | null>(null)
  const asOf = useMemo(() => readAsOf(), [])

  useEffect(() => {
    fetchKillSwitch()
      .then(setKill)
      .catch((err: unknown) => setKillError(err instanceof Error ? err.message : 'kill switch unreachable'))
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchMarket('AVAXUSDT', asOf)
      .then(setMarket)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'market unavailable'))
      .finally(() => setLoading(false))
  }, [asOf])

  const severed = Boolean(kill?.engaged)
  const health = market?.health.status ?? 'unknown'
  const live = health === 'live' && !severed
  const shadow = market?.forecast.shadow_journal
  const journalGap = shadow && shadow.remaining > 0 ? shadow.remaining : null
  const regimes = TF_ORDER.map((tf) => market?.snapshot.timeframes[tf]).filter(
    (state): state is TimeframeState => Boolean(state),
  )
  const last = market?.candles.at(-1)
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

  async function drainJournal() {
    if (!market || market.replay || severed || draining) return
    setDraining(true)
    setDrainError(null)
    try {
      await drainShadowJournal(market.symbol)
      const next = await fetchMarket(market.symbol, asOf)
      setMarket(next)
    } catch (err: unknown) {
      setDrainError(err instanceof Error ? err.message : 'journal drain failed')
    } finally {
      setDraining(false)
    }
  }

  function selectSheet(next: SheetPanel) {
    setSheet(next)
    const url = new URL(window.location.href)
    if (next === 'context') url.searchParams.delete('panel')
    else url.searchParams.set('panel', next)
    window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`)
  }

  return (
    <main className={`shell ${severed ? 'severed' : ''}`}>
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
      {market?.replay && (
        <div className="banner replay" role="status">
          Replay at {market.as_of}. Future candles after this timestamp are hidden. <button type="button" className="quiet" onClick={exitReplay}>Exit replay</button>
        </div>
      )}
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
          <div className="regimeStrip" aria-label="Regime by timeframe">
            {regimes.map((state) => (
              <span className={`regimeChip ${state.regime}`} key={`strip-${state.timeframe}`}>
                {state.timeframe} {state.regime}
              </span>
            ))}
          </div>
          {loading && <p className="pad muted">Loading market state…</p>}
          {error && <p className="pad killError">{error}</p>}
          {market && <MarketChart candles={market.candles} zones={overlayZones} className="chart" />}
          {market && (
            <ContextOverlays
              zones={overlayZones}
              priceMin={Math.min(...market.candles.map((c) => c.low))}
              priceMax={Math.max(...market.candles.map((c) => c.high))}
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
              <div className="row" key={state.timeframe}>
                <span>{state.timeframe}</span>
                <b className={state.regime}>{state.regime}</b>
              </div>
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
            replay={Boolean(market?.replay)}
            severed={severed}
            draining={draining}
            drainError={drainError}
            onDrain={drainJournal}
          />
          <section className="card" data-sheet="journal">
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
