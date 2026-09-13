import { AccuracyPanel, type AccuracySlice } from '../components/AccuracyPanel'

export function AccuracyView({
  slices,
  modelId,
  loading,
  error,
  asOf,
}: {
  slices: AccuracySlice[]
  modelId: string
  loading: boolean
  error: string | null
  asOf: string | null
}) {
  return (
    <div className="pageView" aria-label="Accuracy">
      <section className="card">
        <h2>Walk-forward scores</h2>
        <p className="muted">
          Primary accuracy destination. Scores come from journaled or walk-forward metrics already
          on the market payload. Missing values stay not yet scored. This page does not invent ECE
          or a generic accuracy percentage.
        </p>
        {asOf && <p className="muted">Market as_of {asOf}</p>}
        {loading && <p className="muted">Loading scored slices…</p>}
        {error && <p className="killError">{error}</p>}
      </section>
      <AccuracyPanel
        slices={slices}
        baselineName="drift20 vs zero"
        baselineDeltaMetric="mae"
        modelId={modelId}
        coverageInterval="q10–q90 residual vs drift20"
      />
    </div>
  )
}
