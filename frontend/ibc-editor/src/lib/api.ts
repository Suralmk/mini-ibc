function resolveApiBase(): string {
  const raw = import.meta.env.VITE_API_BASE

  if (raw === '') return ''

  const fallback = 'http://127.0.0.1:8000'
  const configured =
    raw === undefined || raw === null ? fallback : String(raw).replace(/\/$/, '')

  if (!configured) return ''

  if (typeof window !== 'undefined') {
    const pageHost = window.location.hostname
    if (pageHost && pageHost !== 'localhost' && pageHost !== '127.0.0.1') {
      try {
        const u = new URL(configured)
        if (u.hostname === 'localhost' || u.hostname === '127.0.0.1') {
          u.hostname = pageHost
          return u.origin
        }
      } catch {
        /* ignore */
      }
    }
  }

  return configured
}

export const API_BASE = resolveApiBase()

export type AnimationStyle =
  | 'fade'
  | 'zoom'
  | 'slide'
  | 'typewriter'
  | 'pulse'

export type GraphicKind = 'title' | 'lower_third' | 'stats'
export type MatchPeriod = '1H' | 'HT' | '2H' | 'ET' | 'FT'

export type GraphicPayload = {
  kind?: GraphicKind
  text?: string
  title?: string
  subtitle?: string
  line3?: string
  duration: number
  style?: AnimationStyle
  home_possession?: number
  away_possession?: number
  home_shots?: number
  away_shots?: number
  home_on_target?: number
  away_on_target?: number
  home_label?: string
  away_label?: string
  data_source?: string
}

export type MatchState = {
  home_team: string
  away_team: string
  home_score: number
  away_score: number
  score: string
  period: MatchPeriod
  clock_minute: number
  stoppage: number
  clock: string
}

export function wsStreamUrl() {
  if (!API_BASE) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${window.location.host}/ws/stream`
  }
  const base = API_BASE.replace(/^http/, 'ws')
  return `${base}/ws/stream`
}

async function parseJson<T>(res: Response): Promise<T> {
  const data = await res.json()
  if (!res.ok) {
    const detail = data.detail
    if (typeof detail === 'string') throw new Error(detail)
    if (Array.isArray(detail)) {
      throw new Error(detail.map((d: { msg?: string }) => d.msg).join(', '))
    }
    throw new Error('Request failed')
  }
  return data as T
}

export async function pushGraphic(payload: GraphicPayload) {
  const res = await fetch(`${API_BASE}/graphics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kind: 'title', style: 'pulse', ...payload }),
  })
  return parseJson<{
    ok: boolean
    kind: GraphicKind
    text?: string
    title?: string
    style?: AnimationStyle
    duration: number
    message: string
  }>(res)
}

export async function getActiveGraphic() {
  const res = await fetch(`${API_BASE}/graphics/active`)
  return parseJson<{
    active: boolean
    kind?: GraphicKind
    text?: string
    title?: string
    subtitle?: string
    style?: AnimationStyle
    duration?: number
    remaining?: number
  }>(res)
}

export async function getMatch() {
  const res = await fetch(`${API_BASE}/match`)
  return parseJson<MatchState>(res)
}

export async function updateMatch(
  patch: Partial<{
    home_team: string
    away_team: string
    home_score: number
    away_score: number
    period: MatchPeriod
    clock_minute: number
    stoppage: number
  }>,
) {
  const res = await fetch(`${API_BASE}/match`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
  return parseJson<MatchState>(res)
}

export async function addGoal(side: 'home' | 'away', announce = true) {
  const res = await fetch(`${API_BASE}/match/goal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ side, announce }),
  })
  return parseJson<MatchState>(res)
}
