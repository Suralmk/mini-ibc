#!/usr/bin/env bash
# Build MINI IBC images and push them to Docker Hub.
#
# Usage:
#   export DOCKERHUB_USER=suralmk
#   ./scripts/build-and-push.sh              # tag: latest
#   ./scripts/build-and-push.sh v0.1.0       # tag: v0.1.0 (+ latest)
#
# Requires: docker login (run `docker login` once)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Load repo .env if present (DOCKERHUB_USER=suralmk)
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

DOCKERHUB_USER="${DOCKERHUB_USER:-suralmk}"

if [[ -z "${DOCKERHUB_USER}" ]]; then
  echo "ERROR: set DOCKERHUB_USER to your Docker Hub username"
  echo "  export DOCKERHUB_USER=suralmk"
  exit 1
fi

TAG="${1:-latest}"
API_IMAGE="${DOCKERHUB_USER}/mini-ibc-api"
EDITOR_IMAGE="${DOCKERHUB_USER}/mini-ibc-editor"
PLAYER_IMAGE="${DOCKERHUB_USER}/mini-ibc-player"

echo "==> Building ${API_IMAGE}:${TAG}"
docker build -t "${API_IMAGE}:${TAG}" -f Dockerfile .

echo "==> Building ${EDITOR_IMAGE}:${TAG}"
docker build \
  --build-arg VITE_API_BASE= \
  -t "${EDITOR_IMAGE}:${TAG}" \
  -f frontend/ibc-editor/Dockerfile \
  frontend/ibc-editor

echo "==> Building ${PLAYER_IMAGE}:${TAG}"
docker build \
  --build-arg VITE_API_BASE= \
  -t "${PLAYER_IMAGE}:${TAG}" \
  -f frontend/player/Dockerfile \
  frontend/player

if [[ "${TAG}" != "latest" ]]; then
  docker tag "${API_IMAGE}:${TAG}" "${API_IMAGE}:latest"
  docker tag "${EDITOR_IMAGE}:${TAG}" "${EDITOR_IMAGE}:latest"
  docker tag "${PLAYER_IMAGE}:${TAG}" "${PLAYER_IMAGE}:latest"
fi

echo "==> Pushing images"
docker push "${API_IMAGE}:${TAG}"
docker push "${EDITOR_IMAGE}:${TAG}"
docker push "${PLAYER_IMAGE}:${TAG}"

if [[ "${TAG}" != "latest" ]]; then
  docker push "${API_IMAGE}:latest"
  docker push "${EDITOR_IMAGE}:latest"
  docker push "${PLAYER_IMAGE}:latest"
fi

echo ""
echo "Done. Pull / run with:"
echo "  export DOCKERHUB_USER=${DOCKERHUB_USER}"
echo "  export TAG=${TAG}"
echo "  docker compose pull"
echo "  docker compose up -d"
echo ""
echo "Editor: http://localhost:5173"
echo "Player: http://localhost:5174"
echo "API:    http://localhost:8000/health"
