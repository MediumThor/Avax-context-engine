import { useEffect, useState } from 'react'
import { fetchModels, type ModelsPayload } from '../api/catalog'

export function ModelsView() {
  const [payload, setPayload] = useState<ModelsPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchModels()
      .then(setPayload)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'models unavailable'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="pageView" aria-label="Models">
      <section className="card">
        <h2>Incumbent and research models</h2>
        {loading && <p className="muted">Loading model catalog…</p>}
        {error && <p className="killError">{error}</p>}
        {payload && <p className="muted">{payload.note}</p>}
        {payload && (
          <>
            <div className="row">
              <span>Feature schema</span>
              <b>{payload.feature_schema}</b>
            </div>
            <div className="row">
              <span>Promotion allowed</span>
              <b>{payload.promotion_allowed ? 'true' : 'false'}</b>
            </div>
            <div className="row">
              <span>Execution</span>
              <b>{payload.execution_enabled ? 'on' : 'off'}</b>
            </div>
          </>
        )}
      </section>
      {payload && (
        <section className="card">
          <h2>Incumbent</h2>
          <div className="row">
            <span>Model</span>
            <b>{payload.incumbent.model_id}</b>
          </div>
          <div className="row">
            <span>Role</span>
            <b>{payload.incumbent.role}</b>
          </div>
          <p className="muted">{payload.incumbent.notes}</p>
        </section>
      )}
      {(payload?.research ?? []).map((row) => (
        <section className="card" key={row.model_id}>
          <h2>Research</h2>
          <div className="row">
            <span>Model</span>
            <b>{row.model_id}</b>
          </div>
          <div className="row">
            <span>Role</span>
            <b>{row.role}</b>
          </div>
          <p className="muted">{row.notes}</p>
        </section>
      ))}
    </div>
  )
}
