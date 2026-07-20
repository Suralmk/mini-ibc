import { useEffect, useState } from 'react'
import {
  addGoal,
  getActiveGraphic,
  getMatch,
  pushGraphic,
  updateMatch,
  type MatchPeriod,
  type MatchState,
} from './lib/api'
import { useWorldFeed } from './lib/useWorldFeed'

const PRESETS = ['FIFA', 'GOAL', 'KICK OFF', 'WORLD CUP'] as const
const PERIODS: MatchPeriod[] = ['1H', 'HT', '2H', 'ET', 'FT']

const LT_PRESETS = [
  {
    label: 'Messi',
    title: 'Lionel Messi',
    subtitle: 'Argentina',
    line3: '3 Goals in Tournament',
  },
  {
    label: 'Coach',
    title: 'Lionel Scaloni',
    subtitle: 'Head Coach · Argentina',
    line3: '',
  },
  {
    label: 'Referee',
    title: 'Szymon Marciniak',
    subtitle: 'Referee · Poland',
    line3: '',
  },
  {
    label: 'Interview',
    title: 'Post-Match Interview',
    subtitle: 'Mixed Zone',
    line3: 'Breaking · Exclusive',
  },
] as const

const emptyMatch: MatchState = {
  home_team: 'HOME',
  away_team: 'AWAY',
  home_score: 0,
  away_score: 0,
  score: '0-0',
  period: '1H',
  clock_minute: 0,
  stoppage: 0,
  clock: "0'",
}

export default function App() {
  const [duration, setDuration] = useState(5)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const [active, setActive] = useState<string | null>(null)
  const [match, setMatch] = useState<MatchState>(emptyMatch)
  const [goalBusy, setGoalBusy] = useState(false)

  // Lower third form
  const [ltTitle, setLtTitle] = useState('Lionel Messi')
  const [ltSubtitle, setLtSubtitle] = useState('Argentina')
  const [ltLine3, setLtLine3] = useState('3 Goals in Tournament')

  // Stats form (FIFA-style card)
  const [possHome, setPossHome] = useState(58)
  const [shotsHome, setShotsHome] = useState(16)
  const [shotsAway, setShotsAway] = useState(0)
  const [onTargetHome, setOnTargetHome] = useState(11)
  const [onTargetAway, setOnTargetAway] = useState(0)

  const { frameUrl, connected } = useWorldFeed()
  const possAway = 100 - possHome

  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const [g, m] = await Promise.all([getActiveGraphic(), getMatch()])
        setMatch(m)
        if (g.active) {
          const label = g.text || g.title || g.kind || 'overlay'
          setActive(`${label} · ${g.remaining?.toFixed(1) ?? '?'}s`)
        } else {
          setActive(null)
        }
      } catch {
        /* ignore poll errors */
      }
    }, 500)
    return () => clearInterval(id)
  }, [])

  async function sendTitle(text: string) {
    setSending(true)
    setError('')
    setStatus('Pushing title…')
    try {
      const res = await pushGraphic({
        kind: 'title',
        text,
        duration,
        style: 'pulse',
      })
      setStatus(`On air: "${res.text}" · ${res.duration}s`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Send failed')
      setStatus('')
    } finally {
      setSending(false)
    }
  }

  async function sendLowerThird() {
    setSending(true)
    setError('')
    setStatus('Pushing lower third…')
    try {
      const res = await pushGraphic({
        kind: 'lower_third',
        title: ltTitle,
        subtitle: ltSubtitle,
        line3: ltLine3,
        duration: Math.max(duration, 6),
      })
      setStatus(`Lower third: "${res.title}" · ${res.duration}s`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Lower third failed')
      setStatus('')
    } finally {
      setSending(false)
    }
  }

  async function sendStats() {
    setSending(true)
    setError('')
    setStatus('Pushing match stats…')
    try {
      const res = await pushGraphic({
        kind: 'stats',
        duration: Math.max(duration, 7),
        home_possession: possHome,
        away_possession: possAway,
        home_shots: shotsHome,
        away_shots: shotsAway,
        home_on_target: onTargetHome,
        away_on_target: onTargetAway,
        home_label: match.home_team,
        away_label: match.away_team,
        data_source: 'Opta / Stats Perform / FIFA',
      })
      setStatus(`Stats on air · ${res.duration}s`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Stats failed')
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
      setStatus(`Goal ${side} → ${m.score}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Goal failed')
    } finally {
      setGoalBusy(false)
    }
  }

  async function patchMatch(
    patch: Parameters<typeof updateMatch>[0],
  ): Promise<void> {
    try {
      const m = await updateMatch(patch)
      setMatch(m)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Match update failed')
    }
  }

  async function startET() {
    await patchMatch({ period: 'ET', clock_minute: 90, stoppage: 0 })
    setStatus('Extra time started · 90\'')
  }

  async function bumpStoppage() {
    await patchMatch({ stoppage: match.stoppage + 1 })
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#f5f5f5] text-[#1a1a1a]">
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-[#e5e5e5] bg-white px-3">
        <div className="flex items-center gap-3">
          <div className="flex h-7 items-center justify-center rounded-md bg-[#0d99ff] px-1.5 text-[10px] font-bold tracking-tight text-white">
            MINI IBC
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
            <span className="hidden max-w-[220px] truncate rounded-full bg-[#fff7ed] px-2.5 py-1 text-[#c2410c] sm:inline">
              {active}
            </span>
          )}
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        {/* Left rail */}
        <aside className="flex w-[300px] shrink-0 flex-col border-r border-[#e5e5e5] bg-white">
          <div className="border-b border-[#ebebeb] px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
            Overlays
          </div>
          <div className="flex-1 space-y-5 overflow-y-auto p-3">
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

            {/* Titles */}
            <section>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
                1 · Titles
              </p>
              <div className="flex flex-col gap-1.5">
                {PRESETS.map((label) => (
                  <button
                    key={label}
                    type="button"
                    disabled={sending}
                    onClick={() => void sendTitle(label)}
                    className="rounded-md border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2 text-left text-sm text-[#111] transition hover:border-[#0d99ff] hover:bg-white disabled:opacity-50"
                  >
                    {label}
                    <span className="ml-2 text-[11px] text-[#9ca3af]">pulse</span>
                  </button>
                ))}
              </div>
            </section>

            {/* Lower third */}
            <section className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
                2 · Lower third
              </p>
              <div className="flex flex-wrap gap-1">
                {LT_PRESETS.map((p) => (
                  <button
                    key={p.label}
                    type="button"
                    onClick={() => {
                      setLtTitle(p.title)
                      setLtSubtitle(p.subtitle)
                      setLtLine3(p.line3)
                    }}
                    className="rounded-full border border-[#e5e7eb] bg-white px-2.5 py-1 text-[11px] text-[#374151] hover:border-[#0d99ff]"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
              <input
                value={ltTitle}
                onChange={(e) => setLtTitle(e.target.value)}
                placeholder="Name"
                className="w-full rounded-md border border-[#d1d5db] px-2.5 py-2 text-sm outline-none focus:border-[#0d99ff]"
              />
              <input
                value={ltSubtitle}
                onChange={(e) => setLtSubtitle(e.target.value)}
                placeholder="Team / role"
                className="w-full rounded-md border border-[#d1d5db] px-2.5 py-2 text-sm outline-none focus:border-[#0d99ff]"
              />
              <input
                value={ltLine3}
                onChange={(e) => setLtLine3(e.target.value)}
                placeholder="Extra line (optional)"
                className="w-full rounded-md border border-[#d1d5db] px-2.5 py-2 text-sm outline-none focus:border-[#0d99ff]"
              />
              <button
                type="button"
                disabled={sending || !ltTitle.trim()}
                onClick={() => void sendLowerThird()}
                className="w-full rounded-md bg-[#0d99ff] px-3 py-2.5 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
              >
                Push lower third
              </button>
            </section>

            {/* Stats */}
            <section className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
                3 · Match stats
              </p>
              <p className="text-[10px] leading-relaxed text-[#9ca3af]">
                Simulated feed · Opta / Stats Perform / FIFA
              </p>
              <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-3 space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <label className="space-y-1">
                    <span className="text-[10px] uppercase text-[#6b7280]">
                      Attempts {match.home_team}
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={99}
                      value={shotsHome}
                      onChange={(e) => setShotsHome(Number(e.target.value))}
                      className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                    />
                  </label>
                  <label className="space-y-1">
                    <span className="text-[10px] uppercase text-[#6b7280]">
                      Attempts {match.away_team}
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={99}
                      value={shotsAway}
                      onChange={(e) => setShotsAway(Number(e.target.value))}
                      className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                    />
                  </label>
                  <label className="space-y-1">
                    <span className="text-[10px] uppercase text-[#6b7280]">
                      On target {match.home_team}
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={99}
                      value={onTargetHome}
                      onChange={(e) => setOnTargetHome(Number(e.target.value))}
                      className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                    />
                  </label>
                  <label className="space-y-1">
                    <span className="text-[10px] uppercase text-[#6b7280]">
                      On target {match.away_team}
                    </span>
                    <input
                      type="number"
                      min={0}
                      max={99}
                      value={onTargetAway}
                      onChange={(e) => setOnTargetAway(Number(e.target.value))}
                      className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                    />
                  </label>
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-[11px] text-[#6b7280]">
                    <span>
                      {match.home_team} {possHome}%
                    </span>
                    <span>
                      {possAway}% {match.away_team}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={possHome}
                    onChange={(e) => setPossHome(Number(e.target.value))}
                    className="w-full accent-[#0d99ff]"
                  />
                  <p className="mt-0.5 text-center text-[10px] text-[#9ca3af]">
                    Possession
                  </p>
                </div>
              </div>
              <button
                type="button"
                disabled={sending}
                onClick={() => void sendStats()}
                className="w-full rounded-md bg-[#0d99ff] px-3 py-2.5 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
              >
                Push stats
              </button>
            </section>

            {(status || error) && (
              <div className="rounded-md border border-[#e5e7eb] bg-[#f9fafb] p-2 text-xs">
                {status && <p className="text-[#059669]">{status}</p>}
                {error && <p className="text-[#dc2626]">{error}</p>}
              </div>
            )}
          </div>
        </aside>

        {/* Center preview */}
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
            </div>
          </div>
        </main>

        {/* Right rail — match / clock */}
        <aside className="flex w-[300px] shrink-0 flex-col border-l border-[#e5e5e5] bg-white">
          <div className="border-b border-[#ebebeb] px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-[#6b7280]">
            Match · Clock
          </div>
          <div className="flex-1 space-y-5 overflow-y-auto p-3">
            <section className="space-y-3">
              <p className="text-[11px] uppercase tracking-wider text-[#6b7280]">
                Scorebug
              </p>
              <div
                className="rounded-lg p-3 text-white shadow-inner"
                style={{
                  background: '#1c1c20',
                  border: '2px solid transparent',
                  backgroundImage:
                    'linear-gradient(#1c1c20, #1c1c20), linear-gradient(135deg, #c83cb4, #3b66ff, #50e050, #ff7a28)',
                  backgroundOrigin: 'border-box',
                  backgroundClip: 'padding-box, border-box',
                }}
              >
                <div className="mb-2 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-lg font-semibold">
                    <span>{match.home_team}</span>
                    <span className="rounded-md bg-[#2d3038] px-2 py-0.5 text-[#a8ffbc]">
                      {match.home_score}
                    </span>
                    <span className="rounded-md bg-[#2d3038] px-2 py-0.5 text-[#a8ffbc]">
                      {match.away_score}
                    </span>
                    <span>{match.away_team}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-semibold text-[#a8ffbc]">{match.clock}</span>
                  <span className="rounded bg-[#2d3038] px-1.5 py-0.5 text-[10px] text-[#d1d5db]">
                    {match.period}
                  </span>
                  <span className="ml-auto flex items-center gap-1 rounded-full bg-[#c62828] px-2 py-0.5 text-[9px] font-bold">
                    <span className="h-1.5 w-1.5 rounded-full bg-white" />
                    LIVE
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <label className="space-y-1">
                  <span className="text-[10px] uppercase text-[#6b7280]">Home</span>
                  <input
                    value={match.home_team}
                    onChange={(e) =>
                      setMatch((m) => ({ ...m, home_team: e.target.value }))
                    }
                    onBlur={(e) => void patchMatch({ home_team: e.target.value })}
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
                    onBlur={(e) => void patchMatch({ away_team: e.target.value })}
                    className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                  />
                </label>
              </div>

              <div className="grid grid-cols-2 gap-2">
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
                      void patchMatch({ home_score: Number(e.target.value) })
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
                      void patchMatch({ away_score: Number(e.target.value) })
                    }
                    className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                  />
                </label>
              </div>
            </section>

            <section className="space-y-2">
              <p className="text-[11px] uppercase tracking-wider text-[#6b7280]">
                Period & clock
              </p>
              <div className="flex flex-wrap gap-1">
                {PERIODS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => void patchMatch({ period: p })}
                    className={`rounded-md px-2.5 py-1.5 text-xs font-semibold ${
                      match.period === p
                        ? 'bg-[#0d99ff] text-white'
                        : 'border border-[#e5e7eb] bg-[#f9fafb] text-[#374151] hover:border-[#0d99ff]'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <label className="space-y-1">
                  <span className="text-[10px] uppercase text-[#6b7280]">Minute</span>
                  <input
                    type="number"
                    min={0}
                    max={120}
                    value={match.clock_minute}
                    onChange={(e) =>
                      void patchMatch({ clock_minute: Number(e.target.value) })
                    }
                    className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                  />
                </label>
                <label className="space-y-1">
                  <span className="text-[10px] uppercase text-[#6b7280]">
                    Stoppage
                  </span>
                  <input
                    type="number"
                    min={0}
                    max={20}
                    value={match.stoppage}
                    onChange={(e) =>
                      void patchMatch({ stoppage: Number(e.target.value) })
                    }
                    className="w-full rounded border border-[#d1d5db] bg-white px-2 py-1.5 text-sm outline-none focus:border-[#0d99ff]"
                  />
                </label>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => void startET()}
                  className="rounded-md border border-[#fbbf24] bg-[#fffbeb] px-2 py-2 text-xs font-semibold text-[#92400e] hover:bg-[#fef3c7]"
                >
                  Start ET
                </button>
                <button
                  type="button"
                  onClick={() => void bumpStoppage()}
                  className="rounded-md border border-[#e5e7eb] bg-[#f9fafb] px-2 py-2 text-xs font-semibold text-[#374151] hover:border-[#0d99ff]"
                >
                  +1 stoppage
                </button>
              </div>
              <button
                type="button"
                onClick={() =>
                  void patchMatch({
                    clock_minute: match.clock_minute + 1,
                  })
                }
                className="w-full rounded-md border border-[#e5e7eb] bg-white px-2 py-2 text-xs font-medium text-[#374151] hover:border-[#0d99ff]"
              >
                +1′
              </button>
            </section>

            <section className="space-y-2">
              <p className="text-[11px] uppercase tracking-wider text-[#6b7280]">
                Goal editor
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
