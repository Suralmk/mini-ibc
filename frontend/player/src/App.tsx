import { useCallback, useEffect, useRef, useState } from 'react'
import { getHealth, wsStreamUrl } from './lib/api'
import { useWorldFeed } from './lib/useWorldFeed'

/**
 * Rights-holder player: native <video> fed by canvas.captureStream()
 * from IBC WebSocket JPEG frames — standard pattern for live frame
 * pipelines in the browser (vs raw <img> tags).
 */
export default function App() {
  const [score, setScore] = useState('--')
  const [home, setHome] = useState('')
  const [away, setAway] = useState('')
  const [landscape, setLandscape] = useState(false)
  const shellRef = useRef<HTMLDivElement | null>(null)
  const { connected, hasSignal, setCanvas, setVideo } = useWorldFeed()

  useEffect(() => {
    const tick = async () => {
      try {
        const h = await getHealth()
        setScore(h.score)
        setHome(h.home)
        setAway(h.away)
      } catch {
        /* ignore */
      }
    }
    void tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  const enterLandscape = useCallback(async () => {
    setLandscape(true)
    const el = shellRef.current
    try {
      await el?.requestFullscreen?.()
    } catch {
      /* fullscreen optional */
    }
    try {
      const orientation = screen.orientation as ScreenOrientation & {
        lock?: (o: string) => Promise<void>
      }
      await orientation.lock?.('landscape')
    } catch {
      /* iOS / unsupported — CSS rotate handles still work */
    }
  }, [])

  const exitLandscape = useCallback(async () => {
    setLandscape(false)
    try {
      screen.orientation.unlock?.()
    } catch {
      /* ignore */
    }
    if (document.fullscreenElement) {
      try {
        await document.exitFullscreen()
      } catch {
        /* ignore */
      }
    }
  }, [])

  useEffect(() => {
    const onFs = () => {
      if (!document.fullscreenElement) setLandscape(false)
    }
    document.addEventListener('fullscreenchange', onFs)
    return () => document.removeEventListener('fullscreenchange', onFs)
  }, [])

  const live = connected && hasSignal

  return (
    <div className="flex min-h-screen flex-col bg-[#f7f8fa]">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e5e7eb] bg-white px-6 py-5">
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-[#6b7280]">
            MINI IBC · Rights-holder
          </p>
          <h1 className="text-xl font-semibold text-[#111827]">
            World Feed Player
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-[#f3f4f6] px-3 py-1 text-xs text-[#374151] ring-1 ring-[#e5e7eb]">
            {home || 'HOME'} {score} {away || 'AWAY'}
          </span>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-4 px-6 py-8">
        <section
          ref={shellRef}
          className={`relative overflow-hidden rounded-2xl border border-[#e5e7eb] bg-black shadow-sm ${
            landscape
              ? 'fixed inset-0 z-50 rounded-none border-0'
              : ''
          }`}
        >
          {/* Hidden canvas → MediaStream source for <video> */}
          <canvas
            ref={setCanvas}
            className="pointer-events-none absolute left-0 top-0 h-px w-px opacity-0"
            aria-hidden
          />

          <div
            className={`relative bg-black ${
              landscape
                ? 'flex h-full w-full items-center justify-center'
                : 'aspect-video'
            }`}
          >
            <video
              ref={setVideo}
              className={`bg-black object-contain ${
                landscape ? 'h-full w-full' : 'h-full w-full'
              }`}
              autoPlay
              muted
              playsInline
              controls
              controlsList="nodownload"
            />

            {!live && (
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black text-[#9ca3af]">
                <span>No signal from IBC server</span>
                <span className="text-xs opacity-70">{wsStreamUrl()}</span>
              </div>
            )}

            {/* Rotate handles — tap corners to force landscape viewing */}
            {!landscape && (
              <>
                <button
                  type="button"
                  aria-label="Rotate to landscape"
                  title="Landscape"
                  onClick={() => void enterLandscape()}
                  className="absolute left-2 top-2 z-10 flex h-10 w-10 items-center justify-center rounded-lg border border-white/30 bg-black/55 text-white shadow backdrop-blur-sm active:scale-95"
                >
                  <RotateIcon />
                </button>
                <button
                  type="button"
                  aria-label="Rotate to landscape"
                  title="Landscape"
                  onClick={() => void enterLandscape()}
                  className="absolute right-2 top-2 z-10 flex h-10 w-10 items-center justify-center rounded-lg border border-white/30 bg-black/55 text-white shadow backdrop-blur-sm active:scale-95"
                >
                  <RotateIcon />
                </button>
                <button
                  type="button"
                  aria-label="Rotate to landscape"
                  title="Landscape"
                  onClick={() => void enterLandscape()}
                  className="absolute bottom-14 left-2 z-10 flex h-10 w-10 items-center justify-center rounded-lg border border-white/30 bg-black/55 text-white shadow backdrop-blur-sm active:scale-95"
                >
                  <RotateIcon />
                </button>
                <button
                  type="button"
                  aria-label="Rotate to landscape"
                  title="Landscape"
                  onClick={() => void enterLandscape()}
                  className="absolute bottom-14 right-2 z-10 flex h-10 w-10 items-center justify-center rounded-lg border border-white/30 bg-black/55 text-white shadow backdrop-blur-sm active:scale-95"
                >
                  <RotateIcon />
                </button>
              </>
            )}

            {landscape && (
              <button
                type="button"
                onClick={() => void exitLandscape()}
                className="absolute right-3 top-3 z-20 rounded-lg border border-white/30 bg-black/60 px-3 py-2 text-sm font-medium text-white backdrop-blur-sm"
              >
                Exit landscape
              </button>
            )}
          </div>

          {!landscape && (
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#e5e7eb] bg-[#fafafa] px-4 py-3 text-sm text-[#6b7280]">
              <span>
                Player:{' '}
                <strong className="text-[#059669]">
                  &lt;video&gt; · canvas.captureStream
                </strong>
              </span>
              <span>
                Socket:{' '}
                <strong className={live ? 'text-[#059669]' : 'text-[#dc2626]'}>
                  {live ? 'connected' : 'disconnected'}
                </strong>
              </span>
              <button
                type="button"
                onClick={() => void enterLandscape()}
                className="rounded-md border border-[#e5e7eb] bg-white px-3 py-1.5 text-xs font-medium text-[#374151] hover:border-[#0d99ff] hover:text-[#0d99ff]"
              >
                Landscape mode
              </button>
            </div>
          )}
        </section>

        <p className="text-center text-xs text-[#9ca3af]">
          Tip: use the corner rotate handles (or Landscape mode) on your phone,
          then turn the device sideways.
        </p>
      </main>
    </div>
  )
}

function RotateIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <polyline points="1 4 1 10 7 10" />
      <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
      <rect x="8" y="8" width="11" height="8" rx="1" />
    </svg>
  )
}
