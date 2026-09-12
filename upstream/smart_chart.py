"""Choose and draw the useful forecast for Today/Tomorrow (no network or browser JS)."""
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import math

LOG = logging.getLogger('nookpanel.smart_chart')


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def speed(forecast, gust=False):
    wind = forecast.get('wind') or {}
    value = number(wind.get('gust' if gust else 'value'))
    if value is None:
        return None
    unit = wind.get('unit', 'kmh')
    return value * {'mph': 1.609344, 'm/s': 3.6, 'kn': 1.852}.get(unit, 1)


def hour_label(value):
    return value.strftime('%I%p').lstrip('0').lower()


@dataclass
class Chart:
    kind: str
    title: str
    reason: str
    unit: str
    hours: list
    values: list


def choose_chart(forecasts, tomorrow=False, now=None):
    hours = sorted((f for f in (forecasts or []) if isinstance(f.get('dt'), datetime)),
                   key=lambda f: f['dt'])
    if not hours:
        return None
    if not tomorrow:
        now = now or datetime.now(tz=hours[0]['dt'].tzinfo)
        hours = [f for f in hours if now <= f['dt']]
        if not hours:
            return None
        relevant = [f for f in hours if f['dt'] <= now + timedelta(hours=5)]
    else:
        relevant = hours  # Tomorrow's complete 06:00–21:00 window, not tonight.

    def wet(f):
        probability = number(f.get('rain_probability'))
        amount = number(f.get('precipitation_mm'))
        code = number(f.get('weather_code'))
        return ((probability is not None and probability >= 40)
                or (amount is not None and amount >= 0.1)
                or code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
                            71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99})

    rain = next((f for f in relevant if wet(f)), None)
    winds = [speed(f) for f in hours]
    gusts = [speed(f, True) for f in hours]
    peak_wind = max((v for v in winds if v is not None), default=0)
    peak_gust = max((v for v in gusts if v is not None), default=0)
    uv = [number(f.get('uv_index')) if f.get('is_day') != 0 else 0 for f in hours]
    peak_uv = max((v for v in uv if v is not None), default=0)
    sunny = any(f.get('is_day') == 1 and number(f.get('cloud_cover')) is not None
                and number(f.get('cloud_cover')) <= 40 for f in hours)

    cloudy_wind = any((number(f.get('cloud_cover')) or 0) >= 60
                      and ((speed(f) or 0) >= 20 or (speed(f, True) or 0) >= 35)
                      for f in hours)

    if rain:
        kind, title, unit = 'precipitation', 'Chance of precipitation', '%'
        reason = 'Precipitation possible at ' + hour_label(rain['dt'])
        values = [number(f.get('rain_probability')) for f in hours]
    elif peak_wind >= 30 or peak_gust >= 45 or cloudy_wind:
        kind = 'wind'
    elif peak_uv >= 3:
        kind = 'uv'
    elif peak_wind >= 20 or peak_gust >= 35:
        kind = 'wind'
    elif sunny and peak_uv > 0:
        kind = 'uv'
    else:
        kind = 'temperature'

    if kind == 'wind':
        # Select using km/h thresholds, display in the provider's configured units.
        unit = (next((f.get('wind') for f in hours if f.get('wind')), {}) or {}).get('unit', 'kmh')
        unit = {'kmh': 'km/h'}.get(unit, unit)
        factor = {'mph': 1.609344, 'm/s': 3.6, 'kn': 1.852}.get(unit, 1)
        title = 'Wind speed'
        reason = (f'Gusts up to {peak_gust / factor:.0f} {unit}' if peak_gust
                  else f'Wind up to {peak_wind / factor:.0f} {unit}')
        values = [v / factor if v is not None else None for v in winds]
    elif kind == 'uv':
        title, unit = 'UV index', ''
        level = 'Low' if peak_uv < 3 else 'Moderate' if peak_uv < 6 else 'High' if peak_uv < 8 else 'Very high' if peak_uv < 11 else 'Extreme'
        reason, values = f'{level} · peak {peak_uv:g}', uv
    elif kind == 'temperature':
        title = 'Temperature'
        unit = next(((f.get('temperature') or {}).get('unit') for f in hours
                     if (f.get('temperature') or {}).get('unit')), '°C')
        values = [number((f.get('temperature') or {}).get('value')) for f in hours]
        reason = 'Hourly outlook'

    # Missing data is never silently turned into zero. An unavailable metric can
    # fall back to temperature, or simply omit the chart if that is absent too.
    if not any(v is not None for v in values):
        if kind != 'temperature':
            values = [number((f.get('temperature') or {}).get('value')) for f in hours]
            kind, title, reason = 'temperature', 'Temperature', 'Hourly outlook'
            unit = next(((f.get('temperature') or {}).get('unit') for f in hours
                         if (f.get('temperature') or {}).get('unit')), '°C')
        if not any(v is not None for v in values):
            return None

    # Tomorrow uses 2-hour buckets to fit. Decide using every hour first, then
    # show each bucket's peak so a shower/UV/wind spike between labels survives.
    if tomorrow:
        buckets = [list(zip(hours[i:i+2], values[i:i+2])) for i in range(0, len(hours), 2)]
        hours = [bucket[0][0] for bucket in buckets]
        values = [max((v for _, v in bucket if v is not None), default=None) for bucket in buckets]
        reason += ' · tomorrow, 2h peaks'
    else:
        reason += ' · upcoming hours'
    return Chart(kind, title, reason, unit, hours, values)


def draw_chart(a, chart):
    if chart is None:
        return
    LOG.info('Selected %s: %s', chart.kind, chart.reason)
    valid = [v for v in chart.values if v is not None]
    if chart.kind == 'precipitation':
        lower, upper = 0, max(40, math.ceil(max(valid) / 20) * 20)
    elif chart.kind == 'uv':
        lower, upper = 0, max(3, math.ceil(max(valid)))
    elif chart.kind == 'wind':
        lower, upper = 0, max(20, math.ceil(max(valid) / 10) * 10)
    else:
        lower = math.floor(min(valid) / 5) * 5
        upper = max(lower + 5, math.ceil(max(valid) / 5) * 5)
    left, right, top, bottom = 42, 980, 36, 246
    slot = (right - left) / len(chart.hours)
    bar_w = slot * 0.62
    def y(value):
        return bottom - (value - lower) / (upper - lower) * (bottom - top)
    def label(value):
        return f'{value:g}' + ('%' if chart.kind == 'precipitation' else '')

    with a.div(id='day-precip', **{'data-metric': chart.kind}):
        a.p(klass='day-precip-title', _t=chart.title + (f' ({chart.unit})' if chart.unit and chart.unit != '%' else ''))
        a.p(klass='day-chart-reason', _t=chart.reason)
        with a.svg(viewBox='0 0 1000 300', preserveAspectRatio='none', klass='day-precip-chart'):
            with a.defs():
                with a.pattern(id='hatch', width='7', height='7', patternUnits='userSpaceOnUse', patternTransform='rotate(45)'):
                    a.line(x1='0', y1='0', x2='0', y2='7', stroke='#000', **{'stroke-width': '2.4'})
            a.line(x1=str(left), y1=str((top + bottom) / 2), x2=str(right), y2=str((top + bottom) / 2), stroke='#000', **{'stroke-width': '1.5', 'stroke-dasharray': '6 9', 'opacity': '0.35'})
            a.text(x=str(left), y='24', klass='day-precip-scale', _t=label(upper))
            if chart.kind == 'temperature':
                a.text(x=str(left - 20), y=str(bottom), klass='day-precip-scale', _t=label(lower))
            previous = None
            for i, (forecast, value) in enumerate(zip(chart.hours, chart.values)):
                x = left + slot * (i + 0.5)
                if value is None:
                    a.text(x=f'{x:.1f}', y=str(bottom - 8), klass='day-precip-value', _t='–')
                    previous = None
                elif chart.kind == 'temperature':
                    point = (x, y(value))
                    if previous:
                        a.line(x1=f'{previous[0]:.1f}', y1=f'{previous[1]:.1f}', x2=f'{x:.1f}', y2=f'{point[1]:.1f}', stroke='#000', **{'stroke-width': '4'})
                    a.circle(cx=f'{x:.1f}', cy=f'{point[1]:.1f}', r='5', fill='#000')
                    a.text(x=f'{x:.1f}', y=f'{point[1]-10:.1f}', klass='day-precip-value', _t=label(value))
                    previous = point
                else:
                    if value > 0:
                        a.rect(x=f'{x - bar_w/2:.1f}', y=f'{y(value):.1f}', width=f'{bar_w:.1f}', height=f'{bottom-y(value):.1f}', fill='url(#hatch)', stroke='#000', **{'stroke-width': '3'})
                    a.text(x=f'{x:.1f}', y=f'{y(value)-9:.1f}', klass='day-precip-value', _t=label(value))
                if i % 2 == 0 or len(chart.hours) <= 8:
                    a.text(x=f'{x:.1f}', y=str(bottom + 34), klass='day-precip-hour', _t=hour_label(forecast['dt']))
            a.line(x1=str(left), y1=str(bottom), x2=str(right), y2=str(bottom), stroke='#000', **{'stroke-width': '3'})
