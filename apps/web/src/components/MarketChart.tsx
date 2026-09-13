import { useEffect, useRef } from 'react'
import { CandlestickSeries, HistogramSeries, LineSeries, createChart, type IChartApi } from 'lightweight-charts'
import type { Candle } from '../api/types'

interface Props {
  candles: Candle[]
  className?: string
}

export function MarketChart({ candles, className }: Props) {
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
    const ema20 = candles.filter((c) => typeof c.ema20 === 'number' && Number.isFinite(c.ema20))
    if (ema20.length) {
      chart.addSeries(LineSeries, { color: '#8cb4ff', lineWidth: 2, priceLineVisible: false }).setData(
        ema20.map((c) => ({ time: c.time as never, value: c.ema20 as number })),
      )
    }
    const ema50 = candles.filter((c) => typeof c.ema50 === 'number' && Number.isFinite(c.ema50))
    if (ema50.length) {
      chart.addSeries(LineSeries, { color: '#f0c36a', lineWidth: 2, priceLineVisible: false }).setData(
        ema50.map((c) => ({ time: c.time as never, value: c.ema50 as number })),
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
  }, [candles])
  return <div ref={host} className={className} aria-label="AVAX market chart" />
}
