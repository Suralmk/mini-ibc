import { useCallback, useEffect, useRef, useState } from 'react'
import { wsStreamUrl } from './api'

const STALE_MS = 2000

/**
 * Live world feed over WebSocket JPEG frames.
 * Real-world analogue: contribution is often frame/essence based (e.g. ST 2110);
 * for the browser we paint frames to a canvas and expose a MediaStream to a
 * native <video> element (same pattern as canvas.captureStream live previews).
 */
export function useWorldFeed(reconnectToken = 0) {
  const [connected, setConnected] = useState(false)
  const [hasSignal, setHasSignal] = useState(false)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const ensureStream = useCallback(() => {
    const canvas = canvasRef.current
    const video = videoRef.current
    if (!canvas || !video) return

    if (!streamRef.current) {
      streamRef.current = canvas.captureStream(30)
    }
    if (video.srcObject !== streamRef.current) {
      video.srcObject = streamRef.current
      void video.play().catch(() => {
        /* autoplay policies — muted + playsInline usually ok */
      })
    }
  }, [])

  const setCanvas = useCallback(
    (el: HTMLCanvasElement | null) => {
      canvasRef.current = el
      ensureStream()
    },
    [ensureStream],
  )

  const setVideo = useCallback(
    (el: HTMLVideoElement | null) => {
      videoRef.current = el
      ensureStream()
    },
    [ensureStream],
  )

  const clearSignal = useCallback(() => {
    setHasSignal(false)
    setConnected(false)
    const canvas = canvasRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.fillStyle = '#000'
        ctx.fillRect(0, 0, canvas.width || 16, canvas.height || 9)
      }
    }
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
      clearSignal()
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

    const paintFrame = async (data: ArrayBuffer) => {
      const canvas = canvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      const blob = new Blob([data], { type: 'image/jpeg' })
      const bitmap = await createImageBitmap(blob)
      if (cancelled) {
        bitmap.close()
        return
      }

      if (canvas.width !== bitmap.width || canvas.height !== bitmap.height) {
        canvas.width = bitmap.width
        canvas.height = bitmap.height
      }
      ctx.drawImage(bitmap, 0, 0)
      bitmap.close()
      ensureStream()
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
        clearSignal()
        retryTimer = window.setTimeout(connect, 1500)
      }

      ws.onerror = () => {
        clearStaleWatch()
        clearSignal()
        ws?.close()
      }

      ws.onmessage = (event) => {
        if (cancelled) return
        bumpStaleWatch()
        setConnected(true)
        setHasSignal(true)
        void paintFrame(event.data as ArrayBuffer)
      }
    }

    connect()

    return () => {
      cancelled = true
      clearStaleWatch()
      if (retryTimer) window.clearTimeout(retryTimer)
      ws?.close()
      streamRef.current?.getTracks().forEach((t) => t.stop())
      streamRef.current = null
      if (videoRef.current) videoRef.current.srcObject = null
      clearSignal()
    }
  }, [reconnectToken, clearSignal, ensureStream])

  return { connected, hasSignal, setCanvas, setVideo }
}
