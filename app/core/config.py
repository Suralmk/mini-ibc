import os

# Camera / encode
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
JPEG_QUALITY = 80

# Default match state (overridden live via /match API from the IBC editor)
HOME_TEAM = "ESP"
AWAY_TEAM = "ARG"
HOME_SCORE = 0
AWAY_SCORE = 0

APP_TITLE = "mini-ipc"
APP_DESCRIPTION = (
    "Laptop World Cup–style IBC: camera ingest, graphics burn-in, world-feed stream."
)

# Allow LAN / phone browsers (lab PoC)
CORS_ORIGINS = ["*"]
