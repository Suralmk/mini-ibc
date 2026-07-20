function resolveApiBase(): string {
  const raw = import.meta.env.VITE_API_BASE

  // Docker / nginx same-origin
  if (raw === '') return ''

  const fallback = 'http://127.0.0.1:8000'
  const configured =
    raw === undefined || raw === null ? fallback : String(raw).replace(/\/$/, '')

  if (!configured) return ''

  // Phone/LAN: page is http://192.168.x.x:5174 but .env says 127.0.0.1
  // → rewrite API host to the machine's LAN IP from the address bar
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

export function wsStreamUrl() {
  if (!API_BASE) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${window.location.host}/ws/stream`
  }
  const base = API_BASE.replace(/^http/, 'ws')
  return `${base}/ws/stream`
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('IBC offline')
  return res.json() as Promise<{
    status: string
    home: string
    away: string
    score: string
    home_score: number
    away_score: number
    period?: string
    clock?: string
    graphic_active: boolean
    graphic_kind?: string | null
  }>
}
