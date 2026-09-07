"""A stylised greyscale map of your city, fading into white at the bottom.

Tiles come from OpenStreetMap's standard raster layer, greyscaled and lightened
into the minimal style the reference dashboard uses. (CARTO's "light_all" would
be a closer match stylistically but now demands an API key, and Wikimedia's
tiles return 403 to third parties.)

The map for a fixed location never changes, so it is fetched **once** and cached
on disk. That keeps us within OSM's tile usage policy — which asks for a real
User-Agent and no bulk downloading — and makes every later render instant.

Attribution (required): © OpenStreetMap contributors.
"""

import io
import logging
import math
import os
import urllib.request

from PIL import Image, ImageOps

LOG = logging.getLogger("nookpanel.map")

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_PX = 256
USER_AGENT = "hacking_nook/0.1 (personal e-ink dashboard; single cached fetch)"


def _deg2num(lat, lon, zoom):
    """Slippy-map tile coordinates, kept fractional so we can crop precisely."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return x, y


def _fetch_tile(z, x, y, retina):
    url = TILE_URL.format(z=z, x=x, y=y)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return Image.open(io.BytesIO(response.read())).convert("RGB")


def _build(lat, lon, zoom, width, height, retina):
    """Stitch enough tiles to cover width x height centred on lat/lon."""
    scale = 2 if retina else 1
    tile = TILE_PX * scale

    cx, cy = _deg2num(lat, lon, zoom)
    # Pixel position of the centre within the whole world at this zoom.
    px, py = cx * tile, cy * tile
    left, top = px - width / 2, py - height / 2

    x0, y0 = int(left // tile), int(top // tile)
    x1, y1 = int((left + width) // tile), int((top + height) // tile)

    canvas = Image.new("RGB", ((x1 - x0 + 1) * tile, (y1 - y0 + 1) * tile), "white")
    n = 2 ** zoom
    for tx in range(x0, x1 + 1):
        for ty in range(y0, y1 + 1):
            if not (0 <= ty < n):
                continue
            try:
                img = _fetch_tile(zoom, tx % n, ty, retina)
            except Exception as exc:
                LOG.warning("tile %s/%s/%s failed: %s", zoom, tx, ty, exc)
                continue
            canvas.paste(img, ((tx - x0) * tile, (ty - y0) * tile))

    ox, oy = int(left - x0 * tile), int(top - y0 * tile)
    return canvas.crop((ox, oy, ox + width, oy + height))


def _ramp(t, power=2.0):
    """Opacity at distance `t` (0..1) into a fade. 1 keeps the map, 0 is paper."""
    return 1.0 - t ** power


def _fade_mask(width, height, fade):
    """Opacity mask for the map: 255 keeps the map, 0 shows paper."""
    mask = Image.new("L", (width, height), 255)
    pixels = mask.load()

    bottom_from = int(height * 0.55)
    left_to = int(width * 0.50) if fade == "left_bottom" else 0

    for y in range(height):
        v_bottom = 1.0
        if y >= bottom_from:
            v_bottom = _ramp((y - bottom_from) / max(1, height - bottom_from))
        for x in range(width):
            v = v_bottom
            if x < left_to:
                # A square-root falloff clears a wide, genuinely white margin for
                # the overlaid badges; the quadratic used at the bottom would
                # keep the map dark until the last few columns.
                v *= _ramp((left_to - x) / left_to, power=0.5)
            pixels[x, y] = int(255 * v)
    return mask


def get(lat, lon, zoom, width, height, cache_dir,
        strength=0.8, style="light", fade="bottom", retina=False):
    """Cached greyscale map, faded to white over the bottom third.

    `strength` is how much of the original darkness to keep: 1.0 is the raw
    greyscale, 0.3 is a ghost. `style` is "light" (roads on white, a backdrop
    for large type) or "dark" (inverted — the map carries the picture).
    `fade` is "bottom", "left_bottom" (leaves room for overlaid badges) or None.

    Returns an "L" image, or None if the tiles could not be fetched and nothing
    is cached — callers should just render without a map in that case.
    """
    os.makedirs(cache_dir, exist_ok=True)
    key = (f"map_{lat:.4f}_{lon:.4f}_z{zoom}_{width}x{height}"
           f"_{style}_s{strength:.2f}_f{fade}{'@2x' if retina else ''}.png")
    path = os.path.join(cache_dir, key)

    if os.path.exists(path):
        return Image.open(path).convert("L")

    LOG.info("fetching map tiles (first run for this location)")
    try:
        rgb = _build(lat, lon, zoom, width, height, retina)
    except Exception as exc:
        LOG.warning("map unavailable: %s", exc)
        return None

    grey = rgb.convert("L")

    # OSM is a light-themed map: land and buildings are essentially white and
    # only thin lines are dark, so no tone curve can make it punchy — darkening
    # the land darkens the roads with it. Inverting does exactly what the
    # reference dashboard's custom dark map style does: dark land and water,
    # light roads and labels.
    if style == "dark":
        grey = ImageOps.invert(grey)

    # Pull back towards white so the panel keeps some headroom for the type.
    grey = grey.point(lambda v: 255 - int((255 - v) * strength))

    if fade is None:
        grey.save(path)
        return grey

    mask = _fade_mask(width, height, fade)
    faded = Image.composite(grey, Image.new("L", (width, height), 255), mask)

    faded.save(path)
    LOG.info("cached map at %s", path)
    return faded
