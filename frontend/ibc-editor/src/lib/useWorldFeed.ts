import { useCallback, useEffect, useRef, useState } from 'react'
import { wsStreamUrl } from './api'

/** Drop the picture if no frame arrives within this window (server gone / stalled). */
const STALE_MS = 2000

export function useWorldFeed(reconnectToken = 0) {
  const [frameUrl, setFrameUrl] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)
  const urlRef = useRef<string | null>(null)

  const clearFrame = useCallback(() => {
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current)
      urlRef.current = null
    }
    setFrameUrl(null)
  }, [])

  useEffect(() => {
    let cancelled = false
    let ws: WebSocket | null = null
    let retryTimer: number | undefined
    let staleTimer: number | undefined

    const clearStaleWatch = () => {
      if (staleTimer !== undefined) {
        window.clearTimeout(staleTimer)
        staleTimer = undefined
      }
    }

    const markStale = () => {
      if (cancelled) return
      setConnected(false)
      clearFrame()
      try {
        ws?.close()
      } catch {
        /* ignore */
      }
    }

    const bumpStaleWatch = () => {
      clearStaleWatch()
      staleTimer = window.setTimeout(markStale, STALE_MS)
    }

    const connect = () => {
      clearStaleWatch()
      ws = new WebSocket(wsStreamUrl())
      ws.binaryType = 'arraybuffer'

      ws.onopen = () => {
        if (cancelled) return
        setConnected(true)
        bumpStaleWatch()
      }

      ws.onclose = () => {
        if (cancelled) return
        clearStaleWatch()
        setConnected(false)
        clearFrame()
        retryTimer = window.setTimeout(connect, 1500)
      }

      ws.onerror = () => {
        clearStaleWatch()
        setConnected(false)
        clearFrame()
        ws?.close()
      }

      ws.onmessage = (event) => {
        if (cancelled) return
        bumpStaleWatch()
        setConnected(true)
        const blob = new Blob([event.data], { type: 'image/jpeg' })
        const next = URL.createObjectURL(blob)
        const prev = urlRef.current
        urlRef.current = next
        setFrameUrl(next)
        if (prev) URL.revokeObjectURL(prev)
      }
    }

    connect()

    return () => {
      cancelled = true
      clearStaleWatch()
      if (retryTimer) window.clearTimeout(retryTimer)
      ws?.close()
      clearFrame()
      setConnected(false)
    }
  }, [reconnectToken, clearFrame])

  return { frameUrl, connected }
}
