"""A black-line street map drawn from raw OpenStreetMap geometry.

Every black-and-white raster basemap that used to serve this style is gone:
Stamen Toner moved to Stadia and needs a key, `tiles.wmflabs.org/bw-mapnik` no
longer resolves, Tracestrack returns 403. So this queries Overpass for the road
and water geometry directly and draws it — thin black lines on white, water
solid black.

That is the best possible input for this panel. E Ink has 16 grey levels and
upstream dithers to 4, so any greyscale photo turns to noise; pure black on
white has nothing to dither.

One query per location, cached to disk — Overpass is a shared free service and
this is not a thing to poll.
"""

import json
import logging
import math
import os
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw

LOG = logging.getLogger("nookpanel.linemap")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "hacking_nook/0.1 (personal e-ink dashboard; one cached query)"

# Line width in pixels at 1x, by road class. Drawn at 2x and downsampled.
ROAD_WIDTHS = {
    "motorway": 3.0, "trunk": 3.0,
    "primary": 2.4, "secondary": 1.9, "tertiary": 1.5,
    "residential": 1.0, "unclassified": 1.0, "living_street": 1.0,
}
ROAD_CLASSES = "|".join(ROAD_WIDTHS)

QUERY = """
[out:json][timeout:180];
(
  way["highway"~"^({classes})(_link)?$"]({bbox});
  way["natural"="water"]({bbox});
  way["waterway"="riverbank"]({bbox});
  relation["natural"="water"]({bbox});
  way["waterway"~"^(river|stream|canal)$"]({bbox});
);
out geom;
"""


def _metres_per_pixel(lat, zoom):
    return 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)


def _bbox(lat, lon, zoom, size):
    """South, west, north, east covering a `size`-pixel square at `zoom`."""
    half_m = _metres_per_pixel(lat, zoom) * size / 2
    dlat = half_m / 111_320.0
    dlon = half_m / (111_320.0 * math.cos(math.radians(lat)))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def _fetch(lat, lon, zoom, size, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"osm_{lat:.4f}_{lon:.4f}_z{zoom}_{size}.json")
    if os.path.exists(path):
        with open(path) as handle:
            return json.load(handle)

    south, west, north, east = _bbox(lat, lon, zoom, size)
    query = QUERY.format(classes=ROAD_CLASSES,
                         bbox=f"{south},{west},{north},{east}")
    LOG.info("querying Overpass for %.4f,%.4f z%d (first run for this location)",
             lat, lon, zoom)

    request = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=240) as response:
        payload = json.load(response)

    with open(path, "w") as handle:
        json.dump(payload, handle)
    LOG.info("cached %d OSM elements at %s", len(payload.get("elements", [])), path)
    return payload


def _projector(lat, lon, zoom, size, scale):
    """lat/lon -> pixel coordinates in a `size * scale` square centred on lat/lon."""
    world = 256 * (2 ** zoom) * scale

    def to_world(latitude, longitude):
        x = (longitude + 180.0) / 360.0 * world
        sin_lat = math.sin(math.radians(latitude))
        y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * world
        return x, y

    cx, cy = to_world(lat, lon)
    origin_x, origin_y = cx - size * scale / 2, cy - size * scale / 2

    def project(point):
        x, y = to_world(point["lat"], point["lon"])
        return x - origin_x, y - origin_y

    return project


def _stitch_rings(segments):
    """Join multipolygon outer members end-to-end into closed rings.

    Overpass hands back a relation's outer boundary as separate ways in no
    particular order or direction. Filling each one on its own closes an open
    line across the map — which is how the North Saskatchewan ends up as a black
    band from corner to corner. Only rings that actually close are returned.
    """
    def key(point):
        return round(point["lat"], 7), round(point["lon"], 7)

    remaining = [list(s) for s in segments if len(s) > 1]
    rings = []

    while remaining:
        ring = remaining.pop(0)
        extended = True
        while extended and key(ring[0]) != key(ring[-1]):
            extended = False
            for i, candidate in enumerate(remaining):
                if key(candidate[0]) == key(ring[-1]):
                    ring += candidate[1:]
                elif key(candidate[-1]) == key(ring[-1]):
                    ring += list(reversed(candidate))[1:]
                elif key(candidate[-1]) == key(ring[0]):
                    ring = candidate[:-1] + ring
                elif key(candidate[0]) == key(ring[0]):
                    ring = list(reversed(candidate))[:-1] + ring
                else:
                    continue
                remaining.pop(i)
                extended = True
                break
        if key(ring[0]) == key(ring[-1]) and len(ring) > 3:
            rings.append(ring)
    return rings


def get(lat, lon, zoom, size, cache_dir, label=None):
    """Return an "L" image: black roads and water on white. None if it fails."""
    os.makedirs(cache_dir, exist_ok=True)
    key = f"linemap_{lat:.4f}_{lon:.4f}_z{zoom}_{size}{'_' + label if label else ''}.png"
    path = os.path.join(cache_dir, key)
    if os.path.exists(path):
        return Image.open(path).convert("L")

    try:
        payload = _fetch(lat, lon, zoom, size, cache_dir)
    except Exception as exc:
        LOG.warning("Overpass unavailable: %s", exc)
        return None

    # Draw at 2x for anti-aliasing; PIL has no anti-aliased lines.
    scale = 2
    canvas = Image.new("L", (size * scale, size * scale), 255)
    draw = ImageDraw.Draw(canvas)
    project = _projector(lat, lon, zoom, size, scale)

    roads, water_areas, water_lines = [], [], []
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        if "highway" in tags:
            roads.append(element)
        elif tags.get("natural") == "water" or tags.get("waterway") == "riverbank":
            water_areas.append(element)
        elif "waterway" in tags:
            water_lines.append(element)

    def points(element):
        geometry = element.get("geometry")
        if geometry:
            return [project(p) for p in geometry]
        return None

    # Water first: solid black areas, then the thin watercourses on top.
    for element in water_areas:
        if element["type"] == "relation":
            outers = [m["geometry"] for m in element.get("members", [])
                      if m.get("role") == "outer" and m.get("geometry")]
            for ring in _stitch_rings(outers):
                pts = [project(p) for p in ring]
                if len(pts) > 2:
                    draw.polygon(pts, fill=0)
        else:
            pts = points(element)
            if pts and len(pts) > 2:
                draw.polygon(pts, fill=0)

    for element in water_lines:
        pts = points(element)
        if pts and len(pts) > 1:
            draw.line(pts, fill=0, width=max(1, int(1.6 * scale)), joint="curve")

    for element in roads:
        pts = points(element)
        if not pts or len(pts) < 2:
            continue
        highway = element["tags"]["highway"].replace("_link", "")
        width = ROAD_WIDTHS.get(highway, 1.0) * scale
        draw.line(pts, fill=0, width=max(1, round(width)), joint="curve")

    image = canvas.resize((size, size), Image.LANCZOS)

    if label:
        _draw_label(image, label, size)

    image.save(path)
    LOG.info("drew %d roads, %d water areas -> %s", len(roads), len(water_areas), key)
    return image


def _draw_label(image, label, size):
    """A black plate with the place name, as on the printed poster style."""
    import fonts

    draw = ImageDraw.Draw(image)
    text = " ".join(label.upper())
    font = fonts.load(max(14, size // 34), "bold")
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    pad_x, pad_y = size // 48, size // 90
    box_w, box_h = (right - left) + pad_x * 2, (bottom - top) + pad_y * 2
    x = (size - box_w) // 2
    y = int(size * 0.86)
    draw.rectangle([x, y, x + box_w, y + box_h], fill=0)
    draw.text((x + pad_x - left, y + pad_y - top), text, font=font, fill=255)
