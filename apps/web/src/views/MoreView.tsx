import type { SystemPayload } from '../api/health'
import type { ShadowJournalStatus } from '../api/types'

export function MoreView({
  system,
  shadow,
  loading,
  error,
}: {
  system: SystemPayload | null
  shadow?: ShadowJournalStatus
  loading: boolean
  error: string | null
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
        <h2>Not in this shell</h2>
        <p className="muted">
          /benchmarks and /models are listed in the navigation directive and are not implemented
          here. Missing destinations are absent, not scored. Do not treat this page as calibration
          evidence.
        </p>
      </section>
    </div>
  )
}
