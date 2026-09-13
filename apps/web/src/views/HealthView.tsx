import { useEffect, useState } from 'react'
import { fetchHealth, fetchSystem, type HealthPayload, type SystemPayload } from '../api/health'

export function HealthView() {
  const [health, setHealth] = useState<HealthPayload | null>(null)
  const [system, setSystem] = useState<SystemPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([fetchHealth(), fetchSystem()])
      .then(([nextHealth, nextSystem]) => {
        setHealth(nextHealth)
        setSystem(nextSystem)
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'health unavailable'))
      .finally(() => setLoading(false))
  }, [])

  const data = health?.data
  const executionOff = health?.execution === false && system?.execution_enabled === false

  return (
    <div className="pageView" aria-label="Health">
      <section className="card">
        <h2>Service health</h2>
        {loading && <p className="muted">Loading /health and /api/v1/system…</p>}
        {error && <p className="killError">{error}</p>}
        {!loading && !error && !health && (
          <p className="muted" role="status">
            Health payload is missing. Status is unknown, not scored as healthy.
          </p>
        )}
        {health && (
          <>
            <div className="row">
              <span>Status</span>
              <b>{health.status}</b>
            </div>
            <div className="row">
              <span>Mode</span>
              <b>{health.mode ?? 'unknown'}</b>
            </div>
            <div className="row">
              <span>Execution</span>
              <b>{health.execution === false ? 'off' : health.execution === true ? 'on' : 'unknown'}</b>
            </div>
            <div className="row">
              <span>Kill switch</span>
              <b>{health.kill_switch_engaged ? 'engaged' : 'open'}</b>
            </div>
            <div className="row">
              <span>Source</span>
              <b>{health.source ?? data?.source ?? 'unknown'}</b>
            </div>
            <div className="row">
              <span>Last close</span>
              <b>{health.as_of ?? data?.last_close ?? 'unknown'}</b>
            </div>
            <div className="row">
              <span>Data status</span>
              <b>{data?.status ?? 'unknown'}</b>
            </div>
            <div className="row">
              <span>Age (seconds)</span>
              <b>{data?.age_seconds == null ? 'unknown' : String(data.age_seconds)}</b>
            </div>
            {data?.error && <p className="killError">{data.error}</p>}
          </>
        )}
        <p className="muted">
          This page reports service and data freshness only. It does not invent Brier, ECE, coverage,
          or forecast accuracy.
        </p>
      </section>
      <section className="card">
        <h2>System</h2>
        {!system && !loading && <p className="muted">System payload is missing.</p>}
        {system && (
          <>
            <div className="row">
              <span>Project</span>
              <b>{system.project ?? 'unknown'}</b>
            </div>
            <div className="row">
              <span>Harness</span>
              <b>{system.harness ?? 'unknown'}</b>
            </div>
            <div className="row">
              <span>Horizons</span>
              <b>{system.forecast_horizons ?? 'unknown'}</b>
            </div>
            <div className="row">
              <span>Base TF</span>
              <b>{system.base_timeframe ?? 'unknown'}</b>
            </div>
            <div className="row">
              <span>Branch</span>
              <b>{system.prototype_branch ?? 'unknown'}</b>
            </div>
            <div className="row">
              <span>Execution enabled</span>
              <b>{system.execution_enabled === false ? 'false' : String(system.execution_enabled)}</b>
            </div>
          </>
        )}
        {executionOff && (
          <p className="muted">v1 is read-only. Real trade execution stays off.</p>
        )}
      </section>
    </div>
  )
}
