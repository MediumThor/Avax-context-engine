import { DEST_IDS, DEST_LABELS, type DestId, type RouteState } from './destinations'

export function DestNav({
  route,
  onNavigate,
  journalGap = null,
}: {
  route: RouteState
  onNavigate: (dest: DestId) => void
  journalGap?: number | null
}) {
  return (
    <nav className="destNav" aria-label="Primary destinations">
      {DEST_IDS.map((id) => {
        const selected = route.dest === id
        return (
          <button
            key={id}
            type="button"
            className="destBtn"
            aria-current={selected ? 'page' : undefined}
            onClick={() => onNavigate(id)}
          >
            <span>{DEST_LABELS[id]}</span>
            {id === 'market' && journalGap != null && (
              <span className="sheetBadge" aria-label={`${journalGap} remaining journal origins`}>
                {journalGap}
              </span>
            )}
          </button>
        )
      })}
    </nav>
  )
}
