export interface BenchmarkEntry {
  id: string
  title: string
  status: string
  kind?: string
  dataset_id?: string
  dataset_ref?: string | null
  sealed: boolean
  window_start?: string | null
  window_end?: string | null
  baseline_ids: string[]
  metric_ids: string[]
  validation?: string | null
  random_shuffle_allowed?: boolean | null
  notes?: string | null
}

export interface BenchmarksPayload {
  available: boolean
  promotion_allowed: boolean
  execution_enabled: boolean
  note: string
  entries: BenchmarkEntry[]
}

export interface ModelRole {
  model_id: string
  role: string
  promotion_allowed: boolean
  notes: string
}

export interface ModelsPayload {
  available: boolean
  promotion_allowed: boolean
  execution_enabled: boolean
  feature_schema: string
  incumbent: ModelRole
  research: ModelRole[]
  note: string
}

const base = import.meta.env.VITE_API_BASE ?? ''

export async function fetchBenchmarks(): Promise<BenchmarksPayload> {
  const res = await fetch(`${base}/api/v1/benchmarks`)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<BenchmarksPayload>
}

export async function fetchModels(): Promise<ModelsPayload> {
  const res = await fetch(`${base}/api/v1/models`)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<ModelsPayload>
}
