import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.stream import frame_hub

router = APIRouter()


@router.websocket("/ws/stream")
async def world_feed_ws(websocket: WebSocket):
    """
    Persistent world-feed socket: each message is one JPEG frame (binary).
    Clients display frames as they arrive — no HTTP request per image.
    """
    await websocket.accept()
    last_seq = -1
    try:
        while True:
            last_seq, jpg = await asyncio.to_thread(
                frame_hub.wait_next_jpeg,
                last_seq,
            )
            await websocket.send_bytes(jpg)
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass
