import { useState } from 'react'
import { engageKillSwitch, resetKillSwitch, type KillSwitchState } from '../api/killSwitch'

interface Props {
  state: KillSwitchState | null
  error: string | null
  onChange: (next: KillSwitchState) => void
}

export function AgentKillSwitch({ state, error, onChange }: Props) {
  const [busy, setBusy] = useState(false)
  const [confirm, setConfirm] = useState<'engage' | 'reset' | null>(null)
  const [localError, setLocalError] = useState<string | null>(null)
  const engaged = Boolean(state?.engaged)

  async function run(kind: 'engage' | 'reset') {
    setBusy(true)
    setLocalError(null)
    try {
      const next =
        kind === 'engage'
          ? await engageKillSwitch('Operator kill switch: sever all recursive agent work')
          : await resetKillSwitch('Operator reset: resume prototype on main')
      onChange(next)
      setConfirm(null)
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'kill switch failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className={`killSwitch ${engaged ? 'engaged' : ''}`} aria-label="Recursive agent kill switch">
      <div className="killCopy">
        <span className="eyebrow">{engaged ? 'Agents severed' : 'Recursive agents'}</span>
        <strong>{engaged ? 'KILL SWITCH ENGAGED' : 'Prototype on main'}</strong>
        <p>
          {engaged
            ? `All RLH / wave-1 agent work is halted. ${state?.severed_task_ids.length ?? 0} tasks severed. Journal and forecasts stay.`
            : 'One line of work on main. This switch severs every recursive agent immediately.'}
        </p>
        {(error || localError) && <p className="killError">{error || localError}</p>}
      </div>
      <div className="killActions">
        {!engaged && (
          <button type="button" className="danger" disabled={busy} onClick={() => setConfirm('engage')}>
            Kill all agents
          </button>
        )}
        {engaged && (
          <button type="button" className="ghost" disabled={busy} onClick={() => setConfirm('reset')}>
            Reset switch
          </button>
        )}
      </div>
      {confirm && (
        <div className="confirm" role="dialog" aria-modal="true" aria-labelledby="kill-confirm-title">
          <h3 id="kill-confirm-title">
            {confirm === 'engage' ? 'Sever all recursive agent work?' : 'Reset the kill switch?'}
          </h3>
          <p>
            {confirm === 'engage'
              ? 'This halts new loops, freezes promotion, and marks every launched agent task severed. It does not delete journals or turn on trading.'
              : 'Agents may run again on main. The engage/reset audit trail stays append-only.'}
          </p>
          <div className="killActions">
            <button type="button" className={confirm === 'engage' ? 'danger' : 'ghost'} disabled={busy} onClick={() => run(confirm)}>
              {confirm === 'engage' ? 'Yes, sever them' : 'Yes, reset'}
            </button>
            <button type="button" className="quiet" disabled={busy} onClick={() => setConfirm(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </section>
  )
}
