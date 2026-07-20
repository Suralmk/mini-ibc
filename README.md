# MINI IBC

**MINI IBC** is a small-scale **International Broadcast Centre** lab: your webcam is the “stadium,” a FastAPI backend “makes” the match (scorebug + pulsed titles), and two React apps act as the graphics desk and a rights-holder player.

Inspired by how the real FIFA World Cup IBC works — stadium feeds over fiber into a central facility, then out to broadcasters worldwide. See **[FIFA-IBC.md](FIFA-IBC.md)** for that architecture (with diagrams), and Network Chuck’s tour for the full story: [YouTube](https://www.youtube.com/watch?v=LhnH0juUaGw).

```
Webcam (stadium)
        │
        ▼
FastAPI API  (:8000)   ← compose graphics / live score
        │
        ├── React Graphics Editor  (:5173)
        └── React World Feed Player  (:5174)
```

## What you can do

- Live camera over **WebSocket** → native `<video>` player (`canvas.captureStream`)
- **Graphics desk**: pulse titles, **lower thirds**, **match stats** (simulated Opta / Stats Perform / FIFA), live score / goals
- **Scorebug**: FIFA-style strip with period (`1H` · `HT` · `2H` · `ET` · `FT`) and stoppage (`90+3'`)
- **Player**: watch the burned-in world feed (landscape handles on mobile)

## Project structure

```
mini-ibc/
├── app/                         # FastAPI backend
├── frontend/
│   ├── ibc-editor/
│   └── player/
├── Dockerfile
├── docker-compose.yml
├── scripts/build-and-push.sh
├── FIFA-IBC.md
└── requirements.txt
```

---

## Option A — Clone and run locally (dev)

```bash
git clone <your-repo-url> mini-ibc
cd mini-ibc
```

**1. Backend**

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use `--host 127.0.0.1` only if you never need phone/LAN access.

**2. Graphics Editor**

```bash
cd frontend/ibc-editor
npm install
npm run dev
```

→ http://127.0.0.1:5173

**3. World Feed Player**

```bash
cd frontend/player
npm install
npm run dev
```

→ http://127.0.0.1:5174

---

## Option B — Pull from Docker Hub

Images:

| Service | Image |
|---------|--------|
| API | `suralmk/mini-ibc-api` |
| Editor | `suralmk/mini-ibc-editor` |
| Player | `suralmk/mini-ibc-player` |

```bash
export DOCKERHUB_USER=suralmk
export TAG=latest

docker compose pull
docker compose up -d
```

- Editor: http://localhost:5173  
- Player: http://localhost:5174  
- API health: http://localhost:8000/health  

Frontends proxy `/health`, `/graphics`, `/match`, and `/ws/` to the API container (same-origin).

> **Webcam note:** camera access inside Docker depends on the host OS. On Linux you can uncomment `devices: /dev/video0` in `docker-compose.yml`. On Docker Desktop (Windows/macOS), host webcam passthrough is limited — use Option A for reliable camera access.

---

## How to test

1. Open the **player** (5174) — live `<video>` over WebSocket frames.
2. Open the **editor** (5173) — push a title, lower third, or match stats; set period / ET / stoppage.
3. Watch overlays and the scorebug update on both apps (burned into the feed).

## API

```bash
# Pulse title
curl -X POST http://127.0.0.1:8000/graphics \
  -H "Content-Type: application/json" \
  -d '{"kind":"title","text":"FIFA","duration":4,"style":"pulse"}'

# Lower third
curl -X POST http://127.0.0.1:8000/graphics \
  -H "Content-Type: application/json" \
  -d '{"kind":"lower_third","title":"Lionel Messi","subtitle":"Argentina","line3":"3 Goals in Tournament","duration":6}'

# Match stats (simulated data feed)
curl -X POST http://127.0.0.1:8000/graphics \
  -H "Content-Type: application/json" \
  -d '{"kind":"stats","home_possession":58,"away_possession":42,"home_shots":12,"away_shots":8,"duration":7}'

# Extra time on scorebug
curl -X PATCH http://127.0.0.1:8000/match \
  -H "Content-Type: application/json" \
  -d '{"period":"ET","clock_minute":90,"stoppage":2}'

curl -X POST http://127.0.0.1:8000/match/goal \
  -H "Content-Type: application/json" \
  -d '{"side":"home","announce":true}'
```

`GET/PATCH /match` · `POST /match/goal` · `POST /graphics` (`title` | `lower_third` | `stats`) · `WS /ws/stream`

## Learn more

- **[How the FIFA World Cup IBC works](FIFA-IBC.md)** — fiber, red/blue paths, multicast, ST 2110, fallbacks  
- **Video reference:** [Network Chuck — World Cup network / IBC](https://www.youtube.com/watch?v=LhnH0juUaGw)
