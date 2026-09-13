import { useEffect, useRef } from 'react'
import {
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type SeriesMarker,
  type Time,
} from 'lightweight-charts'
import type { Candle, SwingPivot } from '../api/types'
import { ZoneBandPrimitive, type ChartZone } from './ChartZoneBands'

interface Props {
  candles: Candle[]
  zones?: ChartZone[]
  pivots?: SwingPivot[]
  className?: string
}

export function MarketChart({ candles, zones = [], pivots = [], className }: Props) {
  const host = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  useEffect(() => {
    if (!host.current) return
    const chart = createChart(host.current, {
      autoSize: true,
      layout: { background: { color: '#0a0d12' }, textColor: '#c7d0dc' },
      grid: { vertLines: { color: '#151a22' }, horzLines: { color: '#151a22' } },
      rightPriceScale: { borderColor: '#242b36' },
      timeScale: { borderColor: '#242b36', timeVisible: true },
    })
    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#25d09a',
      downColor: '#ff5964',
      borderVisible: false,
      wickUpColor: '#25d09a',
      wickDownColor: '#ff5964',
    })
    series.setData(candles.map((c) => ({ ...c, time: c.time as never })))
    if (zones.length && candles.length) {
      series.attachPrimitive(
        new ZoneBandPrimitive(zones, candles[0].time, candles[candles.length - 1].time),
      )
    }
    const candleTimes = new Set(candles.map((c) => c.time))
    const markers: SeriesMarker<Time>[] = pivots
      .filter((pivot) => candleTimes.has(pivot.time))
      .map((pivot) => ({
        time: pivot.time as Time,
        position: pivot.kind === 'high' ? 'aboveBar' : 'belowBar',
        color: pivot.kind === 'high' ? '#ff5964' : '#25d09a',
        shape: pivot.kind === 'high' ? 'arrowDown' : 'arrowUp',
        text: `${pivot.timeframe ?? '5m'} ${pivot.kind === 'high' ? 'H' : 'L'}`,
      }))
    if (markers.length) {
      createSeriesMarkers(series, markers)
    }
    const emaLayers: Array<{ key: keyof Candle; color: string; width: 1 | 2 }> = [
      { key: 'ema9', color: '#d6a4ff', width: 1 },
      { key: 'ema20', color: '#8cb4ff', width: 2 },
      { key: 'ema50', color: '#f0c36a', width: 2 },
      { key: 'ema100', color: '#6fbf9a', width: 1 },
      { key: 'ema200', color: '#9aa5b3', width: 1 },
    ]
    for (const layer of emaLayers) {
      const points = candles.filter((c) => typeof c[layer.key] === 'number' && Number.isFinite(c[layer.key]))
      if (!points.length) continue
      chart.addSeries(LineSeries, { color: layer.color, lineWidth: layer.width, priceLineVisible: false }).setData(
        points.map((c) => ({ time: c.time as never, value: c[layer.key] as number })),
      )
    }
    const volumes = candles.filter((c) => typeof c.volume === 'number' && Number.isFinite(c.volume))
    if (volumes.length) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      })
      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.78, bottom: 0 },
        borderVisible: false,
      })
      volumeSeries.setData(
        volumes.map((c) => ({
          time: c.time as never,
          value: c.volume as number,
          color: c.close >= c.open ? 'rgba(37,208,154,0.35)' : 'rgba(255,89,100,0.35)',
        })),
      )
    }
    chartRef.current = chart
    const resize = new ResizeObserver(() => chart.timeScale().fitContent())
    resize.observe(host.current)
    return () => {
      resize.disconnect()
      chart.remove()
      chartRef.current = null
    }
  }, [candles, zones, pivots])
  return <div ref={host} className={className} aria-label="AVAX market chart" />
}
