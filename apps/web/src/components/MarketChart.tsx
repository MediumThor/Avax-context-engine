import { useEffect, useRef } from 'react'
import { createChart, CandlestickSeries, type IChartApi } from 'lightweight-charts'
import type { Candle } from '../api/types'

interface Props { candles:Candle[]; className?:string }

export function MarketChart({candles,className}:Props){
  const host=useRef<HTMLDivElement>(null); const chartRef=useRef<IChartApi|null>(null)
  useEffect(()=>{
    if(!host.current)return
    const chart=createChart(host.current,{autoSize:true,layout:{background:{color:'#0a0d12'},textColor:'#c7d0dc'},grid:{vertLines:{color:'#151a22'},horzLines:{color:'#151a22'}},rightPriceScale:{borderColor:'#242b36'},timeScale:{borderColor:'#242b36',timeVisible:true}})
    const series=chart.addSeries(CandlestickSeries,{upColor:'#25d09a',downColor:'#ff5964',borderVisible:false,wickUpColor:'#25d09a',wickDownColor:'#ff5964'})
    series.setData(candles.map(c=>({...c,time:c.time as never})))
    chartRef.current=chart
    const resize=new ResizeObserver(()=>chart.timeScale().fitContent()); resize.observe(host.current)
    return()=>{resize.disconnect();chart.remove();chartRef.current=null}
  },[candles])
  return <div ref={host} className={className} aria-label="AVAX market chart" />
}
