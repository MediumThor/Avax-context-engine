import { useId, useMemo, useState, type CSSProperties } from 'react'
import type { ForecastHorizon } from '../api/types'

/**
 * Isolated next-10 5m forecast fan.
 *
 * Constitution: forecasts are distributions, not prophecies. This component
 * never draws one deterministic future candle path, never invents missing
 * quantiles or a disagreement score, and never presents model probabilities
 * as calibrated confidence or accuracy.
 */

export type ForecastHealth = 'valid' | 'degraded' | 'stale' | 'unknown'

export type HorizonIssue =
  | 'missing-horizon'
  | 'horizon-out-of-range'
  | 'duplicate-horizon'
  | 'missing-quantile'
  | 'crossed-quantiles'
  | 'non-finite-expected'
  | 'non-finite-probability'
  | 'probability-out-of-range'

export interface ForecastFanDisagreement {
  /** Caller-supplied presence label. Never computed here. */
  label: string
  /**
   * Optional visual-only envelope padding factor (>= 1) supplied by the caller
   * (for example from an Evaluation Engine disagreement treatment).
   * Quantile values are not rescaled.
   */
  envelopeWidenFactor?: number
  /** Optional provenance note. Not a score. */
  note?: string
}

export interface ForecastInnerQuantile {
  h: number
  q25_cum_return: number
  q75_cum_return: number
}

export interface InspectedHorizon {
  h: number
  status: 'ok' | 'rejected' | 'missing'
  issues: HorizonIssue[]
  source?: ForecastHorizon
  q10?: number
  q50?: number
  q90?: number
  expectedCumReturn?: number
  pCloseAboveOrigin?: number
}

export interface ForecastFanInspection {
  empty: boolean
  drawable: InspectedHorizon[]
  rejected: InspectedHorizon[]
  missing: InspectedHorizon[]
  slots: InspectedHorizon[]
  hasCrossedQuantiles: boolean
  hasMissingQuantiles: boolean
}

export interface ForecastFanProps {
  horizons?: ForecastHorizon[] | null
  innerQuantiles?: ForecastInnerQuantile[] | null
  disagreement?: ForecastFanDisagreement | null
  health?: ForecastHealth
  originClose?: number
  symbol?: string
  forecastedAt?: string
  emptyReason?: string
  error?: string | null
  className?: string
  calibrationRef?: string | null
}

const HORIZONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const
const VIEW_W = 360
const VIEW_H = 176
const PAD = { l: 46, r: 10, t: 12, b: 26 }

const palette = {
  bg: '#0d1118',
  border: '#1c2430',
  text: '#eef3f8',
  muted: '#8f9bad',
  dim: '#7f8997',
  line: '#242b36',
  median: '#d7e2ef',
  envelope: '#6ea0c7',
  hatch: '#6ea0c7',
  inner: '#9bb4c9',
  warn: '#f0c36a',
  danger: '#ff8b93',
  origin: '#94a0af',
  pick: '#1d2430',
  pickOn: '#243044',
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

export function quantileOrderOk(q10: number, q50: number, q90: number): boolean {
  return q10 <= q50 && q50 <= q90
}

export function inspectForecastHorizons(
  horizons: ForecastHorizon[] | null | undefined,
): ForecastFanInspection {
  const byH = new Map<number, ForecastHorizon[]>()
  for (const row of horizons ?? []) {
    if (!row || !isFiniteNumber(row.h)) continue
    const list = byH.get(row.h) ?? []
    list.push(row)
    byH.set(row.h, list)
  }

  const slots: InspectedHorizon[] = HORIZONS.map((h) => {
    const copies = byH.get(h) ?? []
    if (copies.length === 0) {
      return { h, status: 'missing', issues: ['missing-horizon'] }
    }

    const issues: HorizonIssue[] = []
    if (h < 1 || h > 10 || !Number.isInteger(h)) issues.push('horizon-out-of-range')
    if (copies.length > 1) issues.push('duplicate-horizon')

    const source = copies[0]
    const q10 = source.q10_cum_return
    const q50 = source.q50_cum_return
    const q90 = source.q90_cum_return
    const expected = source.expected_cum_return
    const p = source.p_close_above_origin

    if (!isFiniteNumber(q10) || !isFiniteNumber(q50) || !isFiniteNumber(q90)) {
      issues.push('missing-quantile')
    } else if (!quantileOrderOk(q10, q50, q90)) {
      issues.push('crossed-quantiles')
    }

    if (!isFiniteNumber(expected)) issues.push('non-finite-expected')
    if (!isFiniteNumber(p)) issues.push('non-finite-probability')
    else if (p < 0 || p > 1) issues.push('probability-out-of-range')

    const blocking = issues.some((issue) =>
      issue === 'missing-quantile' ||
      issue === 'crossed-quantiles' ||
      issue === 'horizon-out-of-range' ||
      issue === 'duplicate-horizon',
    )

    return {
      h,
      status: blocking ? 'rejected' : 'ok',
      issues,
      source,
      q10: isFiniteNumber(q10) ? q10 : undefined,
      q50: isFiniteNumber(q50) ? q50 : undefined,
      q90: isFiniteNumber(q90) ? q90 : undefined,
      expectedCumReturn: isFiniteNumber(expected) ? expected : undefined,
      pCloseAboveOrigin: isFiniteNumber(p) ? p : undefined,
    }
  })

  const extra = [...byH.keys()].filter((h) => !HORIZONS.includes(h as (typeof HORIZONS)[number]))
  for (const h of extra.sort((a, b) => a - b)) {
    slots.push({
      h,
      status: 'rejected',
      issues: ['horizon-out-of-range'],
      source: byH.get(h)?.[0],
    })
  }

  const drawable = slots.filter((row) => row.status === 'ok')
  const rejected = slots.filter((row) => row.status === 'rejected')
  const missing = slots.filter((row) => row.status === 'missing')

  return {
    empty: !horizons || horizons.length === 0,
    drawable,
    rejected,
    missing,
    slots,
    hasCrossedQuantiles: slots.some((row) => row.issues.includes('crossed-quantiles')),
    hasMissingQuantiles: slots.some((row) => row.issues.includes('missing-quantile')),
  }
}

function formatReturn(value: number | undefined): string {
  if (!isFiniteNumber(value)) return '—'
  const pct = value * 100
  if (pct === 0) return '0.00%'
  const digits = Math.abs(pct) < 0.01 ? 3 : 2
  return `${pct < 0 ? '−' : '+'}${Math.abs(pct).toFixed(digits)}%`
}

function formatProb(value: number | undefined, usable: boolean): string {
  if (!isFiniteNumber(value) || !usable) return '—'
  return value.toFixed(2)
}

function impliedPrice(originClose: number | undefined, ret: number | undefined): string {
  if (!isFiniteNumber(originClose) || originClose <= 0 || !isFiniteNumber(ret)) return '—'
  return (originClose * (1 + ret)).toFixed(4)
}

function yDomain(rows: InspectedHorizon[]): { min: number; max: number } {
  const values = rows.flatMap((row) => [row.q10, row.q50, row.q90]).filter(isFiniteNumber)
  if (values.length === 0) return { min: -0.01, max: 0.01 }
  let min = Math.min(0, ...values)
  let max = Math.max(0, ...values)
  if (min === max) {
    min -= 0.01
    max += 0.01
  }
  const pad = (max - min) * 0.12
  return { min: min - pad, max: max + pad }
}

function plotX(h: number): number {
  const width = VIEW_W - PAD.l - PAD.r
  return PAD.l + (h / 10) * width
}

function plotY(value: number, min: number, max: number): number {
  const height = VIEW_H - PAD.t - PAD.b
  return PAD.t + ((max - value) / (max - min)) * height
}

interface BandPoint {
  h: number
  q10: number
  q50: number
  q90: number
  q25?: number
  q75?: number
}

function contiguousRuns(points: BandPoint[]): BandPoint[][] {
  const runs: BandPoint[][] = []
  let current: BandPoint[] = []
  for (const point of points) {
    const prev = current[current.length - 1]
    if (!prev || point.h === prev.h + 1) current.push(point)
    else {
      runs.push(current)
      current = [point]
    }
  }
  if (current.length) runs.push(current)
  return runs
}

function envelopePath(run: BandPoint[], min: number, max: number): string {
  const top = run.map((p) => `${plotX(p.h).toFixed(2)},${plotY(p.q90, min, max).toFixed(2)}`)
  const bottom = [...run].reverse().map((p) => `${plotX(p.h).toFixed(2)},${plotY(p.q10, min, max).toFixed(2)}`)
  return `M${top.join(' L')} L${bottom.join(' L')} Z`
}

function medianPath(run: BandPoint[], min: number, max: number): string {
  return run.map((p, i) => `${i === 0 ? 'M' : 'L'}${plotX(p.h).toFixed(2)},${plotY(p.q50, min, max).toFixed(2)}`).join(' ')
}

function innerEnvelopePath(run: BandPoint[], min: number, max: number): string | null {
  const usable = run.filter((p) => isFiniteNumber(p.q25) && isFiniteNumber(p.q75))
  if (usable.length < 2) return null
  const top = usable.map((p) => `${plotX(p.h).toFixed(2)},${plotY(p.q75 as number, min, max).toFixed(2)}`)
  const bottom = [...usable].reverse().map((p) => `${plotX(p.h).toFixed(2)},${plotY(p.q25 as number, min, max).toFixed(2)}`)
  return `M${top.join(' L')} L${bottom.join(' L')} Z`
}

function issueLabel(issue: HorizonIssue): string {
  switch (issue) {
    case 'missing-horizon':
      return 'no journaled horizon'
    case 'horizon-out-of-range':
      return 'h outside 1–10'
    case 'duplicate-horizon':
      return 'duplicate h rejected'
    case 'missing-quantile':
      return 'missing q10/q50/q90'
    case 'crossed-quantiles':
      return 'q10 ≤ q50 ≤ q90 violated'
    case 'non-finite-expected':
      return 'expected return unusable'
    case 'non-finite-probability':
      return 'P(close>origin) unusable'
    case 'probability-out-of-range':
      return 'P(close>origin) not in [0, 1]'
  }
}

function healthCopy(health: ForecastHealth): string {
  switch (health) {
    case 'valid':
      return 'Forecast health valid. Bands are model output, not a certainty path.'
    case 'degraded':
      return 'Forecast health degraded. Treat remaining bands as incomplete.'
    case 'stale':
      return 'Forecast health stale. Do not read this as a live update.'
    case 'unknown':
      return 'Forecast health unknown. No completeness claim.'
  }
}

const rootStyle: CSSProperties = {
  background: palette.bg,
  border: `1px solid ${palette.border}`,
  borderRadius: 14,
  padding: 12,
  color: palette.text,
  fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
  minWidth: 0,
}

const eyebrowStyle: CSSProperties = {
  color: palette.muted,
  fontSize: 11,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  margin: 0,
}

const bannerStyle = (tone: 'warn' | 'danger' | 'info'): CSSProperties => ({
  margin: '8px 0 0',
  padding: '8px 10px',
  borderRadius: 8,
  fontSize: 13,
  lineHeight: 1.35,
  border: `1px solid ${tone === 'danger' ? '#7a2430' : tone === 'warn' ? '#5a4a22' : palette.border}`,
  background: tone === 'danger' ? '#1a0d10' : tone === 'warn' ? '#1a160c' : '#10151d',
  color: tone === 'danger' ? palette.danger : tone === 'warn' ? palette.warn : palette.text,
})

export function ForecastFan({
  horizons,
  innerQuantiles,
  disagreement,
  health = 'unknown',
  originClose,
  symbol,
  forecastedAt,
  emptyReason,
  error,
  className,
  calibrationRef,
}: ForecastFanProps) {
  const uid = useId()
  const titleId = `${uid}-title`
  const svgTitleId = `${uid}-svg`
  const hatchId = `${uid}-hatch`
  const innerHatchId = `${uid}-inner`

  const inspection = useMemo(() => inspectForecastHorizons(horizons), [horizons])
  const innerByH = useMemo(() => {
    const map = new Map<number, ForecastInnerQuantile>()
    for (const row of innerQuantiles ?? []) {
      if (!row || !HORIZONS.includes(row.h as (typeof HORIZONS)[number])) continue
      if (!isFiniteNumber(row.q25_cum_return) || !isFiniteNumber(row.q75_cum_return)) continue
      map.set(row.h, row)
    }
    return map
  }, [innerQuantiles])

  const firstOk = inspection.drawable[0]?.h ?? null
  const [selected, setSelected] = useState<number | null>(null)
  const activeH = selected ?? firstOk

  const selectedRow = inspection.slots.find((row) => row.h === activeH) ?? inspection.drawable[0] ?? null
  const extraHorizons = inspection.slots.filter((row) => row.h < 1 || row.h > 10)
  const domain = yDomain(inspection.drawable)
  const dimmed = health === 'stale' || health === 'degraded'

  const points: BandPoint[] = useMemo(() => {
    const rows: BandPoint[] = []
    const originNeeded = inspection.drawable.some((row) => row.h === 1)
    if (originNeeded) rows.push({ h: 0, q10: 0, q50: 0, q90: 0, q25: 0, q75: 0 })
    for (const row of inspection.drawable) {
      const inner = innerByH.get(row.h)
      let q25: number | undefined
      let q75: number | undefined
      if (
        inner &&
        isFiniteNumber(row.q10) &&
        isFiniteNumber(row.q50) &&
        isFiniteNumber(row.q90) &&
        row.q10 <= inner.q25_cum_return &&
        inner.q25_cum_return <= row.q50 &&
        row.q50 <= inner.q75_cum_return &&
        inner.q75_cum_return <= row.q90
      ) {
        q25 = inner.q25_cum_return
        q75 = inner.q75_cum_return
      }
      rows.push({
        h: row.h,
        q10: row.q10 as number,
        q50: row.q50 as number,
        q90: row.q90 as number,
        q25,
        q75,
      })
    }
    return rows
  }, [inspection.drawable, innerByH])

  const runs = useMemo(() => contiguousRuns(points), [points])
  const isolated = runs.filter((run) => run.length === 1 && run[0].h !== 0)
  const connected = runs.filter((run) => run.length >= 2)

  const innerRejected = (innerQuantiles ?? []).filter((row) => {
    const host = inspection.drawable.find((item) => item.h === row.h)
    if (!host || !isFiniteNumber(host.q10) || !isFiniteNumber(host.q50) || !isFiniteNumber(host.q90)) return true
    if (!isFiniteNumber(row.q25_cum_return) || !isFiniteNumber(row.q75_cum_return)) return true
    return !(
      host.q10 <= row.q25_cum_return &&
      row.q25_cum_return <= host.q50 &&
      host.q50 <= row.q75_cum_return &&
      row.q75_cum_return <= host.q90
    )
  })

  const widenFactor =
    disagreement && isFiniteNumber(disagreement.envelopeWidenFactor) && disagreement.envelopeWidenFactor > 1
      ? disagreement.envelopeWidenFactor
      : null
  const widenPx = widenFactor ? Math.min(22, (widenFactor - 1) * 10) : 0

  const ticks = [domain.max, (domain.min + domain.max) / 2, domain.min]
  const ready = inspection.drawable.length > 0
  const state = error && !ready ? 'error' : inspection.empty ? 'empty' : ready ? 'ready' : 'invalid'

  const selectedProbUsable =
    !!selectedRow &&
    !selectedRow.issues.includes('non-finite-probability') &&
    !selectedRow.issues.includes('probability-out-of-range')

  return (
    <section
      className={className}
      style={rootStyle}
      aria-labelledby={titleId}
      data-testid="forecast-fan"
      data-state={state}
      data-health={health}
      data-has-crossed={inspection.hasCrossedQuantiles ? 'true' : 'false'}
    >
      <header style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'flex-start' }}>
        <div>
          <p style={eyebrowStyle}>{symbol ? `${symbol} · next 10 × 5m` : 'Forecast · next 10 × 5m'}</p>
          <h2 id={titleId} style={{ margin: '2px 0 0', fontSize: 16 }}>
            Forecast fan
          </h2>
        </div>
        <span
          style={{
            ...eyebrowStyle,
            border: `1px solid ${health === 'valid' ? '#1e3a32' : '#3a2a12'}`,
            padding: '6px 8px',
            borderRadius: 8,
            color: health === 'valid' ? palette.muted : palette.warn,
          }}
        >
          health {health}
        </span>
      </header>

      <p style={{ margin: '8px 0 0', color: palette.dim, fontSize: 13, lineHeight: 1.4 }}>
        q10–q90 envelope and q50 median path. This is a distribution, not one future candle path.
        {forecastedAt ? ` Forecasted at ${forecastedAt}.` : ''}
      </p>

      <p style={{ margin: '6px 0 0', color: palette.dim, fontSize: 12, lineHeight: 1.4 }}>
        {healthCopy(health)}
        {calibrationRef
          ? ` Probability field uses calibration ref ${calibrationRef}.`
          : ' P(close > origin) is the raw model field — not a calibrated confidence and not accuracy.'}
      </p>

      {error && (
        <p role="alert" style={bannerStyle('danger')}>
          {error}
        </p>
      )}

      {state === 'empty' && (
        <p role="status" style={bannerStyle('info')}>
          {emptyReason ?? 'No journaled forecast horizons available. No envelope is drawn.'}
        </p>
      )}

      {state === 'invalid' && (
        <p role="status" style={bannerStyle('warn')}>
          Horizons were provided, but none have a usable q10 ≤ q50 ≤ q90 set. No fan is drawn.
        </p>
      )}

      {inspection.hasCrossedQuantiles && (
        <p role="status" style={bannerStyle('warn')}>
          Crossed quantiles rejected. Required order is q10 ≤ q50 ≤ q90. Those horizons are labeled, not drawn as a valid band.
        </p>
      )}

      {inspection.hasMissingQuantiles && (
        <p role="status" style={bannerStyle('warn')}>
          Missing or non-finite q10/q50/q90 values. Gaps are left empty; no quantile is interpolated.
        </p>
      )}

      {extraHorizons.length > 0 && (
        <p role="status" style={bannerStyle('warn')}>
          Horizons outside 1–10 were rejected: {extraHorizons.map((row) => row.h).join(', ')}.
        </p>
      )}

      {innerRejected.length > 0 && (
        <p role="status" style={bannerStyle('warn')}>
          Inner q25–q75 omitted where missing or unordered (q10 ≤ q25 ≤ q50 ≤ q75 ≤ q90 required). No inner band was invented.
        </p>
      )}

      {disagreement && (
        <p role="status" style={bannerStyle('info')} data-testid="forecast-fan-disagreement">
          Disagreement reported by caller: {disagreement.label}
          {disagreement.note ? ` ${disagreement.note}` : ''}
          {widenFactor
            ? ` Visual envelope padding uses supplied factor ${widenFactor}; quantile values are unchanged.`
            : ' No disagreement score is computed here.'}
        </p>
      )}

      {ready && (
        <figure style={{ margin: '10px 0 0', opacity: dimmed ? 0.62 : 1 }}>
          <svg
            viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
            width="100%"
            role="img"
            aria-labelledby={svgTitleId}
            style={{ display: 'block', minHeight: 168 }}
          >
            <title id={svgTitleId}>
              Probabilistic forecast envelope for 5-minute horizons +1 to +10. Translucent q10 to q90
              band with q50 median. Not a single future path.
            </title>
            <defs>
              <pattern id={hatchId} width="6" height="6" patternUnits="userSpaceOnUse">
                <path d="M0 6 L6 0" stroke={palette.hatch} strokeWidth="0.8" opacity="0.55" />
              </pattern>
              <pattern id={innerHatchId} width="4" height="4" patternUnits="userSpaceOnUse">
                <path d="M0 4 L4 0" stroke={palette.inner} strokeWidth="0.7" opacity="0.7" />
              </pattern>
            </defs>
            {ticks.map((tick, index) => (
              <g key={`tick-${index}`}>
                <line
                  x1={PAD.l}
                  x2={VIEW_W - PAD.r}
                  y1={plotY(tick, domain.min, domain.max)}
                  y2={plotY(tick, domain.min, domain.max)}
                  stroke={palette.line}
                />
                <text
                  x={PAD.l - 6}
                  y={plotY(tick, domain.min, domain.max) + 3}
                  textAnchor="end"
                  fill={palette.muted}
                  fontSize="9"
                >
                  {formatReturn(tick)}
                </text>
              </g>
            ))}
            {HORIZONS.map((h) => (
              <text key={`x-${h}`} x={plotX(h)} y={VIEW_H - 8} textAnchor="middle" fill={palette.muted} fontSize="9">
                +{h}
              </text>
            ))}
            <line
              x1={PAD.l}
              x2={VIEW_W - PAD.r}
              y1={plotY(0, domain.min, domain.max)}
              y2={plotY(0, domain.min, domain.max)}
              stroke={palette.origin}
              strokeDasharray="3 3"
            />
            {connected.map((run, index) => (
              <g key={`run-${index}`}>
                {widenPx > 0 && (
                  <path
                    d={envelopePath(run, domain.min, domain.max)}
                    fill="none"
                    stroke={palette.warn}
                    strokeWidth={2 + widenPx}
                    opacity={0.28}
                  />
                )}
                <path
                  d={envelopePath(run, domain.min, domain.max)}
                  fill={`url(#${hatchId})`}
                  stroke={palette.envelope}
                  strokeWidth="1"
                  opacity="0.85"
                />
                {innerEnvelopePath(run, domain.min, domain.max) && (
                  <path
                    d={innerEnvelopePath(run, domain.min, domain.max) ?? undefined}
                    fill={`url(#${innerHatchId})`}
                    stroke={palette.inner}
                    strokeWidth="1"
                    opacity="0.8"
                  />
                )}
                <path
                  d={medianPath(run, domain.min, domain.max)}
                  fill="none"
                  stroke={palette.median}
                  strokeWidth="2"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
              </g>
            ))}
            {isolated.map((run) => {
              const point = run[0]
              const x = plotX(point.h)
              return (
                <g key={`iso-${point.h}`}>
                  <line
                    x1={x}
                    x2={x}
                    y1={plotY(point.q90, domain.min, domain.max)}
                    y2={plotY(point.q10, domain.min, domain.max)}
                    stroke={palette.envelope}
                    strokeWidth="6"
                    opacity="0.35"
                  />
                  {isFiniteNumber(point.q25) && isFiniteNumber(point.q75) && (
                    <line
                      x1={x}
                      x2={x}
                      y1={plotY(point.q75, domain.min, domain.max)}
                      y2={plotY(point.q25, domain.min, domain.max)}
                      stroke={palette.inner}
                      strokeWidth="3"
                      opacity="0.9"
                    />
                  )}
                  <rect
                    x={x - 4}
                    y={plotY(point.q50, domain.min, domain.max) - 4}
                    width="8"
                    height="8"
                    fill={palette.median}
                  />
                </g>
              )
            })}
            {inspection.drawable.map((row) => {
              const x = plotX(row.h)
              const y = plotY(row.q50 as number, domain.min, domain.max)
              const active = activeH === row.h
              return (
                <g key={`pt-${row.h}`}>
                  <rect
                    x={x - 3.5}
                    y={y - 3.5}
                    width="7"
                    height="7"
                    fill={active ? palette.warn : palette.median}
                    stroke={palette.bg}
                    strokeWidth="1"
                  />
                  {isFiniteNumber(row.pCloseAboveOrigin) &&
                    !row.issues.includes('probability-out-of-range') && (
                      <text x={x} y={y - 8} textAnchor="middle" fill={palette.text} fontSize="8">
                        {row.pCloseAboveOrigin.toFixed(2)}
                      </text>
                    )}
                </g>
              )
            })}
          </svg>
          <figcaption style={{ color: palette.dim, fontSize: 12, marginTop: 6 }}>
            Hatched outer band = q10–q90. Dotted zero line = origin. Squares = q50 median. Numbers on
            the path are model P(close &gt; origin), not confidence. Isolated horizons are vertical
            intervals (no interpolation across gaps).
            {originClose
              ? ` Implied prices use simple return × origin ${originClose} and are not log-return conversions.`
              : ''}
          </figcaption>
        </figure>
      )}

      <div style={{ marginTop: 12 }}>
        <p style={eyebrowStyle} id={`${uid}-picker`}>
          Horizons +1 to +10
        </p>
        <div
          role="listbox"
          aria-labelledby={`${uid}-picker`}
          aria-activedescendant={activeH ? `${uid}-h-${activeH}` : undefined}
          onKeyDown={(event) => {
            const usable = inspection.drawable.map((row) => row.h)
            if (!usable.length) return
            const idx = Math.max(0, usable.indexOf(activeH ?? usable[0]))
            if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
              event.preventDefault()
              setSelected(usable[Math.min(usable.length - 1, idx + 1)])
            }
            if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
              event.preventDefault()
              setSelected(usable[Math.max(0, idx - 1)])
            }
          }}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(44px, 1fr))', gap: 6, marginTop: 8 }}
        >
          {HORIZONS.map((h) => {
            const row = inspection.slots.find((item) => item.h === h)
            const disabled = !row || row.status !== 'ok'
            const active = activeH === h
            return (
              <button
                key={h}
                id={`${uid}-h-${h}`}
                type="button"
                role="option"
                aria-selected={active}
                disabled={disabled}
                onClick={() => setSelected(h)}
                style={{
                  minHeight: 44,
                  minWidth: 44,
                  borderRadius: 8,
                  border: `1px solid ${active ? palette.warn : palette.border}`,
                  background: active ? palette.pickOn : palette.pick,
                  color: disabled ? palette.dim : palette.text,
                  fontWeight: 600,
                  cursor: disabled ? 'not-allowed' : 'pointer',
                }}
              >
                +{h}
                <span style={{ display: 'block', fontSize: 10, fontWeight: 500, color: palette.muted }}>
                  {row?.status === 'ok' ? formatReturn(row.q50) : row?.status === 'rejected' ? 'invalid' : 'missing'}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      <div
        style={{
          marginTop: 12,
          padding: 10,
          borderRadius: 8,
          background: '#10151d',
          border: `1px solid ${palette.border}`,
          fontSize: 13,
          lineHeight: 1.45,
        }}
        aria-live="polite"
      >
        {selectedRow ? (
          <>
            <strong>
              +{selectedRow.h} · {selectedRow.status === 'ok' ? 'usable quantiles' : selectedRow.status}
            </strong>
            <p style={{ margin: '6px 0 0', color: palette.text }}>
              q10 {formatReturn(selectedRow.q10)} · q50 {formatReturn(selectedRow.q50)} · q90{' '}
              {formatReturn(selectedRow.q90)}
            </p>
            <p style={{ margin: '4px 0 0', color: palette.muted }}>
              expected {formatReturn(selectedRow.expectedCumReturn)} · P(close &gt; origin){' '}
              {formatProb(selectedRow.pCloseAboveOrigin, selectedProbUsable)}
              {originClose && selectedRow.status === 'ok'
                ? ` · implied q50 price ${impliedPrice(originClose, selectedRow.q50)} (simple return)`
                : ''}
            </p>
            {selectedRow.status === 'ok' &&
              isFiniteNumber(selectedRow.q10) &&
              selectedRow.q10 === selectedRow.q90 && (
                <p style={{ margin: '4px 0 0', color: palette.warn }}>
                  Zero-width interval at this horizon (q10 = q50 = q90). That is the supplied
                  distribution, not a certain candle path.
                </p>
              )}
            {selectedRow.issues.length > 0 && (
              <p style={{ margin: '4px 0 0', color: palette.warn }}>
                {selectedRow.issues.map(issueLabel).join(' · ')}
              </p>
            )}
          </>
        ) : (
          <p style={{ margin: 0, color: palette.muted }}>No horizon selected. Values stay in the table below.</p>
        )}
      </div>

      <table
        style={{ width: '100%', borderCollapse: 'collapse', marginTop: 12, fontSize: 12 }}
        aria-label="Forecast quantiles by horizon"
      >
        <caption style={{ captionSide: 'top', textAlign: 'left', color: palette.muted, paddingBottom: 6 }}>
          Journaled cumulative returns by horizon. Empty cells are missing, not zero.
        </caption>
        <thead>
          <tr style={{ color: palette.muted, textAlign: 'left' }}>
            <th style={{ padding: '6px 4px' }}>h</th>
            <th style={{ padding: '6px 4px' }}>q10</th>
            <th style={{ padding: '6px 4px' }}>q50</th>
            <th style={{ padding: '6px 4px' }}>q90</th>
            <th style={{ padding: '6px 4px' }}>P&gt;origin</th>
            <th style={{ padding: '6px 4px' }}>status</th>
          </tr>
        </thead>
        <tbody>
          {HORIZONS.map((h) => {
            const row = inspection.slots.find((item) => item.h === h)
            const active = activeH === h
            return (
              <tr
                key={`row-${h}`}
                tabIndex={0}
                onClick={() => row?.status === 'ok' && setSelected(h)}
                onKeyDown={(event) => {
                  if ((event.key === 'Enter' || event.key === ' ') && row?.status === 'ok') {
                    event.preventDefault()
                    setSelected(h)
                  }
                }}
                style={{
                  background: active ? palette.pickOn : 'transparent',
                  borderTop: `1px solid ${palette.line}`,
                  cursor: row?.status === 'ok' ? 'pointer' : 'default',
                }}
              >
                <td style={{ padding: '10px 4px', minHeight: 44 }}>+{h}</td>
                <td style={{ padding: '10px 4px' }}>{formatReturn(row?.q10)}</td>
                <td style={{ padding: '10px 4px' }}>{formatReturn(row?.q50)}</td>
                <td style={{ padding: '10px 4px' }}>{formatReturn(row?.q90)}</td>
                <td style={{ padding: '10px 4px' }}>
                  {formatProb(
                    row?.pCloseAboveOrigin,
                    !!row &&
                      !row.issues.includes('non-finite-probability') &&
                      !row.issues.includes('probability-out-of-range'),
                  )}
                </td>
                <td style={{ padding: '10px 4px', color: row?.status === 'ok' ? palette.muted : palette.warn }}>
                  {row?.status === 'ok'
                    ? row.issues.length
                      ? row.issues.map(issueLabel).join(', ')
                      : 'ok'
                    : row?.issues.map(issueLabel).join(', ') ?? 'missing'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </section>
  )
}
