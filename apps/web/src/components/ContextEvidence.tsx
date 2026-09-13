import type { AnalogMatch, FibLevelSummary, PatternHypothesisSummary } from '../api/types'

function shortTime(iso: string): string {
  return iso.replace('+00:00', 'Z').replace('T', ' ').slice(0, 16)
}

export function ContextEvidence({
  analogs,
  patterns,
  fibLevels,
}: {
  analogs: AnalogMatch[]
  patterns: PatternHypothesisSummary[]
  fibLevels: FibLevelSummary[]
}) {
  return (
    <>
      <section className="card">
        <h2>Analog matches</h2>
        <p className="muted">
          Prior prefixes whose h=10 close is already known at T. Distance is fingerprint proximity, not confidence
          and not a forecast.
        </p>
        {analogs.length === 0 && <p className="muted">No matured analog origins at this as_of.</p>}
        {analogs.map((row) => (
          <div className="row analogRow" key={`${row.origin_close_time}-${row.known_at}`}>
            <span>{shortTime(row.origin_close_time)}</span>
            <span className="muted">
              d={row.distance.toFixed(4)} · realized h10 {row.realized_h10_log_return.toFixed(4)} · known{' '}
              {shortTime(row.known_at)}
            </span>
          </div>
        ))}
      </section>
      <section className="card">
        <h2>Pattern hypotheses</h2>
        <p className="muted">Competing labels. evidence_count_v1 is a count, not a calibrated percent.</p>
        {patterns.length === 0 && <p className="muted">No competing pattern hypotheses at T.</p>}
        {patterns.map((hyp) => (
          <div className="row" key={hyp.id}>
            <span>
              {hyp.kind} · {hyp.status}
            </span>
            <span className="muted">
              {hyp.timeframe} · score {hyp.evidence_score} · {hyp.score_provenance}
            </span>
          </div>
        ))}
      </section>
      <section className="card">
        <h2>Fib features</h2>
        <p className="muted">Candidate prices from confirmed swings. Not guaranteed support or resistance.</p>
        {fibLevels.length === 0 && <p className="muted">No fib candidate levels at T.</p>}
        {fibLevels.map((level) => (
          <div className="row" key={`${level.kind}-${level.ratio}-${level.price}-${level.known_at}`}>
            <span>
              {level.kind} {level.ratio}
            </span>
            <span className="muted">
              {level.price.toFixed(3)} · {level.direction} · {level.status}
            </span>
          </div>
        ))}
      </section>
    </>
  )
}
