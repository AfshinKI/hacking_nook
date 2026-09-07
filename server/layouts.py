"""Panel layouts.

`today` is the headline view, modelled on Chris Twomey's inkplate10-weather-cal:
a pale city map bleeding into white, a big outlined weather icon straddling the
fade, then the date, temperature and conditions in rounded hand-lettering, with
an oversized ghost of the icon watermarked into the bottom corner.

`simple` is the original dense view — clock plus a three-day table — for when
you want more numbers than atmosphere.

Everything renders in mode "L". Pure black on white: e-ink has 16 grey levels
and very little contrast to spare, so greys are reserved for de-emphasis.
"""

from datetime import datetime

from PIL import Image, ImageDraw

import fonts
import icons
import mapview
import weather as wx

BLACK = 0
GREY = 128
PALE = 190


def _centre(draw, y, text, font, fill=BLACK, width=600):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text(((width - (right - left)) / 2 - left, y - top), text, font=font, fill=fill)
    return bottom - top


def _text_size(draw, text, font):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def render_today(config, weather, now, cache_dir):
    width, height = 600, 800
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)

    code = int(weather.current("weather_code", 3) or 3)
    is_day = bool(weather.current("is_day", 1))

    # --- ghost watermark, first so everything else lands on top -----------
    # Sits low and left, mostly cropped by the panel edges, pale enough that the
    # text always wins. Any darker and it fights the "feels like" line.
    ghost_size = int(width * 0.92)
    ghost, ghost_mask = icons.ghost(code, is_day, ghost_size, level=243)
    image.paste(ghost, (int(-width * 0.30), int(height - ghost_size * 0.60)), ghost_mask)

    # --- map ---------------------------------------------------------------
    map_h = 420
    city_map = mapview.get(
        config["latitude"], config["longitude"], config.get("map_zoom", 11),
        width, map_h, cache_dir, strength=config.get("map_strength", 0.55))
    if city_map is not None:
        image.paste(city_map, (0, 0))

    # --- weather icon, straddling the map fade -----------------------------
    icon_size = 210
    icon, icon_mask = icons.get(code, is_day, icon_size)
    image.paste(icon, ((width - icon_size) // 2, 185), icon_mask)

    # --- date --------------------------------------------------------------
    y = 420
    f_date = fonts.load(34, "regular")
    _centre(draw, y, now.strftime("%A, %B %-d"), f_date, GREY)
    y += 54

    # --- temperature: big current, small low beside it ---------------------
    unit = weather.unit
    temp = weather.current("temperature_2m")
    low = weather.today("temperature_2m_min")

    f_big = fonts.load(120, "bold")
    f_low = fonts.load(52, "light")

    big_text = "—" if temp is None else f"{round(temp)}°{unit}"
    low_text = "" if low is None else f"{round(low)}°"

    big_w, big_h = _text_size(draw, big_text, f_big)
    low_w, low_h = _text_size(draw, low_text, f_low) if low_text else (0, 0)
    gap = 18 if low_text else 0

    block_w = low_w + gap + big_w
    x = (width - block_w) / 2
    baseline = y + big_h

    if low_text:
        lb = draw.textbbox((0, 0), low_text, font=f_low)
        draw.text((x - lb[0], baseline - lb[3]), low_text, font=f_low, fill=PALE)
    bb = draw.textbbox((0, 0), big_text, font=f_big)
    draw.text((x + low_w + gap - bb[0], baseline - bb[3]), big_text, font=f_big, fill=BLACK)
    y = baseline + 16

    # --- feels like / conditions / rain ------------------------------------
    f_small = fonts.load(28, "light")
    f_cond = fonts.load(38, "regular")

    feels = weather.current("apparent_temperature")
    if feels is not None:
        _centre(draw, y, f"Feels like {round(feels)}°", f_small, GREY)
        y += 44

    _centre(draw, y, wx.describe(code), f_cond, BLACK)
    y += 52

    pop = weather.today("precipitation_probability_max")
    if pop is not None:
        _centre(draw, y, f"{pop}% rain", f_small, GREY)
        y += 40

    # --- footer: attribution and freshness ---------------------------------
    f_tiny = fonts.load(15, "light")
    draw.text((14, height - 24), "© OpenStreetMap contributors", font=f_tiny, fill=PALE)
    stamp = now.strftime("updated %H:%M")
    tw, _ = _text_size(draw, stamp, f_tiny)
    draw.text((width - tw - 14, height - 24), stamp, font=f_tiny, fill=PALE)

    return image


def render_simple(config, weather, now, cache_dir=None):
    """The original layout: clock, current conditions, three-day table."""
    width, height = 600, 800
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)

    f_huge = fonts.load(150, "bold")
    f_big = fonts.load(52, "bold")
    f_med = fonts.load(32, "bold")
    f_small = fonts.load(24, "regular")
    f_tiny = fonts.load(18, "light")

    margin = 28
    y = margin
    draw.text((margin, y), now.strftime("%H:%M"), font=f_huge, fill=BLACK)
    y += 165
    draw.text((margin, y), now.strftime("%A"), font=f_big, fill=BLACK)
    y += 60
    draw.text((margin, y), now.strftime("%d %B %Y"), font=f_med, fill=BLACK)
    y += 52
    draw.line([(margin, y), (width - margin, y)], fill=BLACK, width=3)
    y += 24

    unit = weather.unit
    temp = weather.current("temperature_2m")
    if temp is not None:
        draw.text((margin, y), f"{round(temp)}°{unit}", font=f_big, fill=BLACK)
        draw.text((margin + 200, y + 6), wx.describe(weather.current("weather_code", 3)),
                  font=f_med, fill=BLACK)
        y += 62
        draw.text((margin, y),
                  f"Feels {round(weather.current('apparent_temperature'))}°"
                  f"  ·  {weather.current('relative_humidity_2m')}% RH"
                  f"  ·  wind {round(weather.current('wind_speed_10m'))}",
                  font=f_small, fill=BLACK)
        y += 44
        draw.text((margin, y), config.get("location_name", ""), font=f_small, fill=BLACK)
        y += 46
        draw.line([(margin, y), (width - margin, y)], fill=BLACK, width=1)
        y += 20

        for i in range(1, min(4, len(weather.daily_dates()))):
            day = datetime.fromisoformat(weather.daily_dates()[i]).strftime("%a")
            hi = round(weather.daily("temperature_2m_max", i))
            lo = round(weather.daily("temperature_2m_min", i))
            pop = weather.daily("precipitation_probability_max", i)
            draw.text((margin, y), day, font=f_med, fill=BLACK)
            draw.text((margin + 90, y + 4), f"{hi}° / {lo}°", font=f_small, fill=BLACK)
            draw.text((margin + 230, y + 4),
                      wx.describe(weather.daily("weather_code", i, 3)),
                      font=f_small, fill=BLACK)
            if pop is not None:
                draw.text((width - margin - 70, y + 4), f"{pop}%", font=f_small, fill=BLACK)
            y += 48
    else:
        draw.text((margin, y), "Weather unavailable", font=f_med, fill=BLACK)

    draw.text((margin, height - margin - 20), now.strftime("updated %H:%M"),
              font=f_tiny, fill=BLACK)
    return image


# --- hourly view -----------------------------------------------------------

def _rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _badge(image, draw, cx, cy, radius, fill=BLACK):
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill)


def _centred_in(draw, cx, cy, text, font, fill):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (right - left) / 2 - left, cy - (bottom - top) / 2 - top),
              text, font=font, fill=fill)


def _hatched_bar(width, height, angle_gap=6):
    """A bar filled with 45° hatching and a heavy outline.

    Stands in for rough.js's sketchy zigzag fill, which the reference draws in a
    browser canvas. Flat hatching reads better on e-ink anyway — dithered noise
    is the one thing this panel cannot show.
    """
    bar = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(bar)
    for offset in range(-height, width + height, angle_gap):
        draw.line([(offset, height), (offset + height, 0)], fill=110, width=1)
    draw.rectangle([0, 0, width - 1, height - 1], outline=BLACK, width=2)
    return bar


def render_hourly(config, weather, now, cache_dir):
    width, height = 600, 800
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)

    map_h = 390
    city_map = mapview.get(
        config["latitude"], config["longitude"], config.get("map_zoom", 11),
        width, map_h, cache_dir,
        strength=config.get("map_strength", 0.70), style="dark", fade="left_bottom")
    if city_map is not None:
        image.paste(city_map, (0, 0))

    unit = weather.unit
    code = int(weather.current("weather_code", 3) or 3)
    is_day = bool(weather.current("is_day", 1))

    # --- date pill: black day-number disc biting into a white month plate --
    f_day = fonts.load(52, "bold")
    f_month = fonts.load(38, "bold")
    month = now.strftime("%b").upper()

    disc_r, disc_cx, disc_cy = 46, 66, 66
    month_w = draw.textbbox((0, 0), month, font=f_month)[2]
    _rounded_rect(draw, [40, disc_cy - 40, disc_cx + disc_r + month_w + 34, disc_cy + 40],
                  40, 255)
    _badge(image, draw, disc_cx, disc_cy, disc_r)
    _centred_in(draw, disc_cx, disc_cy - 2, now.strftime("%-d"), f_day, 255)
    _centred_in(draw, disc_cx + disc_r + 18 + month_w / 2, disc_cy - 2, month, f_month, BLACK)

    # --- temperature and condition badges ---------------------------------
    f_badge = fonts.load(26, "bold")
    temp = weather.current("temperature_2m")
    badge_r = 40

    _badge(image, draw, 66, 168, badge_r)
    _centred_in(draw, 66, 168, "—" if temp is None else f"{round(temp)}°{unit}",
                f_badge, 255)

    _badge(image, draw, 66, 262, badge_r)
    icon, icon_mask = icons.get(code, is_day, 62)
    # White-on-black inside the disc.
    image.paste(Image.eval(icon, lambda v: 255 - v), (66 - 31, 262 - 31), icon_mask)

    # --- hourly table ------------------------------------------------------
    forecasts = weather.hourly_from_now(now, count=9)
    if not forecasts:
        _centre(draw, 500, "No hourly forecast", fonts.load(30, "regular"), GREY)
        return image

    legend_w = 58
    col_w = (width - legend_w) / len(forecasts)

    row_icon, row_hour, row_temp, row_wind, row_precip = 398, 476, 510, 544, 612
    precip_bottom = 778

    f_hour = fonts.load(21, "bold")
    f_temp = fonts.load(22, "bold")
    f_wind = fonts.load(18, "regular")
    f_unit = fonts.load(13, "light")
    f_pct = fonts.load(18, "bold")

    def col_centre(i):
        return legend_w + col_w * (i + 0.5)

    # Legend column, then the dashed rule that separates it.
    for name, y, unit_text in (("clock", row_hour + 13, None),
                               ("thermometer", row_temp + 13, f"°{unit}"),
                               ("wind", row_wind + 18, "kph"),
                               ("drops", row_precip + 26, None)):
        glyph, glyph_mask = icons.legend(name, 30)
        image.paste(glyph, (12, int(y - 15)), glyph_mask)
        if unit_text:
            _centred_in(draw, 27, y + 24, unit_text, f_unit, BLACK)

    for y in range(row_icon, precip_bottom, 12):
        draw.line([(legend_w - 6, y), (legend_w - 6, min(y + 6, precip_bottom))],
                  fill=GREY, width=2)

    # Bars are scaled so the wettest hour in the window fills the row, with a
    # floor of 40% so a dry day still draws something rather than a flat line.
    # Every bar carries its true percentage as a label, so nothing is hidden.
    peak = max([f["precipitation_probability"] or 0 for f in forecasts] + [40])

    # Baseline for the precipitation bars. Without it a dry day reads as a
    # broken empty band rather than a chart with nothing in it.
    draw.line([(legend_w, precip_bottom), (width - 8, precip_bottom)],
              fill=GREY, width=1)

    previous_temp = previous_wind = previous_precip = None
    for i, forecast in enumerate(forecasts):
        cx = col_centre(i)
        show_alternate = i % 2 == 0

        glyph, glyph_mask = icons.get(forecast["code"], forecast["is_day"], 64)
        image.paste(glyph, (int(cx - 32), row_icon), glyph_mask)

        if show_alternate:
            label = forecast["time"].strftime("%-I%p").lower()
            _centred_in(draw, cx, row_hour + 13, label, f_hour, BLACK)

        temp_value = round(forecast["temperature"])
        if temp_value != previous_temp:
            _centred_in(draw, cx, row_temp + 13, f"{temp_value}°", f_temp, BLACK)
        previous_temp = temp_value

        # Arrow size tracks wind speed, as in the reference: sqrt-scaled and
        # capped at 80 km/h so a gale does not swamp the row.
        speed = forecast["wind_speed"]
        arrow_px = int(16 + 14 * min(speed / 80.0, 1.0) ** 0.5)
        arrow, arrow_mask = icons.wind_arrow(
            arrow_px, (forecast["wind_direction"] + 180) % 360)
        image.paste(arrow, (int(cx - arrow_px / 2), row_wind + 2), arrow_mask)

        speed_text = str(round(speed))
        if speed_text != previous_wind:
            _centred_in(draw, cx, row_wind + 46, speed_text, f_wind, BLACK)
        previous_wind = speed_text

        precip = forecast["precipitation_probability"] or 0
        bar_w = int(col_w * 0.76)
        bar_h = max(3, int((precip_bottom - row_precip - 26) * precip / peak))
        bar = _hatched_bar(bar_w, bar_h)
        image.paste(bar, (int(cx - bar_w / 2), precip_bottom - bar_h))

        # Label above the bar, but not when it would run off the top.
        if show_alternate and precip != previous_precip and precip < 80:
            _centred_in(draw, cx, precip_bottom - bar_h - 14, f"{precip}%", f_pct, BLACK)
        previous_precip = precip

    f_tiny = fonts.load(15, "light")
    draw.text((14, height - 20), "© OpenStreetMap contributors", font=f_tiny, fill=PALE)
    stamp = now.strftime("updated %H:%M")
    tw, _ = _text_size(draw, stamp, f_tiny)
    draw.text((width - tw - 14, height - 20), stamp, font=f_tiny, fill=PALE)

    return image


LAYOUTS = {
    "today": render_today,
    "hourly": render_hourly,
    "simple": render_simple,
}


def render(config, weather, now, cache_dir):
    name = config.get("layout", "today")
    fn = LAYOUTS.get(name, render_today)
    image = fn(config, weather, now, cache_dir)
    if config.get("landscape"):
        image = image.rotate(90, expand=True)
    return image
