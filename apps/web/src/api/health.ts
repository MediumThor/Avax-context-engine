const base = import.meta.env.VITE_API_BASE ?? ''

export interface HealthPayload {
  status: string
  mode?: string
  execution?: boolean
  kill_switch_engaged?: boolean
  source?: string
  as_of?: string | null
  data?: {
    status?: string
    age_seconds?: number | null
    last_close?: string | null
    source?: string
    error?: string
  }
}

export interface SystemPayload {
  project?: string
  execution_enabled?: boolean
  forecast_horizons?: number
  base_timeframe?: string
  prototype_branch?: string
  kill_switch_engaged?: boolean
  harness?: string
}

async function parseJson<T>(res: Response, label: string): Promise<T> {
  if (!res.ok) throw new Error(`${label} HTTP ${res.status}`)
  return res.json() as Promise<T>
}

export function fetchHealth(): Promise<HealthPayload> {
  return fetch(`${base}/health`).then((res) => parseJson<HealthPayload>(res, 'health'))
}

export function fetchSystem(): Promise<SystemPayload> {
  return fetch(`${base}/api/v1/system`).then((res) => parseJson<SystemPayload>(res, 'system'))
}
