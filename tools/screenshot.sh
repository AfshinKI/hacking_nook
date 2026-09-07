#!/usr/bin/env bash
# Grab what is on the Nook's e-ink panel, over adb.
#
#   ./tools/screenshot.sh out.png
#
# Android 2.1 has no `screencap`, so read the framebuffer directly. fb0 is
# 600x1600 virtual (double-buffered: two 600x800 pages) at 16 bpp RGB565,
# stride 1200 bytes. We take the first page.
set -euo pipefail

OUT="${1:-nook-screen.png}"
RAW=$(mktemp)
trap 'rm -f "$RAW"' EXIT

W=600; H=800
adb shell "dd if=/dev/graphics/fb0 bs=1200 count=$H 2>/dev/null" > "$RAW"

python3 - "$RAW" "$OUT" "$W" "$H" <<'PY'
import sys
from PIL import Image

raw, out, w, h = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
data = open(raw, "rb").read()
need = w * h * 2
if len(data) < need:
    sys.exit(f"short read: got {len(data)} bytes, need {need}")

img = Image.frombytes("RGB", (w, h), data[:need], "raw", "BGR;16")
img.convert("L").save(out)
print(f"wrote {out} ({w}x{h})")
PY
