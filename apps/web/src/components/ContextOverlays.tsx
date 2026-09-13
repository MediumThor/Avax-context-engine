import { useId, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent } from 'react'

export type OverlayRole = 'support' | 'resistance' | 'mixed'
export type PivotKind = 'HH' | 'HL' | 'LH' | 'LL' | 'state_change'
export type OverlayEventKind = 'breakout' | 'retest' | 'failure'
export type OverlayOrigin = 'system' | 'analyst'

export interface OverlayProvenance {
  sources?: readonly string[]
  timeframes?: readonly string[]
  rule?: string
  status?: string
  notes?: string
}

export interface OverlayZone {
  id: string
  lower: number
  upper: number
  role: OverlayRole
  strength: number
  test_count: number
  known_at?: string | null
  provenance?: OverlayProvenance | null
  timeframes?: readonly string[]
  status?: string
}

export interface OverlayPivot {
  id: string
  price: number
  kind: PivotKind
  time?: number | null
  known_at?: string | null
  provenance?: OverlayProvenance | null
}

export interface OverlayEvent {
  id: string
  kind: OverlayEventKind
  price: number
  time?: number | null
  zone_id?: string | null
  known_at?: string | null
  provenance?: OverlayProvenance | null
}

export interface AnalystAnnotation {
  id: string
  label: string
  lower?: number
  upper?: number
  price?: number
  note?: string
  time?: number | null
  known_at?: string | null
  provenance?: OverlayProvenance | null
}

export interface ContextOverlaysProps {
  zones: readonly OverlayZone[]
  pivots?: readonly OverlayPivot[]
  events?: readonly OverlayEvent[]
  analystAnnotations?: readonly AnalystAnnotation[]
  priceMin?: number
  priceMax?: number
  timeStart?: number
  timeEnd?: number
  plotHeight?: number
  className?: string
  'aria-label'?: string
  onInspect?: (id: string | null) => void
}

type DrawMode = 'range' | 'marker' | 'none'

interface Inspectable {
  key: string
  origin: OverlayOrigin
  kind: 'zone' | 'pivot' | 'event' | 'annotation'
  title: string
  detail: string
  lower?: number
  upper?: number
  price?: number
  time?: number | null
  known_at?: string | null
  provenance?: OverlayProvenance | null
  role?: OverlayRole
  strength?: number
  test_count?: number
  status?: string
  timeframes?: readonly string[]
  note?: string
  zone_id?: string | null
  eventKind?: OverlayEventKind
  pivotKind?: PivotKind
  draw: DrawMode
  invalidReason?: string
}

const OVERLAY_CSS = `
.ace-ctxov{--bg:#0d1118;--ink:#eef3f8;--muted:#8f9bad;--line:#1c2430;--sys:#25d09a;--res:#ff5964;--mix:#f0c36a;--an:#8cb4ff;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:14px;overflow:hidden;font-family:inherit;max-width:100%}
.ace-ctxov *{box-sizing:border-box}
.ace-ctxov-head{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:flex-start;justify-content:space-between;padding:12px 14px;border-bottom:1px solid var(--line)}
.ace-ctxov-head h2{margin:0;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#94a0af}
.ace-ctxov-head p{margin:6px 0 0;color:var(--muted);font-size:12px;line-height:1.4;max-width:42rem}
.ace-ctxov-legend{display:flex;flex-wrap:wrap;gap:8px}
.ace-ctxov-swatch{display:flex;align-items:center;gap:8px;min-height:44px;padding:0 10px;border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:700;letter-spacing:.04em}
.ace-ctxov-swatch i{display:block;width:22px;height:14px;border-radius:2px}
.ace-ctxov-swatch.sys i{border:1px solid var(--sys);background:repeating-linear-gradient(-45deg,rgba(37,208,154,.45) 0 2px,rgba(37,208,154,.08) 2px 6px)}
.ace-ctxov-swatch.an{border-style:dashed;border-color:#3a4a66}
.ace-ctxov-swatch.an i{border:1px dashed var(--an);background:radial-gradient(circle at 2px 2px,rgba(140,180,255,.7) 1.1px,transparent 1.2px) 0 0 / 6px 6px,rgba(140,180,255,.1)}
.ace-ctxov-plotwrap{position:relative;border-bottom:1px solid var(--line)}
.ace-ctxov-plot{position:relative;width:100%;background:#07090d}
.ace-ctxov-canvas{position:absolute;inset:0 56px 22px 0}
.ace-ctxov-canvas.with-gutter{left:72px}
.ace-ctxov-gutter{position:absolute;left:0;top:0;bottom:22px;width:72px;border-right:1px dashed #2a3340;color:var(--muted);font-size:10px;padding:6px;line-height:1.3}
.ace-ctxov-axis{position:absolute;top:0;right:0;bottom:22px;width:56px;border-left:1px solid #151a22;font-size:10px;color:#9aa5b3}
.ace-ctxov-tick{position:absolute;right:6px;transform:translateY(-50%);white-space:nowrap}
.ace-ctxov-timeaxis{position:absolute;left:0;right:0;bottom:0;height:22px;color:#7f8997;font-size:10px;display:flex;justify-content:space-between;padding:4px 56px 0 8px}
.ace-ctxov-empty{min-height:160px;display:flex;align-items:center;padding:16px;color:var(--muted);font-size:13px;line-height:1.45}
.ace-ctxov-band,.ace-ctxov-marker{position:absolute;border:0;padding:0;cursor:pointer;background:transparent;color:inherit;font:inherit}
.ace-ctxov-band{left:0;right:0;min-height:44px}
.ace-ctxov-band-fill{position:absolute;left:0;right:0;pointer-events:none}
.ace-ctxov-band.sys .ace-ctxov-band-fill{border-top:2px solid;border-bottom:2px solid}
.ace-ctxov-band.an .ace-ctxov-band-fill{border:1px dashed}
.ace-ctxov-band.support .ace-ctxov-band-fill{border-color:var(--sys);background:repeating-linear-gradient(-45deg,rgba(37,208,154,.34) 0 2px,rgba(37,208,154,.07) 2px 7px)}
.ace-ctxov-band.resistance .ace-ctxov-band-fill{border-color:var(--res);background:repeating-linear-gradient(-45deg,rgba(255,89,100,.34) 0 2px,rgba(255,89,100,.07) 2px 7px)}
.ace-ctxov-band.mixed .ace-ctxov-band-fill{border-color:var(--mix);background:repeating-linear-gradient(-45deg,rgba(240,195,106,.34) 0 2px,rgba(240,195,106,.07) 2px 7px)}
.ace-ctxov-band.an .ace-ctxov-band-fill{border-color:var(--an);border-radius:6px;background:radial-gradient(circle at 2px 2px,rgba(140,180,255,.62) 1.15px,transparent 1.25px) 0 0 / 7px 7px,rgba(140,180,255,.09)}
.ace-ctxov-badge{position:absolute;left:8px;top:4px;font-size:10px;font-weight:800;letter-spacing:.06em;padding:2px 6px;border-radius:4px;background:#0b0e14;pointer-events:none;max-width:calc(100% - 16px);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ace-ctxov-badge.sys{color:var(--ink)}
.ace-ctxov-badge.an{color:var(--an);font-style:italic;border:1px dashed #3a4a66}
.ace-ctxov-marker{min-width:44px;min-height:44px;display:flex;align-items:center;gap:6px;transform:translate(-50%,-50%)}
.ace-ctxov-marker.unguttered{left:50%}
.ace-ctxov-shape{width:16px;height:16px;flex:0 0 16px}
.ace-ctxov-shape.diamond{background:#c7d0dc;transform:rotate(45deg)}
.ace-ctxov-shape.tri-up{width:0;height:0;background:transparent;border-left:8px solid transparent;border-right:8px solid transparent;border-bottom:14px solid #c7d0dc}
.ace-ctxov-shape.tri-dn{width:0;height:0;background:transparent;border-left:8px solid transparent;border-right:8px solid transparent;border-top:14px solid #f0c36a}
.ace-ctxov-shape.fail{background:transparent;border:2px solid #ff5964;border-radius:2px;position:relative}
.ace-ctxov-shape.fail:before,.ace-ctxov-shape.fail:after{content:"";position:absolute;left:6px;top:1px;width:2px;height:12px;background:#ff5964}
.ace-ctxov-shape.fail:before{transform:rotate(45deg)}
.ace-ctxov-shape.fail:after{transform:rotate(-45deg)}
.ace-ctxov-shape.dot{border:2px dashed var(--an);border-radius:50%;background:radial-gradient(circle,rgba(140,180,255,.5) 40%,transparent 41%)}
.ace-ctxov-mlabel{font-size:11px;font-weight:700;text-shadow:0 1px 2px #07090d}
.ace-ctxov-marker.an .ace-ctxov-mlabel{font-style:italic;color:var(--an)}
.ace-ctxov-band[aria-current="true"] .ace-ctxov-band-fill,.ace-ctxov-marker[aria-current="true"]{outline:2px solid #eef3f8;outline-offset:2px}
.ace-ctxov-band:focus-visible,.ace-ctxov-marker:focus-visible,.ace-ctxov-item:focus-visible,.ace-ctxov-clear:focus-visible{outline:2px solid #eef3f8;outline-offset:2px}
.ace-ctxov-body{display:flex;flex-direction:column}
.ace-ctxov-list{margin:0;padding:8px;list-style:none;display:flex;flex-direction:column;gap:6px;border-bottom:1px solid var(--line)}
.ace-ctxov-item{min-height:44px;width:100%;text-align:left;border:1px solid var(--line);border-radius:8px;background:#0b0e14;color:var(--ink);padding:8px 10px;cursor:pointer;display:flex;flex-direction:column;gap:2px}
.ace-ctxov-item[aria-current="true"]{border-color:#4a5568;background:#141a23}
.ace-ctxov-item.an{border-style:dashed}
.ace-ctxov-item b{font-size:13px}
.ace-ctxov-item span{font-size:12px;color:var(--muted)}
.ace-ctxov-inspect{padding:12px 14px 16px}
.ace-ctxov-inspect h3{margin:0 0 8px;font-size:14px}
.ace-ctxov-inspect dl{margin:0;display:grid;grid-template-columns:minmax(7rem,34%) 1fr;gap:6px 10px;font-size:13px}
.ace-ctxov-inspect dt{color:var(--muted)}
.ace-ctxov-inspect dd{margin:0;overflow-wrap:anywhere}
.ace-ctxov-missing{color:#f0c36a}
.ace-ctxov-note{margin:10px 0 0;color:var(--muted);font-size:12px;line-height:1.4}
.ace-ctxov-clear{min-height:44px;min-width:44px;margin-top:10px;border:1px solid #2a3340;border-radius:8px;background:transparent;color:#9aa5b3;cursor:pointer;padding:0 12px;font-weight:600}
.ace-ctxov-sr{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(min-width:720px){
  .ace-ctxov-body{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
  .ace-ctxov-list{border-bottom:0;border-right:1px solid var(--line);max-height:360px;overflow:auto}
}
`

function finite(n: unknown): n is number {
  return typeof n === 'number' && Number.isFinite(n)
}

function formatPrice(n: number): string {
  return String(n)
}

function formatTime(time: number): string {
  return new Date(time * (time < 1e12 ? 1000 : 1)).toISOString()
}

function clamp01(n: number): number {
  if (!finite(n)) return 0.2
  return Math.min(1, Math.max(0, n))
}

function provenanceEmptiness(p: OverlayProvenance | null | undefined): 'absent' | 'empty' | 'present' {
  if (p == null) return 'absent'
  const sources = p.sources?.filter(Boolean) ?? []
  const timeframes = p.timeframes?.filter(Boolean) ?? []
  const hasText = Boolean(p.rule || p.status || p.notes)
  if (sources.length === 0 && timeframes.length === 0 && !hasText) return 'empty'
  return 'present'
}

function domainFrom(
  prices: number[],
  priceMin?: number,
  priceMax?: number,
): { min: number; max: number; source: 'caller' | 'derived' } | { error: string } | null {
  if (finite(priceMin) && finite(priceMax)) {
    if (priceMax > priceMin) return { min: priceMin, max: priceMax, source: 'caller' }
    return { error: 'priceMax must be greater than priceMin. Plot not drawn; no substitute domain was invented.' }
  }
  if (prices.length === 0) return null
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  if (min === max) {
    const pad = Math.max(Math.abs(min) * 0.01, 1e-9)
    return { min: min - pad, max: max + pad, source: 'derived' }
  }
  const pad = (max - min) * 0.08
  return { min: min - pad, max: max + pad, source: 'derived' }
}

function priceToPct(price: number, min: number, max: number): number {
  if (max === min) return 50
  return ((max - price) / (max - min)) * 100
}

function collectInspectables(
  zones: readonly OverlayZone[],
  pivots: readonly OverlayPivot[],
  events: readonly OverlayEvent[],
  annotations: readonly AnalystAnnotation[],
): Inspectable[] {
  const items: Inspectable[] = []

  for (const zone of zones) {
    const boundsOk = finite(zone.lower) && finite(zone.upper)
    const ordered = boundsOk && zone.lower < zone.upper
    const degenerate = boundsOk && zone.lower === zone.upper
    items.push({
      key: `zone:${zone.id}`,
      origin: 'system',
      kind: 'zone',
      title: `SYSTEM ${zone.role} zone`,
      detail: boundsOk ? `${formatPrice(zone.lower)} – ${formatPrice(zone.upper)}` : 'price bounds not usable',
      lower: zone.lower,
      upper: zone.upper,
      known_at: zone.known_at,
      provenance: zone.provenance,
      role: zone.role,
      strength: zone.strength,
      test_count: zone.test_count,
      status: zone.status,
      timeframes: zone.timeframes,
      draw: ordered ? 'range' : 'none',
      invalidReason: !boundsOk
        ? 'lower/upper are missing or not finite. Not drawn. No substitute level was invented.'
        : degenerate
          ? 'lower equals upper. Not thickened into a fake structural line.'
          : zone.lower > zone.upper
            ? 'lower is above upper. Not drawn and not silently swapped.'
            : undefined,
    })
  }

  for (const pivot of pivots) {
    const ok = finite(pivot.price)
    items.push({
      key: `pivot:${pivot.id}`,
      origin: 'system',
      kind: 'pivot',
      title: `SYSTEM ${pivot.kind === 'state_change' ? 'state change' : pivot.kind} pivot`,
      detail: ok ? formatPrice(pivot.price) : 'price not usable',
      price: pivot.price,
      time: pivot.time,
      known_at: pivot.known_at,
      provenance: pivot.provenance,
      pivotKind: pivot.kind,
      draw: ok ? 'marker' : 'none',
      invalidReason: ok ? undefined : 'pivot price is missing or not finite. Not drawn.',
    })
  }

  for (const event of events) {
    const ok = finite(event.price)
    items.push({
      key: `event:${event.id}`,
      origin: 'system',
      kind: 'event',
      title: `SYSTEM ${event.kind} event`,
      detail: ok ? formatPrice(event.price) : 'price not usable',
      price: event.price,
      time: event.time,
      known_at: event.known_at,
      provenance: event.provenance,
      eventKind: event.kind,
      zone_id: event.zone_id,
      draw: ok ? 'marker' : 'none',
      invalidReason: ok ? undefined : 'event price is missing or not finite. Not drawn.',
    })
  }

  for (const note of annotations) {
    const hasRange = finite(note.lower) && finite(note.upper) && note.lower < note.upper
    const hasPoint = finite(note.price)
    items.push({
      key: `annotation:${note.id}`,
      origin: 'analyst',
      kind: 'annotation',
      title: `ANALYST ${note.label}`,
      detail: hasRange
        ? `${formatPrice(note.lower as number)} – ${formatPrice(note.upper as number)}`
        : hasPoint
          ? formatPrice(note.price as number)
          : 'no price provided',
      lower: note.lower,
      upper: note.upper,
      price: note.price,
      time: note.time,
      known_at: note.known_at,
      provenance: note.provenance,
      note: note.note,
      draw: hasRange ? 'range' : hasPoint ? 'marker' : 'none',
      invalidReason:
        !hasRange && !hasPoint
          ? 'Analyst annotation has no usable price or range. Listed only; nothing was invented for the plot.'
          : finite(note.lower) && finite(note.upper) && note.lower === note.upper
            ? 'Analyst range is zero-width. Not drawn as a structural zone.'
            : finite(note.lower) && finite(note.upper) && note.lower > note.upper
              ? 'Analyst lower is above upper. Not drawn and not silently swapped.'
              : undefined,
    })
  }

  return items
}

function timeDomain(
  items: Inspectable[],
  timeStart?: number,
  timeEnd?: number,
): { start: number; end: number } | null {
  if (finite(timeStart) && finite(timeEnd) && timeEnd > timeStart) return { start: timeStart, end: timeEnd }
  const times = items.map((item) => item.time).filter(finite)
  if (times.length === 0) return null
  const start = Math.min(...times)
  const end = Math.max(...times)
  if (start === end) return { start: start - 1, end: end + 1 }
  return { start, end }
}

function markerShape(item: Inspectable): string {
  if (item.origin === 'analyst') return 'dot'
  if (item.kind === 'pivot') return 'diamond'
  if (item.eventKind === 'breakout') return 'tri-up'
  if (item.eventKind === 'retest') return 'tri-dn'
  if (item.eventKind === 'failure') return 'fail'
  return 'diamond'
}

export function ContextOverlays({
  zones,
  pivots,
  events,
  analystAnnotations,
  priceMin,
  priceMax,
  timeStart,
  timeEnd,
  plotHeight = 220,
  className,
  'aria-label': ariaLabel,
  onInspect,
}: ContextOverlaysProps) {
  const uid = useId()
  const listRef = useRef<HTMLUListElement>(null)
  const inspectorRef = useRef<HTMLElement>(null)
  const itemRefs = useRef(new Map<string, HTMLButtonElement>())
  const [selectedKey, setSelectedKey] = useState<string | null>(null)

  const zoneList = zones ?? []
  const pivotList = pivots ?? []
  const eventList = events ?? []
  const annotationList = analystAnnotations ?? []

  const items = useMemo(
    () => collectInspectables(zoneList, pivotList, eventList, annotationList),
    [zoneList, pivotList, eventList, annotationList],
  )

  const prices = useMemo(() => {
    const out: number[] = []
    for (const item of items) {
      if (finite(item.lower)) out.push(item.lower)
      if (finite(item.upper)) out.push(item.upper)
      if (finite(item.price)) out.push(item.price)
    }
    return out
  }, [items])

  const domain = domainFrom(prices, priceMin, priceMax)
  const times = timeDomain(items, timeStart, timeEnd)
  const needsGutter = items.some((item) => item.draw === 'marker' && !finite(item.time))
  const selected = items.find((item) => item.key === selectedKey) ?? null
  const height = Math.max(160, plotHeight)

  function select(key: string | null, focusInspector: boolean) {
    setSelectedKey(key)
    onInspect?.(key)
    if (focusInspector && key) inspectorRef.current?.focus()
  }

  function focusItem(key: string) {
    itemRefs.current.get(key)?.focus()
  }

  function onListKeyDown(event: KeyboardEvent<HTMLUListElement>) {
    if (items.length === 0) return
    const current = items.findIndex((item) => item.key === (selectedKey ?? document.activeElement?.getAttribute('data-ace-key')))
    const index = current >= 0 ? current : 0
    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
      event.preventDefault()
      const next = items[(index + 1) % items.length]
      select(next.key, false)
      focusItem(next.key)
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
      event.preventDefault()
      const next = items[(index - 1 + items.length) % items.length]
      select(next.key, false)
      focusItem(next.key)
    } else if (event.key === 'Home') {
      event.preventDefault()
      select(items[0].key, false)
      focusItem(items[0].key)
    } else if (event.key === 'End') {
      event.preventDefault()
      const last = items[items.length - 1]
      select(last.key, false)
      focusItem(last.key)
    } else if (event.key === 'Escape') {
      event.preventDefault()
      select(null, false)
    }
  }

  const axisPrices = [...new Set(prices)].sort((a, b) => b - a)
  const plotStyle = { height } satisfies CSSProperties

  return (
    <section
      className={['ace-ctxov', className].filter(Boolean).join(' ')}
      aria-label={ariaLabel ?? 'Context structure overlays'}
      data-ace-component="context-overlays"
    >
      <style>{OVERLAY_CSS}</style>
      <header className="ace-ctxov-head">
        <div>
          <h2>Structure overlays</h2>
          <p>
            Read-only context. Ranges come only from props. System structure uses a hatch and a SYSTEM label.
            Analyst notes use a dotted pattern, dashed edge, and an ANALYST label. This is not an order ticket.
          </p>
        </div>
        <div className="ace-ctxov-legend" aria-hidden="true">
          <div className="ace-ctxov-swatch sys">
            <i />
            SYSTEM hatch
          </div>
          <div className="ace-ctxov-swatch an">
            <i />
            ANALYST dots
          </div>
        </div>
      </header>

      <div className="ace-ctxov-plotwrap">
        {domain && !('error' in domain) ? (
          <div className="ace-ctxov-plot" style={plotStyle} role="group" aria-label="Price-mapped overlay plot">
            {needsGutter && (
              <div className="ace-ctxov-gutter">time not provided</div>
            )}
            <div className={`ace-ctxov-canvas${needsGutter ? ' with-gutter' : ''}`}>
              {items.map((item) => {
                if (item.draw === 'range' && finite(item.lower) && finite(item.upper)) {
                  const topPct = priceToPct(item.upper, domain.min, domain.max)
                  const botPct = priceToPct(item.lower, domain.min, domain.max)
                  const visualH = Math.max(botPct - topPct, 0)
                  const opacity = item.origin === 'system' && finite(item.strength) ? 0.35 + 0.55 * clamp01(item.strength) : 0.85
                  const hitH = Math.max(visualH, (44 / height) * 100)
                  const hitTop = topPct - (hitH - visualH) / 2
                  const roleClass = item.role ?? 'mixed'
                  return (
                    <button
                      key={item.key}
                      type="button"
                      className={`ace-ctxov-band ${item.origin} ${roleClass}`}
                      style={{ top: `${hitTop}%`, height: `${hitH}%` }}
                      aria-current={selectedKey === item.key || undefined}
                      aria-label={item.title + ' ' + item.detail}
                      data-ace-key={item.key}
                      data-ace-origin={item.origin}
                      onClick={() => select(item.key, true)}
                    >
                      <span
                        className="ace-ctxov-band-fill"
                        style={{
                          top: `${((topPct - hitTop) / hitH) * 100}%`,
                          height: `${(visualH / hitH) * 100}%`,
                          opacity,
                        }}
                      />
                      <span className={`ace-ctxov-badge ${item.origin}`}>
                        {item.origin === 'system' ? `SYSTEM · ${item.role}` : `ANALYST · ${item.title.replace(/^ANALYST /, '')}`}
                      </span>
                    </button>
                  )
                }
                if (item.draw === 'marker' && finite(item.price)) {
                  const top = priceToPct(item.price, domain.min, domain.max)
                  const hasTime = finite(item.time) && times
                  const left = hasTime && times
                    ? ((item.time as number) - times.start) / (times.end - times.start) * 100
                    : needsGutter
                      ? 0
                      : 50
                  return (
                    <button
                      key={item.key}
                      type="button"
                      className={`ace-ctxov-marker ${item.origin}${hasTime || needsGutter ? '' : ' unguttered'}`}
                      style={{ top: `${top}%`, left: `${left}%` }}
                      aria-current={selectedKey === item.key || undefined}
                      aria-label={item.title + ' ' + item.detail}
                      data-ace-key={item.key}
                      data-ace-origin={item.origin}
                      onClick={() => select(item.key, true)}
                    >
                      <span className={`ace-ctxov-shape ${markerShape(item)}`} />
                      <span className="ace-ctxov-mlabel">
                        {item.origin === 'analyst' ? 'ANALYST' : item.pivotKind ?? item.eventKind}
                      </span>
                    </button>
                  )
                }
                return null
              })}
            </div>
            <div className="ace-ctxov-axis" aria-hidden="true">
              {axisPrices.map((price) => (
                <span key={price} className="ace-ctxov-tick" style={{ top: `${priceToPct(price, domain.min, domain.max)}%` }}>
                  {formatPrice(price)}
                </span>
              ))}
            </div>
            <div className="ace-ctxov-timeaxis">
              <span>
                {times ? formatTime(times.start) : 'No event timestamps provided'}
              </span>
              <span>{times ? formatTime(times.end) : ''}</span>
            </div>
          </div>
        ) : (
          <div className="ace-ctxov-empty" role="status">
            {domain && 'error' in domain
              ? domain.error
              : items.length === 0
                ? 'No structural overlays provided. This view does not invent support, resistance, pivots, or events.'
                : 'No usable prices were provided, so nothing is mapped onto a plot. Items remain listed for inspection.'}
          </div>
        )}
      </div>

      <div className="ace-ctxov-body">
        <ul
          ref={listRef}
          className="ace-ctxov-list"
          aria-label="Inspectable overlays"
          onKeyDown={onListKeyDown}
        >
          {items.length === 0 && (
            <li>
              <button type="button" className="ace-ctxov-item" disabled>
                <b>Empty overlay set</b>
                <span>Waiting for Context Engine or analyst props. No default AVAX levels are assumed.</span>
              </button>
            </li>
          )}
          {items.map((item) => (
            <li key={item.key}>
              <button
                type="button"
                id={`${uid}-${item.key}`}
                className={`ace-ctxov-item ${item.origin}`}
                aria-current={selectedKey === item.key || undefined}
                aria-pressed={selectedKey === item.key}
                data-ace-key={item.key}
                ref={(node) => {
                  if (node) itemRefs.current.set(item.key, node)
                  else itemRefs.current.delete(item.key)
                }}
                onClick={() => select(item.key, true)}
              >
                <b>{item.title}</b>
                <span>{item.detail}{item.invalidReason ? ` · ${item.invalidReason}` : ''}</span>
              </button>
            </li>
          ))}
        </ul>

        <aside
          className="ace-ctxov-inspect"
          ref={inspectorRef}
          tabIndex={-1}
          aria-live="polite"
          aria-label="Overlay provenance"
        >
          {selected ? <ProvenancePanel item={selected} /> : (
            <>
              <h3>Provenance</h3>
              <p className="ace-ctxov-note">
                Select a zone, pivot, event, or annotation from the list or the plot. Inspection is tap and keyboard;
                hover is not required.
              </p>
            </>
          )}
          {selected && (
            <button type="button" className="ace-ctxov-clear" onClick={() => select(null, false)}>
              Clear selection
            </button>
          )}
        </aside>
      </div>

      <p className="ace-ctxov-sr">
        {zoneList.length} system zones, {pivotList.length} pivots, {eventList.length} events, {annotationList.length} analyst annotations.
        Domain {domain && !('error' in domain) ? domain.source : 'unavailable'}.
      </p>
    </section>
  )
}

function ProvenancePanel({ item }: { item: Inspectable }) {
  const emptiness = provenanceEmptiness(item.provenance)
  const sources = item.provenance?.sources?.filter(Boolean) ?? []
  const timeframes = (item.provenance?.timeframes ?? item.timeframes)?.filter(Boolean) ?? []

  return (
    <>
      <h3>{item.title}</h3>
      <dl>
        <dt>Origin</dt>
        <dd>{item.origin === 'system' ? 'System-derived Context Engine structure' : 'Analyst annotation — not structural authority'}</dd>
        <dt>Kind</dt>
        <dd>{item.kind}{item.role ? ` · ${item.role}` : ''}{item.pivotKind ? ` · ${item.pivotKind}` : ''}{item.eventKind ? ` · ${item.eventKind}` : ''}</dd>
        {finite(item.lower) && finite(item.upper) && (
          <>
            <dt>Range</dt>
            <dd>{formatPrice(item.lower)} – {formatPrice(item.upper)}</dd>
          </>
        )}
        {finite(item.price) && (
          <>
            <dt>Price</dt>
            <dd>{formatPrice(item.price)}</dd>
          </>
        )}
        {item.strength !== undefined && (
          <>
            <dt>Strength</dt>
            <dd>
              {String(item.strength)} provided field. Not a calibrated confidence percentage.
            </dd>
          </>
        )}
        {item.test_count !== undefined && (
          <>
            <dt>Tests</dt>
            <dd>{String(item.test_count)} recorded test_count</dd>
          </>
        )}
        {item.status && (
          <>
            <dt>Status</dt>
            <dd>{item.status}</dd>
          </>
        )}
        {item.zone_id != null && item.zone_id !== '' && (
          <>
            <dt>Linked zone</dt>
            <dd>{item.zone_id}</dd>
          </>
        )}
        <dt>known_at</dt>
        <dd className={item.known_at ? undefined : 'ace-ctxov-missing'}>
          {item.known_at || 'known_at not provided. This overlay cannot be treated as point-in-time confirmed.'}
        </dd>
        <dt>Observed time</dt>
        <dd className={finite(item.time) ? undefined : 'ace-ctxov-missing'}>
          {finite(item.time) ? formatTime(item.time) : 'No event timestamp provided.'}
        </dd>
        <dt>Sources</dt>
        <dd className={sources.length ? undefined : 'ace-ctxov-missing'}>
          {sources.length ? sources.join(', ') : emptiness === 'empty' ? 'Provenance object is present but empty: no sources.' : 'No provenance sources provided.'}
        </dd>
        <dt>Timeframes</dt>
        <dd className={timeframes.length ? undefined : 'ace-ctxov-missing'}>
          {timeframes.length ? timeframes.join(', ') : 'No supporting timeframes provided.'}
        </dd>
        <dt>Rule</dt>
        <dd className={item.provenance?.rule ? undefined : 'ace-ctxov-missing'}>
          {item.provenance?.rule || 'No derivation rule provided.'}
        </dd>
        {item.provenance?.notes && (
          <>
            <dt>Notes</dt>
            <dd>{item.provenance.notes}</dd>
          </>
        )}
        {item.note && (
          <>
            <dt>Analyst note</dt>
            <dd>{item.note}</dd>
          </>
        )}
      </dl>
      {item.invalidReason && <p className="ace-ctxov-note ace-ctxov-missing">{item.invalidReason}</p>}
      {emptiness === 'absent' && (
        <p className="ace-ctxov-note ace-ctxov-missing">
          Provenance was omitted. Why this object exists is unknown in this view.
        </p>
      )}
      {emptiness === 'empty' && (
        <p className="ace-ctxov-note ace-ctxov-missing">
          Provenance is present but empty (no sources, timeframes, rule, status, or notes).
        </p>
      )}
      {item.origin === 'analyst' && (
        <p className="ace-ctxov-note">
          Analyst drawings have no inherent structural authority. They are not promoted to system support or resistance by being shown here.
        </p>
      )}
      {item.origin === 'system' && finite(item.strength) && (
        <p className="ace-ctxov-note">
          Fill weight follows the provided strength field for visibility only. It is not a probability or accuracy claim.
        </p>
      )}
    </>
  )
}
