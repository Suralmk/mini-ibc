from fastapi import APIRouter, HTTPException

from app.schemas.graphics import (
    GraphicActiveResponse,
    GraphicPushResponse,
    GraphicRequest,
)
from app.services.graphics_store import graphics_store
from app.services.match_store import match_store

router = APIRouter(prefix="/graphics")


@router.post("", response_model=GraphicPushResponse)
def push_graphic(req: GraphicRequest):
    """IBC graphics desk: push a timed overlay onto the live world feed."""
    try:
        # Fill stats team labels from live match if omitted
        if req.kind == "stats":
            m = match_store.get()
            if not req.home_label:
                req.home_label = m.home_team
            if not req.away_label:
                req.away_label = m.away_team
        graphic = graphics_store.set(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    label = graphic.text or graphic.title or graphic.kind
    return GraphicPushResponse(
        kind=graphic.kind,
        text=graphic.text or None,
        title=graphic.title or None,
        style=graphic.style if graphic.kind == "title" else None,
        duration=graphic.duration,
        message=f"{graphic.kind} is now burning into the world feed ({label}).",
    )


@router.get("/active", response_model=GraphicActiveResponse)
def active_graphic():
    g = graphics_store.get()
    if g is None:
        return GraphicActiveResponse(active=False)
    return GraphicActiveResponse(
        active=True,
        kind=g.kind,
        text=g.text or None,
        title=g.title or None,
        subtitle=g.subtitle or None,
        style=g.style if g.kind == "title" else None,
        duration=g.duration,
        remaining=round(graphics_store.remaining_seconds(g), 2),
    )
