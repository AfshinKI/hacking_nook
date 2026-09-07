"""Chunky outlined weather icons, drawn rather than downloaded.

The look is white shapes with a heavy black outline — it survives e-ink's
16 grey levels far better than a detailed pictogram, and it means no icon font
or asset pack to ship.

Every icon is built the same way: draw the silhouette into a mask, dilate the
mask to get the outline, then paint white inside and black in the ring. That
gives a single clean outline around the *union* of the parts, instead of seeing
the seams where a cloud's circles overlap.

`get(code, is_day, size)` returns `(image, mask)`, both mode "L", where `mask`
is the icon's alpha.
"""

import math

from PIL import Image, ImageDraw, ImageFilter

BLACK, WHITE = 0, 255


def _dilate(mask, radius):
    """Grow a silhouette by `radius` px. MaxFilter needs an odd kernel."""
    return mask.filter(ImageFilter.MaxFilter(radius * 2 + 1))


def _star(draw, cx, cy, r, fill=255):
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        radius = r if i % 2 == 0 else r * 0.42
        points.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
    draw.polygon(points, fill=fill)


def _sun(draw, cx, cy, r, rays=True):
    if rays:
        for i in range(8):
            angle = i * math.pi / 4
            x0, y0 = cx + math.cos(angle) * r * 1.15, cy + math.sin(angle) * r * 1.15
            x1, y1 = cx + math.cos(angle) * r * 1.75, cy + math.sin(angle) * r * 1.75
            draw.line([(x0, y0), (x1, y1)], fill=255, width=max(3, int(r * 0.28)))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)


def _moon(draw, cx, cy, r):
    """Crescent: a disc with a second disc bitten out of it."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    bite = r * 0.92
    bx = cx + r * 0.52
    draw.ellipse([bx - bite, cy - bite * 1.05, bx + bite, cy + bite * 1.05], fill=0)


def _cloud(draw, cx, cy, w):
    """A cloud as overlapping lobes plus a base slab, centred on (cx, cy)."""
    h = w * 0.62
    left, top = cx - w / 2, cy - h / 2
    draw.ellipse([left, top + h * 0.30, left + w * 0.50, top + h * 1.00], fill=255)
    draw.ellipse([left + w * 0.18, top, left + w * 0.72, top + h * 0.86], fill=255)
    draw.ellipse([left + w * 0.52, top + h * 0.22, left + w * 1.00, top + h * 1.00], fill=255)
    draw.rectangle([left + w * 0.12, top + h * 0.62, left + w * 0.88, top + h * 1.00], fill=255)


def _drops(draw, cx, cy, w, count=3):
    spacing = w / (count + 1)
    for i in range(count):
        x = cx - w / 2 + spacing * (i + 1)
        y = cy + (i % 2) * w * 0.10
        r = w * 0.055
        draw.ellipse([x - r, y, x + r, y + r * 2.1], fill=255)
        draw.polygon([(x - r, y + r * 0.4), (x + r, y + r * 0.4), (x, y - r * 1.5)], fill=255)


def _flakes(draw, cx, cy, w, count=3):
    spacing = w / (count + 1)
    for i in range(count):
        x = cx - w / 2 + spacing * (i + 1)
        y = cy + (i % 2) * w * 0.10 + w * 0.06
        r = w * 0.13
        # Thin arms: the outline dilation thickens them, and anything heavier
        # merges into a blob.
        for k in range(3):
            angle = k * math.pi / 3
            draw.line(
                [(x - math.cos(angle) * r, y - math.sin(angle) * r),
                 (x + math.cos(angle) * r, y + math.sin(angle) * r)],
                fill=255, width=2)


def _bolt(draw, cx, cy, w):
    s = w * 0.20
    draw.polygon([
        (cx + s * 0.35, cy - s * 1.1), (cx - s * 0.75, cy + s * 0.30),
        (cx - s * 0.05, cy + s * 0.30), (cx - s * 0.45, cy + s * 1.6),
        (cx + s * 0.85, cy - s * 0.10), (cx + s * 0.10, cy - s * 0.10),
    ], fill=255)


# WMO code -> which silhouette to draw.
def _kind(code):
    if code == 0:
        return "clear"
    if code in (1, 2):
        return "partly"
    if code == 3:
        return "cloudy"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm"
    return "cloudy"


def _silhouette(code, is_day, size):
    """Everything filled solid white on black — the outline comes later."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    kind = _kind(code)
    cx = size / 2

    if kind == "clear":
        if is_day:
            _sun(draw, cx, size * 0.48, size * 0.24)
        else:
            _moon(draw, cx, size * 0.46, size * 0.24)
            _star(draw, size * 0.24, size * 0.24, size * 0.07)
            _star(draw, size * 0.78, size * 0.70, size * 0.055)
        return mask

    if kind == "partly":
        if is_day:
            _sun(draw, size * 0.36, size * 0.32, size * 0.155)
        else:
            _star(draw, size * 0.46, size * 0.20, size * 0.095)
            _star(draw, size * 0.24, size * 0.34, size * 0.075)
            _star(draw, size * 0.70, size * 0.30, size * 0.06)
        _cloud(draw, size * 0.56, size * 0.62, size * 0.66)
        return mask

    if kind == "fog":
        _cloud(draw, cx, size * 0.44, size * 0.70)
        # Well separated: the outline dilation eats ~2*stroke of the gaps.
        for i in range(3):
            y = size * (0.70 + i * 0.125)
            inset = size * (0.14 + i * 0.05)
            draw.line([(inset, y), (size - inset, y)],
                      fill=255, width=max(2, int(size * 0.03)))
        return mask

    _cloud(draw, cx, size * 0.42, size * 0.72)
    if kind == "rain":
        _drops(draw, cx, size * 0.72, size * 0.60)
    elif kind == "snow":
        _flakes(draw, cx, size * 0.74, size * 0.60)
    elif kind == "storm":
        _bolt(draw, cx, size * 0.78, size * 0.72)
    return mask


def get(code, is_day, size, stroke=None):
    """Return (image, mask) in mode "L" — white shapes, black outline."""
    if stroke is None:
        stroke = max(2, int(size * 0.035))

    core = _silhouette(code, is_day, size)
    outer = _dilate(core, stroke)

    image = Image.new("L", (size, size), WHITE)
    image.paste(Image.new("L", (size, size), BLACK), (0, 0), outer)
    image.paste(Image.new("L", (size, size), WHITE), (0, 0), core)
    return image, outer


def ghost(code, is_day, size, level=238):
    """The oversized watermark version: outline only, very pale."""
    core = _silhouette(code, is_day, size)
    stroke = max(3, int(size * 0.022))
    ring = Image.new("L", (size, size), 0)
    ring.paste(_dilate(core, stroke), (0, 0))
    ring.paste(Image.new("L", (size, size), 0), (0, 0), core)

    image = Image.new("L", (size, size), WHITE)
    image.paste(Image.new("L", (size, size), level), (0, 0), ring)
    return image, ring


# --- small line icons for the hourly table's legend column -----------------

def _legend_clock(draw, s):
    m = s * 0.10
    draw.ellipse([m, m, s - m, s - m], outline=255, width=max(2, int(s * 0.08)))
    c = s / 2
    draw.line([(c, c), (c, c - s * 0.26)], fill=255, width=max(2, int(s * 0.07)))
    draw.line([(c, c), (c + s * 0.20, c)], fill=255, width=max(2, int(s * 0.07)))


def _legend_thermometer(draw, s):
    w = max(2, int(s * 0.07))
    x = s * 0.42
    draw.line([(x, s * 0.14), (x, s * 0.62)], fill=255, width=int(s * 0.18))
    draw.ellipse([x - s * 0.17, s * 0.58, x + s * 0.17, s * 0.92], fill=255)
    for i in range(3):
        y = s * (0.24 + i * 0.13)
        draw.line([(x + s * 0.14, y), (x + s * 0.30, y)], fill=255, width=w)


def _legend_wind(draw, s):
    w = max(2, int(s * 0.09))
    for i, (y, length) in enumerate(((0.30, 0.62), (0.50, 0.80), (0.70, 0.50))):
        draw.line([(s * 0.10, s * y), (s * length, s * y)], fill=255, width=w)
        draw.arc([s * (length - 0.14), s * (y - 0.14), s * (length + 0.14), s * (y + 0.14)],
                 start=-90, end=140, fill=255, width=w)


def _legend_drops(draw, s):
    for cx, cy, r in ((0.34, 0.62, 0.17), (0.66, 0.44, 0.13)):
        x, y, rr = s * cx, s * cy, s * r
        draw.ellipse([x - rr, y - rr * 0.6, x + rr, y + rr * 1.3], fill=255)
        draw.polygon([(x - rr, y), (x + rr, y), (x, y - rr * 1.7)], fill=255)


_LEGEND = {
    "clock": _legend_clock,
    "thermometer": _legend_thermometer,
    "wind": _legend_wind,
    "drops": _legend_drops,
}


def legend(name, size, stroke=None):
    """A small outlined legend glyph. Returns (image, mask), mode "L"."""
    if stroke is None:
        stroke = max(1, int(size * 0.045))
    core = Image.new("L", (size, size), 0)
    _LEGEND[name](ImageDraw.Draw(core), size)
    outer = _dilate(core, stroke)

    image = Image.new("L", (size, size), WHITE)
    image.paste(Image.new("L", (size, size), BLACK), (0, 0), outer)
    image.paste(Image.new("L", (size, size), WHITE), (0, 0), core)
    return image, outer


def wind_arrow(size, degrees, fill=90):
    """A filled arrowhead pointing where the wind is blowing *to*.

    Open-Meteo reports the direction the wind comes *from*, so callers add 180
    the way the reference dashboard does.
    """
    # Draw big and downsample: PIL has no anti-aliased polygons.
    scale = 4
    s = size * scale
    canvas = Image.new("L", (s, s), 0)
    draw = ImageDraw.Draw(canvas)
    draw.polygon([
        (s * 0.50, s * 0.10),
        (s * 0.88, s * 0.88),
        (s * 0.50, s * 0.66),
        (s * 0.12, s * 0.88),
    ], fill=255)
    canvas = canvas.rotate(-degrees, resample=Image.BICUBIC)
    mask = canvas.resize((size, size), Image.LANCZOS)

    image = Image.new("L", (size, size), WHITE)
    image.paste(Image.new("L", (size, size), fill), (0, 0), mask)
    return image, mask
