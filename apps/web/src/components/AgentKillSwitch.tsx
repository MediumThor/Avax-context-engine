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
          ? await engageKillSwitch('Operator pause: stop new prediction writes and recursive agent loops')
          : await resetKillSwitch('Operator resume: allow new prediction writes on main')
      onChange(next)
      setConfirm(null)
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'pause control failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={`pauseControl ${engaged ? 'paused' : ''}`} aria-label="Prediction agent pause">
      <button
        type="button"
        className={engaged ? 'pauseBtn resume' : 'pauseBtn'}
        disabled={busy}
        aria-pressed={engaged}
        aria-haspopup="dialog"
        onClick={() => setConfirm(engaged ? 'reset' : 'engage')}
      >
        {engaged ? 'Resume predictions' : 'Pause predictions'}
      </button>
      {(error || localError) && (
        <span className="killError" role="alert">
          {error || localError}
        </span>
      )}
      {confirm && (
        <div className="confirmSheet" role="dialog" aria-modal="true" aria-labelledby="pause-confirm-title">
          <div className="confirmCard">
            <h3 id="pause-confirm-title">
              {confirm === 'engage' ? 'Pause prediction agents?' : 'Resume prediction agents?'}
            </h3>
            <p>
              {confirm === 'engage'
                ? 'This stops new live forecast journal writes, blocks new loops, and freezes promotion. Journaled forecasts stay. Trading stays off. Connected agents stop cooperatively; this does not forcibly terminate an unconnected external process.'
                : 'Prediction agents may write new forecasts and run loops again. The pause/resume audit trail stays append-only.'}
            </p>
            <div className="killActions">
              <button
                type="button"
                className={confirm === 'engage' ? 'danger' : 'ghost'}
                disabled={busy}
                onClick={() => run(confirm)}
              >
                {confirm === 'engage' ? 'Yes, pause them' : 'Yes, resume'}
              </button>
              <button type="button" className="quiet" disabled={busy} onClick={() => setConfirm(null)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
