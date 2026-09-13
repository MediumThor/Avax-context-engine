import { useEffect, useState } from 'react'
import { fetchBenchmarks, type BenchmarksPayload } from '../api/catalog'

export function BenchmarksView() {
  const [payload, setPayload] = useState<BenchmarksPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchBenchmarks()
      .then(setPayload)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'benchmarks unavailable'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="pageView" aria-label="Benchmarks">
      <section className="card">
        <h2>Evaluation gates</h2>
        {loading && <p className="muted">Loading registry…</p>}
        {error && <p className="killError">{error}</p>}
        {payload && <p className="muted">{payload.note}</p>}
        {payload && (
          <div className="row">
            <span>Promotion allowed</span>
            <b>{payload.promotion_allowed ? 'true' : 'false'}</b>
          </div>
        )}
      </section>
      {(payload?.entries ?? []).map((entry) => (
        <section className="card" key={entry.id}>
          <h2>{entry.title}</h2>
          <div className="row">
            <span>Id</span>
            <b>{entry.id}</b>
          </div>
          <div className="row">
            <span>Status</span>
            <b>{entry.status}</b>
          </div>
          <div className="row">
            <span>Kind</span>
            <b>{entry.kind ?? 'unknown'}</b>
          </div>
          <div className="row">
            <span>Window sealed</span>
            <b>{entry.sealed ? 'yes' : 'no'}</b>
          </div>
          <div className="row">
            <span>Window</span>
            <b>
              {entry.window_start || entry.window_end
                ? `${entry.window_start ?? 'unset'} → ${entry.window_end ?? 'unset'}`
                : 'unsealed'}
            </b>
          </div>
          <div className="row">
            <span>Validation</span>
            <b>{entry.validation ?? 'unknown'}</b>
          </div>
          <div className="row">
            <span>Random shuffle</span>
            <b>
              {entry.random_shuffle_allowed === false
                ? 'forbidden'
                : entry.random_shuffle_allowed == null
                  ? 'unknown'
                  : 'allowed'}
            </b>
          </div>
          <p className="muted">
            Named metrics: {entry.metric_ids.length ? entry.metric_ids.join(', ') : 'none'}. Names
            only — this page does not invent ECE, Brier, coverage, or MAE.
          </p>
          <p className="muted">
            Named baselines: {entry.baseline_ids.length ? entry.baseline_ids.join(', ') : 'none'}.
          </p>
          {entry.notes && <p className="muted">{entry.notes}</p>}
        </section>
      ))}
      {payload && payload.entries.length === 0 && !loading && (
        <p className="muted" role="status">
          No registry entries were returned. Gates are unknown, not passed.
        </p>
      )}
    </div>
  )
}
