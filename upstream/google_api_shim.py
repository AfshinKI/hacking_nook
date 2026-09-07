"""Drop-in replacement for the upstream server's `google/api.py`.

Upstream builds its map with Google Static Maps, which makes a Google Cloud
project with billing a hard requirement — `server.py` constructs
`GoogleAPIService` unconditionally at startup and exits without a valid key.
This provides the same class with the same contract, backed by keyless
OpenStreetMap tiles and Open-Meteo geocoding instead.

Only `get_static_map_local_src(map_id, location)` is called by `server.py`
(line 207). It must write a PNG under `views/html/map-cache/` and return the
path relative to `views/html/`, which is what the page templates put in
`<img src>`.

Tuning, via environment variables:
    OSM_MAP_FILE      path to your own image; used instead of fetching tiles
    OSM_MAP_ZOOM      slippy-map zoom: 11 metro, 13 city centre (default 13)
    OSM_MAP_CENTER    "lat,lon" to frame it by hand instead of geocoding
    OSM_MAP_STYLE     "lineart" (black streets on white, drawn from OSM vector
                      data — best for e-ink), "dark" (inverted raster tiles) or
                      "light" (raster tiles as drawn)
    OSM_MAP_LABEL     place name on a black plate, lineart only
    OSM_MAP_STRENGTH  0-1, how much of the greyscale darkness to keep
    OSM_MAP_SIZE      square edge in pixels (default 1200 = upstream 600 @2x)

See upstream/README.md for how to replace the map with your own picture.
"""

import hashlib
import json
import logging
import os
import sys
import urllib.parse
import urllib.request

from PIL import Image

sys.path.insert(0, "/app")
import linemap  # noqa: E402  (path set above)
import nook_mapview as mapview  # noqa: E402

log = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
USER_AGENT = "hacking_nook/0.1 (personal e-ink dashboard)"


def _env_float(name, default):
    try:
        return float(os.environ[name])
    except (KeyError, ValueError):
        return default


def _env_int(name, default):
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default


class GoogleAPIService:
    """Named for the module it replaces; there is nothing Google about it."""

    def __init__(self, key=None):
        self.apikey = key
        here = os.path.dirname(os.path.realpath(__file__))
        self._tile_cache_dir = os.path.join(here, "map-tiles")
        self._local_map_rel_dir = "map-cache"
        self._local_map_abs_dir = os.path.normpath(
            os.path.join(here, "..", "views", "html", self._local_map_rel_dir))

    # --- geocoding ---------------------------------------------------------

    def _coords(self, location):
        override = os.environ.get("OSM_MAP_CENTER", "").strip()
        if override:
            lat, _, lon = override.partition(",")
            return float(lat), float(lon)

        if isinstance(location, (list, tuple)) and len(location) == 2:
            return float(location[0]), float(location[1])

        query = urllib.parse.urlencode({"name": str(location), "count": 1})
        request = urllib.request.Request(f"{GEOCODING_URL}?{query}",
                                         headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)

        results = payload.get("results") or []
        if not results:
            raise ValueError(f"could not geocode location {location!r}")
        return float(results[0]["latitude"]), float(results[0]["longitude"])

    # --- the one method server.py calls ------------------------------------

    def _own_picture(self, size):
        """Your own image, squared off to `size` — cover-fit, centre-cropped."""
        path = os.environ.get("OSM_MAP_FILE", "").strip()
        if not path:
            return None, None
        if not os.path.exists(path):
            log.warning("OSM_MAP_FILE=%s does not exist; falling back to tiles", path)
            return None, None

        image = Image.open(path).convert("L")
        scale = max(size / image.width, size / image.height)
        resized = image.resize((max(1, round(image.width * scale)),
                                max(1, round(image.height * scale))), Image.LANCZOS)
        left = (resized.width - size) // 2
        top = (resized.height - size) // 2
        cropped = resized.crop((left, top, left + size, top + size))

        digest = hashlib.sha1(
            f"{path}:{os.path.getmtime(path)}:{size}".encode()).hexdigest()[:16]
        return cropped, digest

    def get_static_map_local_src(self, map_id, location):
        size = _env_int("OSM_MAP_SIZE", 1200)

        own, own_digest = self._own_picture(size)
        if own is not None:
            os.makedirs(self._local_map_abs_dir, exist_ok=True)
            filename = f"custommap_{own_digest}.png"
            own.convert("RGB").save(os.path.join(self._local_map_abs_dir, filename))
            log.info("map from OSM_MAP_FILE=%s -> %s",
                     os.environ["OSM_MAP_FILE"], filename)
            return f"{self._local_map_rel_dir}/{filename}"

        lat, lon = self._coords(location)
        zoom = _env_int("OSM_MAP_ZOOM", 13)
        style = os.environ.get("OSM_MAP_STYLE", "lineart")
        strength = _env_float("OSM_MAP_STRENGTH", 0.70)

        if style == "lineart":
            label = os.environ.get("OSM_MAP_LABEL") or None
            image = linemap.get(lat, lon, zoom, size, self._tile_cache_dir,
                                label=label)
        else:
            # Upstream's CSS does its own fade over the map, so ours must not.
            image = mapview.get(lat, lon, zoom, size, size, self._tile_cache_dir,
                                strength=strength, style=style, fade=None)
        if image is None:
            raise RuntimeError("could not build a map from OpenStreetMap data")

        os.makedirs(self._local_map_abs_dir, exist_ok=True)
        key = (f"{lat:.4f},{lon:.4f},{zoom},{size},{style},{strength},"
               f"{os.environ.get('OSM_MAP_LABEL', '')}")
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        filename = f"osmmap_{digest}.png"
        image.convert("RGB").save(os.path.join(self._local_map_abs_dir, filename))

        log.info("map for %s (%.4f, %.4f) z%d %s -> %s",
                 location, lat, lon, zoom, style, filename)
        return f"{self._local_map_rel_dir}/{filename}"

    def get_timezone(self, location):
        raise NotImplementedError("timezone comes from config in this build")
