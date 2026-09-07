#!/usr/bin/env bash
# Build and run the upstream weather-cal server with our OSM map shim.
#
#   ./upstream/run.sh            build and start on :8081
#   ./upstream/run.sh --rebuild  force a rebuild first
#
# Run from the repo root. Needs Docker and an x86_64 host — upstream's image is
# linux/amd64 only, and it carries Chromium.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

IMAGE=nook-weather-cal:latest
NAME=nookcal
PORT=${PORT:-8081}
CONFIG=${CONFIG:-upstream/config.yaml}

[ -f "$CONFIG" ] || cp upstream/config.example.yaml "$CONFIG"

if [ "${1:-}" = "--rebuild" ] || ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "==> building $IMAGE"
    docker build -t "$IMAGE" -f upstream/Dockerfile .
fi

docker rm -f "$NAME" >/dev/null 2>&1 || true

# Map settings live here rather than in config.yaml: they are ours, not
# upstream's, and upstream's schema would reject unknown keys.
docker run -d --name "$NAME" --restart unless-stopped -p "$PORT:8080" \
    -v "$PWD/$CONFIG:/app/config.yaml:ro" \
    ${OSM_MAP_FILE:+-v "$OSM_MAP_FILE:/app/custom-map.png:ro" -e OSM_MAP_FILE=/app/custom-map.png} \
    -e SERVER_PORT=8080 \
    -e OSM_MAP_ZOOM="${OSM_MAP_ZOOM:-12}" \
    -e OSM_MAP_STYLE="${OSM_MAP_STYLE:-lineart}" \
    ${OSM_MAP_LABEL:+-e OSM_MAP_LABEL="$OSM_MAP_LABEL"} \
    -e OSM_MAP_STRENGTH="${OSM_MAP_STRENGTH:-0.70}" \
    ${OSM_MAP_CENTER:+-e OSM_MAP_CENTER="$OSM_MAP_CENTER"} \
    "$IMAGE" >/dev/null

echo "==> $NAME on http://localhost:$PORT"
echo "    pages: /hourly.png /today.png /daily.png /current.png /tomorrow.png"
echo "    logs:  docker logs -f $NAME"
