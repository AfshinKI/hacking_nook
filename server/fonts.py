"""Font lookup.

The dashboard wants a rounded, hand-lettered face — Comic Neue is the closest
thing packaged in Debian (`fonts-comic-neue`). DejaVu is the fallback so the
server still renders something legible on a box without it.
"""

import logging
import os

from PIL import ImageFont

LOG = logging.getLogger("nookpanel.fonts")

# Searched in order; first hit wins.
_FAMILIES = {
    "bold": [
        "~/.local/share/fonts/ComicNeue-Bold.otf",
        "/usr/share/fonts/opentype/comic-neue/ComicNeue-Bold.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "regular": [
        "~/.local/share/fonts/ComicNeue-Regular.otf",
        "/usr/share/fonts/opentype/comic-neue/ComicNeue-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "light": [
        "~/.local/share/fonts/ComicNeue-Light.otf",
        "/usr/share/fonts/opentype/comic-neue/ComicNeue-Light.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}

_warned = set()


def load(size, weight="regular"):
    for path in _FAMILIES[weight]:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    if weight not in _warned:
        LOG.warning("no font found for weight %r; using PIL's bitmap default", weight)
        _warned.add(weight)
    return ImageFont.load_default()


def have_comic_neue():
    """True when the intended face is present — the layout is tuned for it."""
    return any(
        os.path.exists(os.path.expanduser(p))
        for p in _FAMILIES["bold"]
        if "Comic" in p
    )
