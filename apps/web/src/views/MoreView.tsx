import type { SystemPayload } from '../api/health'
import type { ShadowJournalStatus } from '../api/types'
import type { DestId } from '../nav/destinations'

export function MoreView({
  system,
  shadow,
  loading,
  error,
  onNavigate,
}: {
  system: SystemPayload | null
  shadow?: ShadowJournalStatus
  loading: boolean
  error: string | null
  onNavigate?: (dest: DestId) => void
}) {
  return (
    <div className="pageView" aria-label="More">
      <section className="card">
        <h2>Operations</h2>
        {loading && <p className="muted">Loading system…</p>}
        {error && <p className="killError">{error}</p>}
        <p>
          AVAX Context Engine is a research and decision-support instrument. Execution stays off in
          v1. Pause predictions remains in the header on every destination.
        </p>
        <div className="row">
          <span>Execution</span>
          <b>{system?.execution_enabled === false ? 'off' : system ? String(system.execution_enabled) : 'unknown'}</b>
        </div>
        <div className="row">
          <span>Forecast horizons</span>
          <b>{system?.forecast_horizons ?? 'unknown'}</b>
        </div>
        <div className="row">
          <span>Harness</span>
          <b>{system?.harness ?? 'unknown'}</b>
        </div>
        <div className="row">
          <span>Kill switch</span>
          <b>{system?.kill_switch_engaged ? 'engaged' : system ? 'open' : 'unknown'}</b>
        </div>
      </section>
      <section className="card">
        <h2>Journal coverage</h2>
        {!shadow && (
          <p className="muted">
            Shadow-journal remaining is not on this payload. The count is unknown, not zero, and not
            an accuracy claim.
          </p>
        )}
        {shadow && (
          <>
            <div className="row">
              <span>Wrote this request</span>
              <b>{shadow.wrote}</b>
            </div>
            <div className="row">
              <span>Remaining</span>
              <b>{shadow.remaining}</b>
            </div>
            <div className="row">
              <span>Catch-up model</span>
              <b>{shadow.model_id}</b>
            </div>
            <p className="muted">
              Remaining is a coverage gap of mature-able 5m origins. Drain from the Market Journal
              sheet. Catch-up writes baseline.drift20 only and is not a promotion.
            </p>
          </>
        )}
      </section>
      <section className="card">
        <h2>Catalog</h2>
        <p className="muted">
          These are secondary destinations. They are not a sixth bottom-nav item. They name gates
          and model roles. They do not invent ECE or promote a challenger.
        </p>
        <div className="row">
          <button type="button" className="quiet" onClick={() => onNavigate?.('benchmarks')}>
            Benchmarks
          </button>
          <button type="button" className="quiet" onClick={() => onNavigate?.('models')}>
            Models
          </button>
        </div>
      </section>
    </div>
  )
}
