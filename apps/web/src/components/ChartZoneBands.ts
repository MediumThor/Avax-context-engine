import type {
  IChartApi,
  IPrimitivePaneRenderer,
  IPrimitivePaneView,
  ISeriesApi,
  ISeriesPrimitive,
  SeriesAttachedParameter,
  Time,
} from 'lightweight-charts'

export interface ChartZone {
  id: string
  lower: number
  upper: number
  role: string
  known_at?: string | null
}

function fillFor(role: string): string {
  if (role === 'support') return 'rgba(37,208,154,0.16)'
  if (role === 'resistance') return 'rgba(255,89,100,0.16)'
  return 'rgba(240,195,106,0.16)'
}

function knownUnix(iso?: string | null): number | null {
  if (!iso) return null
  const ms = Date.parse(iso)
  return Number.isFinite(ms) ? Math.floor(ms / 1000) : null
}

interface Rect {
  x1: number
  x2: number
  y1: number
  y2: number
  fill: string
}

class ZoneRenderer implements IPrimitivePaneRenderer {
  constructor(private readonly rects: Rect[]) {}

  draw(target: { useBitmapCoordinateSpace: (fn: (scope: { context: CanvasRenderingContext2D; horizontalPixelRatio: number; verticalPixelRatio: number }) => void) => void }) {
    target.useBitmapCoordinateSpace((scope) => {
      const ctx = scope.context
      const hr = scope.horizontalPixelRatio
      const vr = scope.verticalPixelRatio
      for (const r of this.rects) {
        if (![r.x1, r.x2, r.y1, r.y2].every(Number.isFinite)) continue
        ctx.fillStyle = r.fill
        ctx.fillRect(
          Math.min(r.x1, r.x2) * hr,
          Math.min(r.y1, r.y2) * vr,
          Math.abs(r.x2 - r.x1) * hr,
          Math.abs(r.y2 - r.y1) * vr,
        )
      }
    })
  }
}

class ZonePaneView implements IPrimitivePaneView {
  private rendererObj: ZoneRenderer | null = null

  constructor(private readonly owner: ZoneBandPrimitive) {}

  zOrder() {
    return 'bottom' as const
  }

  update() {
    this.rendererObj = new ZoneRenderer(this.owner.layout())
  }

  renderer() {
    return this.rendererObj
  }
}

/** Shaded support/resistance bands from closed-bar zone bounds. Does not invent future width. */
export class ZoneBandPrimitive implements ISeriesPrimitive<Time> {
  private chart: IChartApi | null = null
  private series: ISeriesApi<'Candlestick'> | null = null
  private readonly view: ZonePaneView

  constructor(
    private readonly zones: ChartZone[],
    private readonly timeStart: number,
    private readonly timeEnd: number,
  ) {
    this.view = new ZonePaneView(this)
  }

  attached(param: SeriesAttachedParameter<Time>) {
    this.chart = param.chart as IChartApi
    this.series = param.series as ISeriesApi<'Candlestick'>
    this.view.update()
    param.requestUpdate()
  }

  detached() {
    this.chart = null
    this.series = null
  }

  updateAllViews() {
    this.view.update()
  }

  paneViews() {
    return [this.view]
  }

  layout(): Rect[] {
    if (!this.chart || !this.series) return []
    const scale = this.chart.timeScale()
    return this.zones.map((zone) => {
      const known = knownUnix(zone.known_at)
      const t0 = Math.max(this.timeStart, known ?? this.timeStart)
      const t1 = this.timeEnd
      return {
        x1: scale.timeToCoordinate(t0 as Time) ?? Number.NaN,
        x2: scale.timeToCoordinate(t1 as Time) ?? Number.NaN,
        y1: this.series!.priceToCoordinate(zone.upper) ?? Number.NaN,
        y2: this.series!.priceToCoordinate(zone.lower) ?? Number.NaN,
        fill: fillFor(zone.role),
      }
    })
  }
}
