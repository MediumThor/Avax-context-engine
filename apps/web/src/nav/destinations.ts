export const DEFAULT_SYMBOL = 'AVAXUSDT'

export const DEST_IDS = ['market', 'replay', 'accuracy', 'health', 'more'] as const
export type DestId = (typeof DEST_IDS)[number]

export const SHEET_PANELS = ['context', 'forecast', 'thesis', 'journal'] as const
export type SheetPanel = (typeof SHEET_PANELS)[number]

export const SHEET_LABELS: Record<SheetPanel, string> = {
  context: 'Context',
  forecast: 'Forecast',
  thesis: 'Thesis',
  journal: 'Journal',
}

export const DEST_LABELS: Record<DestId, string> = {
  market: 'Market',
  replay: 'Replay',
  accuracy: 'Accuracy',
  health: 'Health',
  more: 'More',
}

const SYMBOL_RE = /^[A-Z0-9]{3,20}$/

export type RouteState = {
  dest: DestId
  symbol: string
  asOf: string | null
  panel: SheetPanel
}

export function normalizeSymbol(raw?: string | null): string {
  if (!raw) return DEFAULT_SYMBOL
  const up = raw.toUpperCase()
  return SYMBOL_RE.test(up) ? up : DEFAULT_SYMBOL
}

export function readPanel(raw: string | null): SheetPanel {
  return (SHEET_PANELS as readonly string[]).includes(raw ?? '') ? (raw as SheetPanel) : 'context'
}

function rawQueryValue(search: string, key: string): string | null {
  const qs = search.startsWith('?') ? search.slice(1) : search
  if (!qs) return null
  for (const part of qs.split('&')) {
    const eq = part.indexOf('=')
    const name = decodeURIComponent(eq >= 0 ? part.slice(0, eq) : part)
    if (name !== key) continue
    const raw = eq >= 0 ? part.slice(eq + 1) : ''
    let decoded = raw.replace(/\+/g, '%2B')
    try {
      decoded = decodeURIComponent(decoded)
    } catch {
      decoded = raw
    }
    decoded = decoded.trim()
    return decoded.length > 0 ? decoded : null
  }
  return null
}

export function parseLocation(pathname: string, search = ''): RouteState {
  const asOf = rawQueryValue(search, 'as_of')
  const panel = readPanel(rawQueryValue(search, 'panel'))
  const parts = pathname.split('/').filter(Boolean)
  const head = (parts[0] ?? '').toLowerCase()

  if (head === 'replay') {
    return { dest: 'replay', symbol: normalizeSymbol(parts[1]), asOf, panel }
  }
  if (head === 'accuracy') {
    return { dest: 'accuracy', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context' }
  }
  if (head === 'health') {
    return { dest: 'health', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context' }
  }
  if (head === 'more' || head === 'system') {
    return { dest: 'more', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context' }
  }
  if (head === 'market' || head === '') {
    const symbol = normalizeSymbol(parts[1])
    if (asOf) return { dest: 'replay', symbol, asOf, panel }
    return { dest: 'market', symbol, asOf: null, panel }
  }
  return { dest: 'market', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context' }
}

export function pathFor(route: RouteState): string {
  switch (route.dest) {
    case 'market':
      return `/market/${route.symbol}`
    case 'replay':
      return `/replay/${route.symbol}`
    case 'accuracy':
      return '/accuracy'
    case 'health':
      return '/health'
    case 'more':
      return '/more'
  }
}

export function buildHref(route: RouteState): string {
  const parts: string[] = []
  if (route.dest === 'replay' && route.asOf) {
    parts.push(`as_of=${encodeURIComponent(route.asOf)}`)
  }
  if ((route.dest === 'market' || route.dest === 'replay') && route.panel !== 'context') {
    parts.push(`panel=${encodeURIComponent(route.panel)}`)
  }
  const qs = parts.join('&')
  return qs ? `${pathFor(route)}?${qs}` : pathFor(route)
}

export function hrefNeedsCanonicalize(pathname: string, search = ''): string | null {
  const target = buildHref(parseLocation(pathname, search))
  const currentPath = pathname.replace(/\/+$/, '') || '/'
  const currentSearch = search.startsWith('?') ? search : search ? `?${search}` : ''
  const current = `${currentPath === '/' ? '/' : currentPath}${currentSearch}`
  return current === target ? null : target
}

export function marketRoute(symbol = DEFAULT_SYMBOL, panel: SheetPanel = 'context'): RouteState {
  return { dest: 'market', symbol: normalizeSymbol(symbol), asOf: null, panel }
}

export function replayRoute(
  symbol: string,
  asOf: string | null,
  panel: SheetPanel = 'context',
): RouteState {
  return { dest: 'replay', symbol: normalizeSymbol(symbol), asOf, panel }
}

export function destRoute(dest: DestId, current: RouteState, replayHint: string | null): RouteState {
  if (dest === 'market') return marketRoute(current.symbol, current.panel)
  if (dest === 'replay') return replayRoute(current.symbol, current.asOf ?? replayHint, current.panel)
  if (dest === 'accuracy') return { dest: 'accuracy', symbol: current.symbol, asOf: null, panel: 'context' }
  if (dest === 'health') return { dest: 'health', symbol: current.symbol, asOf: null, panel: 'context' }
  return { dest: 'more', symbol: current.symbol, asOf: null, panel: 'context' }
}
