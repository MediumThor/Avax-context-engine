import type { ShadowJournalStatus } from '../api/types'

export function ShadowJournalCard({
  shadow,
  replay,
  severed,
}: {
  shadow?: ShadowJournalStatus
  replay: boolean
  severed: boolean
}) {
  if (!shadow) {
    return (
      <section
        className="card"
        data-sheet="journal"
        id="sheet-panel-journal"
        role="tabpanel"
        aria-labelledby="sheet-tab-journal"
      >
        <h2>Shadow journal</h2>
        <p className="muted" role="status">
          Shadow-journal wrote/remaining is not on this payload. Counts are unknown, not scored as
          zero and not an accuracy claim.
        </p>
      </section>
    )
  }

  const scanned = shadow.wrote > 0 || shadow.remaining > 0
  const gap = shadow.remaining > 0

  let note: string
  if (replay) {
    note = 'Replay does not write catch-up rows and does not scan remaining.'
  } else if (severed && !scanned) {
    note = 'Predictions paused. Catch-up writes are blocked and remaining was not scanned.'
  } else if (gap) {
    note =
      'Request-path catch-up is capped at 24 drift20 rows so /market stays fast. Remaining is a coverage gap, not an accuracy score.'
  } else if (shadow.wrote > 0) {
    note = 'This request reported no further mature-able 5m origins after the rows it wrote.'
  } else {
    note = 'This request reported no remaining mature-able 5m origins. That is not a promotion.'
  }

  return (
    <section
      className="card"
      data-sheet="journal"
      id="sheet-panel-journal"
      role="tabpanel"
      aria-labelledby="sheet-tab-journal"
    >
      <h2>Shadow journal</h2>
      <div className="row">
        <span>Wrote this request</span>
        <b>{shadow.wrote}</b>
      </div>
      <div className="row">
        <span>Remaining mature-able 5m origins</span>
        <b className={gap ? 'journalGap' : undefined}>{shadow.remaining}</b>
      </div>
      <div className="row">
        <span>Catch-up model</span>
        <b>{shadow.model_id}</b>
      </div>
      <p className="muted">
        {note} Existing quantile rows are not rewritten. Catch-up is baseline.drift20 only.
      </p>
    </section>
  )
}
