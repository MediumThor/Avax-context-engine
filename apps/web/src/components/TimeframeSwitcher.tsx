export const CHART_TIMEFRAMES = ['1w', '1d', '4h', '1h', '15m', '5m'] as const
export type ChartTimeframe = (typeof CHART_TIMEFRAMES)[number]

export const TF_LABELS: Record<ChartTimeframe, string> = {
  '1w': '1W',
  '1d': '1D',
  '4h': '4H',
  '1h': '1H',
  '15m': '15m',
  '5m': '5m',
}

export const CHART_LIMITS: Record<ChartTimeframe, number> = {
  '1w': 200,
  '1d': 250,
  '4h': 240,
  '1h': 336,
  '15m': 384,
  '5m': 576,
}

export function isChartTimeframe(value: string | null): value is ChartTimeframe {
  return CHART_TIMEFRAMES.includes(value as ChartTimeframe)
}

interface Props {
  value: ChartTimeframe
  onChange: (tf: ChartTimeframe) => void
}

export function TimeframeSwitcher({ value, onChange }: Props) {
  return (
    <div className="tfSwitch" role="tablist" aria-label="Chart timeframe">
      {CHART_TIMEFRAMES.map((tf) => (
        <button
          key={tf}
          type="button"
          role="tab"
          aria-selected={value === tf}
          className={value === tf ? 'active' : ''}
          onClick={() => onChange(tf)}
        >
          {TF_LABELS[tf]}
        </button>
      ))}
    </div>
  )
}
