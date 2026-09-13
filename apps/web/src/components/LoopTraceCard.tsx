import type { LoopSummary } from '../api/types'

export function LoopTraceCard({ loop }: { loop: LoopSummary }) {
  return (
    <section className="card">
      <h2>Harness loop</h2>
      <p className="muted">
        {loop.note ||
          'Bounded retrieve after the forecast is journaled. Analog count is a retrieval size, not confidence.'}
      </p>
      {loop.ran ? (
        <>
          <div className="row">
            <span>Halt</span>
            <b>{loop.halt_reason ?? 'unknown'}</b>
          </div>
          <div className="row">
            <span>Analogs read</span>
            <b>{loop.analog_count ?? 0}</b>
          </div>
          <div className="row">
            <span>Hypotheses</span>
            <b>{(loop.hypothesis_ids ?? []).length}</b>
          </div>
          <div className="row">
            <span>Trace</span>
            <b>{loop.persisted ? 'journaled' : 'not stored'}</b>
          </div>
          {(loop.hypothesis_ids ?? []).length > 0 && (
            <p className="muted">{loop.hypothesis_ids?.join(', ')}</p>
          )}
        </>
      ) : (
        <p className="muted">Loop did not run{loop.reason ? `: ${loop.reason}` : '.'}</p>
      )}
    </section>
  )
}
