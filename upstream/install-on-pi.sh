#!/usr/bin/env bash
# Install upstream's weather-cal server natively on a Raspberry Pi.
#
# Run it ON the Pi, from a clone of this repo:
#   ~/hacking_nook/upstream/install-on-pi.sh
#
# Not Docker: upstream's published image is linux/amd64, and on a Zero 2 W with
# 425 MB of RAM a container runtime is overhead we cannot spare. Raspberry Pi OS
# ships chromium and chromium-driver in apt, so a venv against those is both
# lighter and simpler.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$REPO/external/inkplate10-weather-cal/server"
VENV="$REPO/upstream/.venv"
RUNDIR="$REPO/upstream/run"
PORT="${PORT:-8082}"
SWAP_MB="${SWAP_MB:-2048}"

echo "==> system packages"
sudo apt-get update -qq
# Pillow and PyYAML come from apt: neither publishes armv7 wheels, and building
# them from source on a Zero 2 W takes the better part of an hour.
sudo apt-get install -y -qq \
    chromium chromium-driver \
    python3-venv python3-pil python3-yaml \
    fonts-dejavu-core git

echo "==> swap (Chromium needs more headroom than 425 MB of RAM)"
if [ "$(free -m | awk '/^Swap:/{print $2}')" -lt "$SWAP_MB" ]; then
    sudo dphys-swapfile swapoff
    sudo sed -i "s/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=$SWAP_MB/" /etc/dphys-swapfile
    # The default cap is 2048; raise it so CONF_SWAPSIZE is honoured.
    sudo sed -i "s/^#\?CONF_MAXSWAP=.*/CONF_MAXSWAP=$SWAP_MB/" /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
fi
free -m | awk '/^Swap:/{print "    swap now " $2 " MB"}'

echo "==> submodule"
git -C "$REPO" submodule update --init --depth 1 external/inkplate10-weather-cal

echo "==> python environment"
# --system-site-packages so the apt Pillow and PyYAML are visible.
[ -d "$VENV" ] || python3 -m venv --system-site-packages "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip wheel

# Upstream's requirements minus Pillow and PyYAML (from apt above), and with
# the pins relaxed: the exact versions upstream pins have no armv7 wheels.
"$VENV/bin/pip" install --quiet \
    selenium airium packaging googlemaps Flask requests Werkzeug \
    paho-mqtt astral \
    "epd-server @ git+https://github.com/chrisjtwomey/epd.git@v0.3.1#subdirectory=server"

echo "==> patches"
# Idempotent: --check first so a re-run does not fail on an already-patched tree.
for patch in "$REPO"/upstream/patches/*.patch; do
    if git -C "$REPO/external/inkplate10-weather-cal" apply --check "$patch" 2>/dev/null; then
        git -C "$REPO/external/inkplate10-weather-cal" apply "$patch"
        echo "    applied $(basename "$patch")"
    else
        echo "    skipped $(basename "$patch") (already applied, or upstream moved)"
    fi
done

echo "==> our map shim"
install -m 644 "$REPO/server/mapview.py" "$APP/nook_mapview.py"
install -m 644 "$REPO/server/linemap.py" "$APP/linemap.py"
install -m 644 "$REPO/server/fonts.py"   "$APP/fonts.py"
install -m 644 "$REPO/upstream/google_api_shim.py" "$APP/google/api.py"

# server.py hardcodes config.yaml beside itself (`cwd` on line 30 is
# os.path.dirname(os.path.realpath(__file__)), not the process working
# directory) and has no --config flag. Keep the real file outside the submodule
# and symlink it into place.
mkdir -p "$RUNDIR"
if [ ! -f "$RUNDIR/config.yaml" ]; then
    sed -e 's/^  port: .*/  port: '"$PORT"'/' \
        "$REPO/upstream/config.example.yaml" > "$RUNDIR/config.yaml"
    # One page, not five, and regenerated through the day rather than once at
    # midnight. Each page is a separate Chromium run; the patch above makes the
    # pool list actually limit what gets rendered.
    python3 - "$RUNDIR/config.yaml" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path).read()
text = re.sub(r"  pools:\n(?:    .*\n)+", "  pools:\n    hourly: [hourly.png]\n", text)
times = "\n".join(f'    "{h:02d}:00:00": hourly' for h in range(0, 24, 2))
text = re.sub(r"  schedule:\n(?:    .*\n)+",
              "  schedule:\n    type: times\n" + times + "\n", text)
open(path, "w").write(text)
PY
    echo "    wrote upstream/run/config.yaml - edit location and timezone"
fi
ln -sfn "$RUNDIR/config.yaml" "$APP/config.yaml"

echo "==> systemd unit"
sudo tee /etc/systemd/system/weather-cal.service >/dev/null <<UNIT
[Unit]
Description=inkplate10-weather-cal server (upstream, with OSM map shim)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$RUNDIR
Environment=CHROME_BIN=/usr/bin/chromium
Environment=SERVER_PORT=$PORT
Environment=OSM_MAP_ZOOM=${OSM_MAP_ZOOM:-12}
Environment=OSM_MAP_STYLE=${OSM_MAP_STYLE:-lineart}
Environment=OSM_MAP_LABEL=${OSM_MAP_LABEL:-}
ExecStart=$VENV/bin/python $APP/server.py
Restart=always
# A regeneration is several minutes of Chromium. Restarting on top of one leaves
# two browsers competing and the webdriver connection times out at 120s - which
# Selenium does not expose - so give a dying run time to take its children with
# it, and leave a long gap before retrying.
RestartSec=120
TimeoutStopSec=90
KillMode=control-group
# Chromium is the memory hog; let it swap rather than be killed.
MemoryMax=infinity

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now weather-cal
echo "==> started. Watch it with:  journalctl -u weather-cal -f"
echo "    then point the Pi's panel server at http://127.0.0.1:$PORT/hourly.png"
