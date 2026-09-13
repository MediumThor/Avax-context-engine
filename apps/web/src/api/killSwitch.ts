export interface KillSwitchEvent {
  at: string
  kind: 'engage' | 'reset' | string
  actor: string
  reason: string
}

export interface KillSwitchState {
  engaged: boolean
  engaged_at: string | null
  reset_at: string | null
  reason: string | null
  actor: string | null
  severed_task_ids: string[]
  effects: string[]
  events: KillSwitchEvent[]
}

const base = import.meta.env.VITE_API_BASE ?? ''

async function parse(res: Response): Promise<KillSwitchState> {
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `kill switch HTTP ${res.status}`)
  }
  return res.json() as Promise<KillSwitchState>
}

export function fetchKillSwitch(): Promise<KillSwitchState> {
  return fetch(`${base}/api/v1/agents/kill-switch`).then(parse)
}

export function engageKillSwitch(reason: string, actor = 'ui'): Promise<KillSwitchState> {
  return fetch(`${base}/api/v1/agents/kill-switch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason, actor }),
  }).then(parse)
}

export function resetKillSwitch(reason: string, actor = 'ui'): Promise<KillSwitchState> {
  return fetch(`${base}/api/v1/agents/kill-switch/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason, actor }),
  }).then(parse)
}
