"""Open-Meteo client. No API key, no account, generous rate limits."""

import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timezone

LOG = logging.getLogger("nookpanel.weather")

# WMO weather interpretation codes, as short phrases that fit the panel.
WMO = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    56: "Freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Rain showers", 81: "Rain showers", 82: "Violent showers",
    85: "Snow showers", 86: "Snow showers",
    95: "Thunderstorm", 96: "Thunder, hail", 99: "Thunder, hail",
}


def describe(code):
    return WMO.get(int(code), "—")


class Weather:
    def __init__(self, config):
        self.config = config
        self.data = None
        self.fetched_at = None

    def fetch(self):
        imperial = self.config.get("units") == "imperial"
        params = {
            "latitude": self.config["latitude"],
            "longitude": self.config["longitude"],
            "current": "temperature_2m,apparent_temperature,weather_code,is_day,"
                       "relative_humidity_2m,wind_speed_10m,precipitation",
            "hourly": "temperature_2m,weather_code,precipitation_probability,"
                      "wind_speed_10m,wind_direction_10m,is_day",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                     "precipitation_probability_max",
            "timezone": self.config["timezone"],
            "forecast_days": 4,
        }
        if imperial:
            params["temperature_unit"] = "fahrenheit"
            params["wind_speed_unit"] = "mph"

        url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=20) as response:
            self.data = json.load(response)
        self.fetched_at = datetime.now(timezone.utc)
        LOG.info("weather updated")
        return self.data

    # --- convenience accessors, all None-safe -----------------------------

    @property
    def unit(self):
        return "F" if self.config.get("units") == "imperial" else "C"

    def current(self, key, default=None):
        if not self.data:
            return default
        return self.data.get("current", {}).get(key, default)

    def today(self, key, default=None):
        return self.daily(key, 0, default)

    def daily(self, key, index, default=None):
        if not self.data:
            return default
        values = self.data.get("daily", {}).get(key)
        if not values or index >= len(values):
            return default
        return values[index]

    def hourly_from_now(self, now, count=9, step=1):
        """The next `count` hourly forecasts at `step`-hour intervals.

        Open-Meteo returns local naive timestamps for the configured timezone,
        so compare against a naive `now` in that same zone.
        """
        if not self.data:
            return []
        hourly = self.data.get("hourly", {})
        times = hourly.get("time", [])
        cursor = now.replace(tzinfo=None)

        start = 0
        for i, stamp in enumerate(times):
            if datetime.fromisoformat(stamp) >= cursor:
                start = i
                break
        else:
            return []

        out = []
        for i in range(start, len(times), step):
            if len(out) == count:
                break
            out.append({
                "time": datetime.fromisoformat(times[i]),
                "temperature": hourly["temperature_2m"][i],
                "code": int(hourly["weather_code"][i]),
                "precipitation_probability": hourly["precipitation_probability"][i],
                "wind_speed": hourly["wind_speed_10m"][i],
                "wind_direction": hourly["wind_direction_10m"][i],
                "is_day": bool(hourly["is_day"][i]),
            })
        return out

    def daily_dates(self):
        if not self.data:
            return []
        return self.data.get("daily", {}).get("time", [])
