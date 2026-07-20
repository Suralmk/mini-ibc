import { useEffect, useState } from 'react'
import {
  addGoal,
  getActiveGraphic,
  getMatch,
  pushGraphic,
  updateMatch,
  type MatchState,
} from './lib/api'
import { useWorldFeed } from './lib/useWorldFeed'

const PRESETS = ['FIFA', 'GOAL', 'KICK OFF', 'WORLD CUP'] as const

const emptyMatch: MatchState = {
  home_team: 'HOME',
  away_team: 'AWAY',
  home_score: 0,
  away_score: 0,
  score: '0-0',
}

export default function App() {
  const [duration, setDuration] = useState(4)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const [active, setActive] = useState<string | null>(null)
  const [match, setMatch] = useState<MatchState>(emptyMatch)
  const [goalBusy, setGoalBusy] = useState(false)
  const { frameUrl, connected } = useWorldFeed()

  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const [g, m] = await Promise.all([getActiveGraphic(), getMatch()])
        setMatch(m)
        if (g.active && g.text) {
          setActive(`${g.text} · ${g.remaining?.toFixed(1) ?? '?'}s left`)
        } else {
          setActive(null)
        }
      } catch {
        /* ignore poll errors */
      }
    }, 500)
    return () => clearInterval(id)
  }, [])

  async function send(text: string) {
    setSending(true)
    setError('')
    setStatus('Pushing to IBC…')
    try {
      const res = await pushGraphic({
        text,
        duration,
        style: 'pulse',
      })
      setStatus(`On air: "${res.text}" · pulse · ${res.duration}s`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Send failed')
      setStatus('')
    } finally {
      setSending(false)
    }
  }

  async function onGoal(side: 'home' | 'away') {
    setGoalBusy(true)
    setError('')
    try {
      const m = await addGoal(side, true)
      setMatch(m)
      setStatus(`Goal ${side} → ${m.score} burned into stream`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Goal failed')
    } finally {
      setGoalBusy(false)
    }
  }

  async function onScoreChange(side: 'home' | 'away', value: number) {
    try {
      const m = await updateMatch(
        side === 'home' ? { home_score: value } : { away_score: value },
      )
      setMatch(m)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Score update failed')
    }
  }

  async function onTeamChange(side: 'home' | 'away', value: string) {
    try {
      const m = await updateMatch(
        side === 'home' ? { home_team: value } : { away_team: value },
      )
      setMatch(m)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Team update failed')
    }
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#f5f5f5] text-[#1a1a1a]">
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-[#e5e5e5] bg-white px-3">
        <div className="flex items-center gap-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#0d99ff] text-xs font-bold text-white">
            IBC
          </div>
          <div>
            <p className="text-sm font-medium leading-none text-[#111]">
              Graphics Desk
            </p>
            <p className="text-[10px] text-[#6b7280]">Program canvas</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`rounded-full px-2.5 py-1 ${
              connected
                ? 'bg-[#ecfdf5] text-[#059669]'
                : 'bg-[#fef2f2] text-[#dc2626]'
            }`}
          >
            {connected ? 'WS live' : 'WS down'}
          </span>
          {active && (
            <span className="hidden rounded-full bg-[#fff7ed] px-2.5 py-1 text-[#c2410c] sm:inline">
              {active}
            </span>
          )}
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="flex w-[280px] shrink-0 flex-col border-r border-[#e5e5e5] bg-white">
          <div className="border-b border-[#ebebeb] px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
            Layers · Titles
          </div>
          <div className="flex-1 space-y-4 overflow-y-auto p-3">
            <label className="block space-y-1">
              <span className="text-[11px] uppercase tracking-wider text-[#6b7280]">
                Duration (sec)
              </span>
              <input
                type="number"
                min={0.5}
                max={30}
                step={0.5}
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="w-full rounded-md border border-[#d1d5db] bg-white px-2.5 py-2 text-sm outline-none focus:border-[#0d99ff]"
              />
            </label>
            <p className="text-xs text-[#6b7280]">
              Animation is always <strong className="text-[#374151]">pulse</strong>{' '}
              — no background plate on the feed.
            </p>

            <div>
              <p className="mb-2 text-[11px] uppercase tracking-wider text-[#6b7280]">
                Presets
              </p>
              <div className="flex flex-col gap-1.5">
                {PRESETS.map((label) => (
                  <button
                    key={label}
                    type="button"
                    disabled={sending}
                    onClick={() => void send(label)}
                    className="rounded-md border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2 text-left text-sm text-[#111] hover:border-[#0d99ff] disabled:opacity-50"
                  >
                    {label}
                    <span className="ml-2 text-[11px] text-[#9ca3af]">pulse</span>
                  </button>
                ))}
              </div>
            </div>

            {(status || error) && (
              <div className="rounded-md border border-[#e5e7eb] bg-[#f9fafb] p-2 text-xs">
                {status && <p className="text-[#059669]">{status}</p>}
                {error && <p className="text-[#dc2626]">{error}</p>}
              </div>
            )}
          </div>
        </aside>

        <main className="relative flex min-w-0 flex-1 flex-col bg-[#f0f0f0]">
          <div className="flex h-9 shrink-0 items-center justify-center border-b border-[#e5e5e5] bg-white text-[11px] text-[#6b7280]">
            World feed · 1280×720 · WebSocket
          </div>
          <div className="flex flex-1 items-center justify-center overflow-auto p-6">
            <div className="relative w-full max-w-4xl overflow-hidden rounded-lg border border-[#e5e7eb] bg-black shadow-[0_8px_30px_rgba(0,0,0,0.08)]">
              <div className="absolute left-2 top-2 z-10 rounded bg-white/90 px-2 py-0.5 text-[10px] uppercase tracking-wider text-[#374151]">
                Canvas
              </div>
              <div className="aspect-video">
                {connected && frameUrl ? (
                  <img
                    src={frameUrl}
                    alt="IBC program preview"
                    className="h-full w-full object-contain"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-[#9ca3af]">
                    No signal from IBC server
                  </div>
                )}
              </div>
              <div className="border-t border-[#e5e7eb] bg-white px-3 py-1.5 text-center text-xs text-[#4b5563]">
                {match.home_team} {match.home_score} – {match.away_score}{' '}
                {match.away_team}
              </div>
            </div>
          </div>
        </main>

        <aside className="flex w-[300px] shrink-0 flex-col border-l border-[#e5e5e5] bg-white">
          <div className="border-b border-[#ebebeb] px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
            Design · Match
          </div>
          <div className="flex-1 space-y-5 overflow-y-auto p-3">
            <section className="space-y-3">
              <p className="text-[11px] uppercase tracking-wider text-[#6b7280]">
                Scorebug (live on stream)
              </p>
              <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-3">
                <div className="mb-3 text-center text-2xl font-semibold tracking-wide text-[#111]">
                  {match.home_score}
                  <span className="mx-2 text-[#9ca3af]">–</span>
                  {match.away_score}
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <label className="space-y-1">
                    <span className="text-[10px] uppercase text-[#6b7280]">Home</span>
                    <input
                      value={match.home_team}
                      onChange={(e) =>
                        setMatch((m) => ({ ...m, home_team: e.target.value }))
                      }
                      onBlur={(e) => void onTeamChange('home', e.target.value)}
                      className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                    />
                  </label>
                  <label className="space-y-1">
                    <span className="text-[10px] uppercase text-[#6b7280]">Away</span>
                    <input
                      value={match.away_team}
                      onChange={(e) =>
                        setMatch((m) => ({ ...m, away_team: e.target.value }))
                      }
                      onBlur={(e) => void onTeamChange('away', e.target.value)}
                      className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                    />
                  </label>
                </div>

                <div className="mt-3 grid grid-cols-2 gap-2">
                  <label className="space-y-1">
                    <span className="text-[10px] uppercase text-[#6b7280]">
                      Home score
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={99}
                      value={match.home_score}
                      onChange={(e) =>
                        void onScoreChange('home', Number(e.target.value))
                      }
                      className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                    />
                  </label>
                  <label className="space-y-1">
                    <span className="text-[10px] uppercase text-[#6b7280]">
                      Away score
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={99}
                      value={match.away_score}
                      onChange={(e) =>
                        void onScoreChange('away', Number(e.target.value))
                      }
                      className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                    />
                  </label>
                </div>
              </div>
            </section>

            <section className="space-y-2">
              <p className="text-[11px] uppercase tracking-wider text-[#6b7280]">
                Goal editor
              </p>
              <p className="text-xs text-[#6b7280]">
                Adds a goal, updates the scorebug on the world feed, and
                flashes a GOAL title.
              </p>
              <button
                type="button"
                disabled={goalBusy}
                onClick={() => void onGoal('home')}
                className="w-full rounded-md bg-[#e11d48] px-3 py-2.5 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
              >
                Goal · {match.home_team}
              </button>
              <button
                type="button"
                disabled={goalBusy}
                onClick={() => void onGoal('away')}
                className="w-full rounded-md bg-[#2563eb] px-3 py-2.5 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
              >
                Goal · {match.away_team}
              </button>
            </section>
          </div>
        </aside>
      </div>
    </div>
  )
}
