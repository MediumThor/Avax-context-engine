import { useId, useMemo, useState, type CSSProperties } from 'react'

/** Canonical forecast horizon h=1..10 (cumulative from forecast origin). */
export type AccuracyHorizon = number

/**
 * One evaluated slice. Every score field is explicit so callers cannot pass a
 * generic `accuracy` number. Use `null` when a metric has not been scored.
 * This component never invents ECE, Brier, coverage, or error values.
 */
export interface AccuracySlice {
  horizon: AccuracyHorizon
  n: number | null
  mae: number | null
  rmse: number | null
  brier: number | null
  ece: number | null
  coverage: number | null
  baseline_delta: number | null
  regime?: string | null
}

export interface AccuracyPanelProps {
  slices: AccuracySlice[]
  /** Inclusive evaluation window start (UTC). */
  windowStart?: string | null
  /** Inclusive evaluation window end (UTC). */
  windowEnd?: string | null
  /** Named baseline the delta is measured against (required for a defined comparison). */
  baselineName?: string | null
  /** Metric the supplied baseline_delta refers to (for example `brier` or `mae`). */
  baselineDeltaMetric?: string | null
  /** Evaluation-run / manifest identifier, if the caller has one. */
  runId?: string | null
  /** Model or ensemble identifier, if the caller has one. */
  modelId?: string | null
  /** Interval the coverage field measures. Default label is q10–q90. */
  coverageInterval?: string | null
  className?: string
}

const INSUFFICIENT = 'sample insufficient'
const NOT_SCORED = 'not yet scored'
const UNKNOWN = 'unknown'

const METRIC_ROWS = [
  {
    key: 'mae' as const,
    label: 'MAE (return error)',
    definition: 'Mean absolute error of cumulative log return versus the realized path at this horizon.',
  },
  {
    key: 'rmse' as const,
    label: 'RMSE (return error)',
    definition: 'Root mean squared error of cumulative log return at this horizon.',
  },
  {
    key: 'brier' as const,
    label: 'Brier score',
    definition: 'Mean squared error of the forecasted event probability (typically close-above-origin). Lower is better. This is not a percent-correct badge.',
  },
  {
    key: 'ece' as const,
    label: 'ECE (calibration)',
    definition: 'Expected calibration error from the evaluation run. Lower is better. Shown only when the caller supplies it.',
  },
  {
    key: 'coverage' as const,
    label: 'Interval coverage',
    definition: 'Empirical fraction of matured outcomes that fell inside the stated forecast interval (default q10–q90).',
  },
  {
    key: 'baseline_delta' as const,
    label: 'Baseline delta',
    definition: 'Caller-stated model minus baseline on the named metric. This panel does not infer which sign is an improvement.',
  },
] as const

const palette = {
  text: '#eef3f8',
  muted: '#9aa5b3',
  faint: '#7f8997',
  line: '#1c2430',
  card: '#0d1118',
  inset: '#0b0e14',
  warn: '#f0c36a',
  warnBg: '#241c0d',
  accent: '#8f9bad',
  focus: '#6ea8ff',
}

function isPresentNumber(value: number | null | undefined): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

function hasSufficientSample(n: number | null | undefined): n is number {
  return isPresentNumber(n) && n > 0
}

function formatPlainNumber(value: number, maxDigits = 4): string {
  return value.toLocaleString('en-US', {
    maximumFractionDigits: maxDigits,
    minimumFractionDigits: 0,
  })
}

/** Format a supplied score. Never converts a missing value into a percentage. */
export function formatAccuracyMetric(
  value: number | null | undefined,
  n: number | null | undefined,
  kind: 'score' | 'coverage' | 'signed' = 'score',
): string {
  if (!hasSufficientSample(n)) return INSUFFICIENT
  if (!isPresentNumber(value)) return NOT_SCORED
  if (kind === 'coverage') {
    if (value >= 0 && value <= 1) {
      return `${formatPlainNumber(value, 4)} empirical fraction`
    }
    return `${formatPlainNumber(value, 4)} (scale as supplied; not converted)`
  }
  if (kind === 'signed') {
    const body = formatPlainNumber(value, 4)
    return value > 0 ? `+${body}` : body
  }
  return formatPlainNumber(value, 4)
}

export function formatSampleCount(n: number | null | undefined): string {
  if (!isPresentNumber(n)) return INSUFFICIENT
  if (n <= 0) return INSUFFICIENT
  return `${n} matured outcome${n === 1 ? '' : 's'}`
}

export function formatHorizonLabel(horizon: number | null | undefined): string {
  if (!isPresentNumber(horizon)) return UNKNOWN
  return `+${horizon}`
}

function formatMeta(value: string | null | undefined): string {
  if (typeof value !== 'string') return UNKNOWN
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : UNKNOWN
}

function sliceKey(slice: AccuracySlice, index: number): string {
  const regime = slice.regime ?? 'unspecified'
  return `${slice.horizon}-${regime}-${index}`
}

export function AccuracyPanel({
  slices,
  windowStart = null,
  windowEnd = null,
  baselineName = null,
  baselineDeltaMetric = null,
  runId = null,
  modelId = null,
  coverageInterval = 'q10–q90',
  className,
}: AccuracyPanelProps) {
  const titleId = useId()
  const summaryId = useId()
  const defsId = useId()
  const [regimeFilter, setRegimeFilter] = useState<string>('all')
  const [horizonFilter, setHorizonFilter] = useState<string>('all')

  const regimes = useMemo(() => {
    const values = new Set<string>()
    for (const slice of slices) {
      if (typeof slice.regime === 'string' && slice.regime.trim()) values.add(slice.regime)
    }
    return Array.from(values)
  }, [slices])

  const horizons = useMemo(() => {
    const values = new Set<number>()
    for (const slice of slices) {
      if (isPresentNumber(slice.horizon)) values.add(slice.horizon)
    }
    return Array.from(values).sort((a, b) => a - b)
  }, [slices])

  const visible = useMemo(() => {
    return slices.filter((slice) => {
      const regimeOk =
        regimeFilter === 'all' ||
        (typeof slice.regime === 'string' && slice.regime === regimeFilter)
      const horizonOk =
        horizonFilter === 'all' ||
        (isPresentNumber(slice.horizon) && String(slice.horizon) === horizonFilter)
      return regimeOk && horizonOk
    })
  }, [slices, regimeFilter, horizonFilter])

  const windowLabel =
    formatMeta(windowStart) === UNKNOWN && formatMeta(windowEnd) === UNKNOWN
      ? UNKNOWN
      : `${formatMeta(windowStart)} → ${formatMeta(windowEnd)}`

  return (
    <section
      className={className}
      aria-labelledby={titleId}
      aria-describedby={`${summaryId} ${defsId}`}
      style={styles.section}
    >
      <style>{css}</style>
      <header style={styles.header}>
        <p style={styles.eyebrow}>Evaluation · calibration and error</p>
        <h2 id={titleId} style={styles.title}>
          Forecast scores by horizon and regime
        </h2>
        <p id={summaryId} style={styles.lead}>
          This is not a generic accuracy badge. Each row is one horizon
          {coverageInterval ? ` with ${coverageInterval} coverage` : ''}, sample
          count, return error, Brier, ECE, and a named baseline delta. Missing
          values stay {NOT_SCORED}. A zero or absent sample is {INSUFFICIENT}.
          Loop depth is process metadata and is not shown as quality.
        </p>
      </header>

      <dl style={styles.metaList}>
        <div style={styles.metaItem}>
          <dt style={styles.dt}>Evaluation window (UTC)</dt>
          <dd style={styles.dd}>{windowLabel}</dd>
        </div>
        <div style={styles.metaItem}>
          <dt style={styles.dt}>Baseline</dt>
          <dd style={styles.dd}>{formatMeta(baselineName)}</dd>
        </div>
        <div style={styles.metaItem}>
          <dt style={styles.dt}>Baseline delta metric</dt>
          <dd style={styles.dd}>{formatMeta(baselineDeltaMetric)}</dd>
        </div>
        <div style={styles.metaItem}>
          <dt style={styles.dt}>Model / ensemble</dt>
          <dd style={styles.dd}>{formatMeta(modelId)}</dd>
        </div>
        <div style={styles.metaItem}>
          <dt style={styles.dt}>Run / manifest</dt>
          <dd style={styles.dd}>{formatMeta(runId)}</dd>
        </div>
        <div style={styles.metaItem}>
          <dt style={styles.dt}>Coverage interval</dt>
          <dd style={styles.dd}>{formatMeta(coverageInterval)}</dd>
        </div>
      </dl>

      {slices.length > 0 && (
        <div style={styles.filters} role="group" aria-label="Filter scored slices">
          <div style={styles.filterBlock}>
            <p style={styles.filterLabel} id={`${titleId}-horizon-filter`}>
              Horizon
            </p>
            <div style={styles.chipRow} role="group" aria-labelledby={`${titleId}-horizon-filter`}>
              <FilterChip
                selected={horizonFilter === 'all'}
                onSelect={() => setHorizonFilter('all')}
                label="All horizons"
              />
              {horizons.map((h) => (
                <FilterChip
                  key={h}
                  selected={horizonFilter === String(h)}
                  onSelect={() => setHorizonFilter(String(h))}
                  label={formatHorizonLabel(h)}
                />
              ))}
            </div>
          </div>
          {regimes.length > 0 && (
            <div style={styles.filterBlock}>
              <p style={styles.filterLabel} id={`${titleId}-regime-filter`}>
                Regime slice
              </p>
              <div style={styles.chipRow} role="group" aria-labelledby={`${titleId}-regime-filter`}>
                <FilterChip
                  selected={regimeFilter === 'all'}
                  onSelect={() => setRegimeFilter('all')}
                  label="All regimes"
                />
                {regimes.map((regime) => (
                  <FilterChip
                    key={regime}
                    selected={regimeFilter === regime}
                    onSelect={() => setRegimeFilter(regime)}
                    label={regime}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {slices.length === 0 ? (
        <p role="status" style={styles.empty}>
          No evaluation slices were provided. Metrics are {NOT_SCORED}. This
          panel does not invent ECE, Brier, coverage, or return-error values.
        </p>
      ) : visible.length === 0 ? (
        <p role="status" style={styles.empty}>
          No slices match the current horizon/regime filter. Scores are not
          inferred for hidden slices.
        </p>
      ) : (
        <ol style={styles.sliceList}>
          {visible.map((slice, index) => (
            <SliceCard
              key={sliceKey(slice, index)}
              slice={slice}
              coverageInterval={formatMeta(coverageInterval)}
              baselineName={formatMeta(baselineName)}
              baselineDeltaMetric={formatMeta(baselineDeltaMetric)}
            />
          ))}
        </ol>
      )}

      <div id={defsId} style={styles.defs}>
        <h3 style={styles.defsTitle}>Metric definitions</h3>
        <ul style={styles.defsList}>
          {METRIC_ROWS.map((metric) => (
            <li key={metric.key} style={styles.defsItem}>
              <strong style={styles.defsName}>{metric.label}.</strong> {metric.definition}
            </li>
          ))}
          <li style={styles.defsItem}>
            <strong style={styles.defsName}>Sample count (n).</strong> Number of
            matured forecast/outcome pairs in this slice. Required before any
            score is shown.
          </li>
          <li style={styles.defsItem}>
            <strong style={styles.defsName}>Horizon.</strong> Machine horizon
            h=1..10, shown as +1..+10, cumulative from forecast origin unless a
            future contract names an individual-candle field.
          </li>
        </ul>
        <p style={styles.disclaimer}>
          Display only. This panel does not score live forecasts, does not
          promote a model, and does not claim production readiness. Subjective
          confidence percentages without a calibration source are prohibited.
        </p>
      </div>
    </section>
  )
}

function FilterChip({
  selected,
  onSelect,
  label,
}: {
  selected: boolean
  onSelect: () => void
  label: string
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onSelect}
      className="ace-accuracy-chip"
      style={{
        ...styles.chip,
        background: selected ? '#1d2430' : 'transparent',
        color: selected ? palette.text : palette.muted,
        borderColor: selected ? '#2a3340' : palette.line,
      }}
    >
      {label}
    </button>
  )
}

function SliceCard({
  slice,
  coverageInterval,
  baselineName,
  baselineDeltaMetric,
}: {
  slice: AccuracySlice
  coverageInterval: string
  baselineName: string
  baselineDeltaMetric: string
}) {
  const sufficient = hasSufficientSample(slice.n)
  const regimeLabel =
    typeof slice.regime === 'string' && slice.regime.trim()
      ? slice.regime
      : 'regime not specified'
  const horizonLabel = formatHorizonLabel(slice.horizon)
  const heading = `${horizonLabel} · ${regimeLabel}`

  return (
    <li style={styles.card}>
      <article aria-label={`Scores for horizon ${horizonLabel}, ${regimeLabel}`}>
        <header style={styles.cardHeader}>
          <h3 style={styles.cardTitle}>{heading}</h3>
          <p style={styles.cardMeta}>
            Horizon h={isPresentNumber(slice.horizon) ? slice.horizon : UNKNOWN} (cumulative).{' '}
            {sufficient
              ? formatSampleCount(slice.n)
              : INSUFFICIENT}
          </p>
        </header>
        {!sufficient && (
          <p role="status" style={styles.warn}>
            Sample is insufficient (n is 0 or absent). Numeric scores for this
            slice are withheld so a missing evaluation cannot appear as a
            percentage.
          </p>
        )}
        <dl style={styles.metricList}>
          {METRIC_ROWS.map((metric) => {
            const kind =
              metric.key === 'coverage'
                ? 'coverage'
                : metric.key === 'baseline_delta'
                  ? 'signed'
                  : 'score'
            const value = formatAccuracyMetric(slice[metric.key], slice.n, kind)
            const extra =
              metric.key === 'coverage'
                ? ` Interval: ${coverageInterval}.`
                : metric.key === 'baseline_delta'
                  ? ` Baseline: ${baselineName}. Metric: ${baselineDeltaMetric}.`
                  : ''
            return (
              <div key={metric.key} style={styles.metricRow}>
                <dt style={styles.metricDt}>
                  <span style={styles.metricLabel}>{metric.label}</span>
                  <span style={styles.metricDef}>
                    {metric.definition}
                    {extra}
                  </span>
                </dt>
                <dd style={styles.metricDd} data-scored={sufficient && isPresentNumber(slice[metric.key]) ? 'yes' : 'no'}>
                  {value}
                </dd>
              </div>
            )
          })}
        </dl>
      </article>
    </li>
  )
}

const styles: Record<string, CSSProperties> = {
  section: {
    background: palette.card,
    border: `1px solid ${palette.line}`,
    borderRadius: 14,
    padding: 14,
    color: palette.text,
    fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
    maxWidth: '100%',
  },
  header: {
    marginBottom: 12,
  },
  eyebrow: {
    margin: 0,
    color: palette.accent,
    fontSize: 12,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
  },
  title: {
    margin: '4px 0 8px',
    fontSize: 16,
    fontWeight: 650,
    lineHeight: 1.3,
  },
  lead: {
    margin: 0,
    color: palette.muted,
    fontSize: 13,
    lineHeight: 1.45,
  },
  metaList: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: 8,
    margin: '0 0 14px',
  },
  metaItem: {
    background: palette.inset,
    border: `1px solid ${palette.line}`,
    borderRadius: 9,
    padding: '10px 12px',
    margin: 0,
  },
  dt: {
    margin: 0,
    color: palette.faint,
    fontSize: 11,
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
  },
  dd: {
    margin: '4px 0 0',
    fontSize: 13,
    wordBreak: 'break-word',
  },
  filters: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
    marginBottom: 14,
  },
  filterBlock: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  filterLabel: {
    margin: 0,
    color: palette.faint,
    fontSize: 11,
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
  },
  chipRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    minHeight: 44,
    minWidth: 44,
    padding: '10px 14px',
    borderRadius: 8,
    border: '1px solid',
    fontWeight: 600,
    fontSize: 13,
    cursor: 'pointer',
  },
  empty: {
    margin: 0,
    padding: 12,
    borderRadius: 9,
    background: palette.warnBg,
    color: palette.warn,
    fontSize: 14,
    lineHeight: 1.45,
  },
  sliceList: {
    listStyle: 'none',
    margin: 0,
    padding: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  card: {
    background: palette.inset,
    border: `1px solid ${palette.line}`,
    borderRadius: 9,
    padding: 12,
  },
  cardHeader: {
    marginBottom: 8,
  },
  cardTitle: {
    margin: 0,
    fontSize: 15,
  },
  cardMeta: {
    margin: '4px 0 0',
    color: palette.muted,
    fontSize: 13,
  },
  warn: {
    margin: '0 0 10px',
    padding: '10px 12px',
    borderRadius: 8,
    background: palette.warnBg,
    color: palette.warn,
    fontSize: 13,
    lineHeight: 1.4,
  },
  metricList: {
    margin: 0,
    display: 'flex',
    flexDirection: 'column',
  },
  metricRow: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 12,
    padding: '10px 0',
    borderBottom: `1px solid #171d27`,
    alignItems: 'flex-start',
  },
  metricDt: {
    margin: 0,
    flex: '1 1 auto',
    minWidth: 0,
  },
  metricLabel: {
    display: 'block',
    fontSize: 13,
    fontWeight: 650,
  },
  metricDef: {
    display: 'block',
    marginTop: 4,
    color: palette.faint,
    fontSize: 12,
    lineHeight: 1.4,
  },
  metricDd: {
    margin: 0,
    flex: '0 0 auto',
    maxWidth: '42%',
    textAlign: 'right',
    fontSize: 13,
    fontVariantNumeric: 'tabular-nums',
    color: palette.text,
  },
  defs: {
    marginTop: 14,
    paddingTop: 12,
    borderTop: `1px solid ${palette.line}`,
  },
  defsTitle: {
    margin: '0 0 8px',
    fontSize: 13,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: '#94a0af',
  },
  defsList: {
    margin: 0,
    paddingLeft: 18,
    color: palette.muted,
    fontSize: 13,
    lineHeight: 1.45,
  },
  defsItem: {
    marginBottom: 6,
  },
  defsName: {
    color: palette.text,
  },
  disclaimer: {
    margin: '10px 0 0',
    color: palette.faint,
    fontSize: 12,
    lineHeight: 1.4,
  },
}

const css = `
.ace-accuracy-chip:focus-visible {
  outline: 2px solid ${palette.focus};
  outline-offset: 2px;
}
@media (max-width: 390px) {
  .ace-accuracy-chip {
    flex: 1 1 calc(50% - 8px);
  }
}
`
