export const DEFAULT_SYMBOL = 'AVAXUSDT'

export const DEST_IDS = ['market', 'replay', 'accuracy', 'health', 'more'] as const
export const SECONDARY_DESTS = ['benchmarks', 'models'] as const
export type DestId = (typeof DEST_IDS)[number] | (typeof SECONDARY_DESTS)[number]

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
  benchmarks: 'Benchmarks',
  models: 'Models',
}

const SYMBOL_RE = /^[A-Z0-9]{3,20}$/

export const CHART_TFS = ['5m', '15m', '1h', '4h', '1d', '1w'] as const
export type ChartTf = (typeof CHART_TFS)[number]
export const DEFAULT_TF: ChartTf = '5m'
export const TF_MINUTES: Record<ChartTf, number> = {
  '5m': 5,
  '15m': 15,
  '1h': 60,
  '4h': 240,
  '1d': 1440,
  '1w': 10080,
}

export type RouteState = {
  dest: DestId
  symbol: string
  asOf: string | null
  panel: SheetPanel
  tf: ChartTf
}

export function normalizeSymbol(raw?: string | null): string {
  if (!raw) return DEFAULT_SYMBOL
  const up = raw.toUpperCase()
  return SYMBOL_RE.test(up) ? up : DEFAULT_SYMBOL
}

export function readPanel(raw: string | null): SheetPanel {
  return (SHEET_PANELS as readonly string[]).includes(raw ?? '') ? (raw as SheetPanel) : 'context'
}

export function readTf(raw: string | null): ChartTf {
  return (CHART_TFS as readonly string[]).includes(raw ?? '') ? (raw as ChartTf) : DEFAULT_TF
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
  const tf = readTf(rawQueryValue(search, 'tf'))
  const parts = pathname.split('/').filter(Boolean)
  const head = (parts[0] ?? '').toLowerCase()

  if (head === 'replay') {
    return { dest: 'replay', symbol: normalizeSymbol(parts[1]), asOf, panel, tf }
  }
  if (head === 'accuracy') {
    return { dest: 'accuracy', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context', tf: DEFAULT_TF }
  }
  if (head === 'health') {
    return { dest: 'health', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context', tf: DEFAULT_TF }
  }
  if (head === 'benchmarks') {
    return { dest: 'benchmarks', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context', tf: DEFAULT_TF }
  }
  if (head === 'models') {
    return { dest: 'models', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context', tf: DEFAULT_TF }
  }
  if (head === 'more' || head === 'system') {
    return { dest: 'more', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context', tf: DEFAULT_TF }
  }
  if (head === 'market' || head === '') {
    const symbol = normalizeSymbol(parts[1])
    if (asOf) return { dest: 'replay', symbol, asOf, panel, tf }
    return { dest: 'market', symbol, asOf: null, panel, tf }
  }
  return { dest: 'market', symbol: DEFAULT_SYMBOL, asOf: null, panel: 'context', tf: DEFAULT_TF }
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
    case 'benchmarks':
      return '/benchmarks'
    case 'models':
      return '/models'
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
  if ((route.dest === 'market' || route.dest === 'replay') && route.tf !== DEFAULT_TF) {
    parts.push(`tf=${encodeURIComponent(route.tf)}`)
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

export function marketRoute(
  symbol = DEFAULT_SYMBOL,
  panel: SheetPanel = 'context',
  tf: ChartTf = DEFAULT_TF,
): RouteState {
  return { dest: 'market', symbol: normalizeSymbol(symbol), asOf: null, panel, tf }
}

export function replayRoute(
  symbol: string,
  asOf: string | null,
  panel: SheetPanel = 'context',
  tf: ChartTf = DEFAULT_TF,
): RouteState {
  return { dest: 'replay', symbol: normalizeSymbol(symbol), asOf, panel, tf }
}

export function destRoute(dest: DestId, current: RouteState, replayHint: string | null): RouteState {
  if (dest === 'market') return marketRoute(current.symbol, current.panel, current.tf)
  if (dest === 'replay') return replayRoute(current.symbol, current.asOf ?? replayHint, current.panel, current.tf)
  if (dest === 'accuracy') {
    return { dest: 'accuracy', symbol: current.symbol, asOf: null, panel: 'context', tf: current.tf }
  }
  if (dest === 'health') {
    return { dest: 'health', symbol: current.symbol, asOf: null, panel: 'context', tf: current.tf }
  }
  if (dest === 'benchmarks') {
    return { dest: 'benchmarks', symbol: current.symbol, asOf: null, panel: 'context', tf: current.tf }
  }
  if (dest === 'models') {
    return { dest: 'models', symbol: current.symbol, asOf: null, panel: 'context', tf: current.tf }
  }
  return { dest: 'more', symbol: current.symbol, asOf: null, panel: 'context', tf: current.tf }
}
