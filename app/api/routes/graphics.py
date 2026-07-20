from fastapi import APIRouter, HTTPException

from app.schemas.graphics import (
    GraphicActiveResponse,
    GraphicPushResponse,
    GraphicRequest,
)
from app.services.graphics_store import graphics_store

router = APIRouter(prefix="/graphics")


@router.post("", response_model=GraphicPushResponse)
def push_graphic(req: GraphicRequest):
    """IBC graphics desk: push animated center title onto the live world feed."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    graphic = graphics_store.set(req)
    return GraphicPushResponse(
        text=graphic.text,
        style=graphic.style,
        duration=graphic.duration,
        message="Graphic is now burning into /stream — watch the player.",
    )


@router.get("/active", response_model=GraphicActiveResponse)
def active_graphic():
    g = graphics_store.get()
    if g is None:
        return GraphicActiveResponse(active=False)
    return GraphicActiveResponse(
        active=True,
        text=g.text,
        style=g.style,
        duration=g.duration,
        remaining=round(graphics_store.remaining_seconds(g), 2),
    )
