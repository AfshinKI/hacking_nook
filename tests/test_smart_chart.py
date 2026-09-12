from datetime import datetime, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'upstream'))
from smart_chart import choose_chart

NOW = datetime(2026, 9, 12, 10, 30)


def hours(count=9):
    return [dict(dt=NOW.replace(minute=0) + timedelta(hours=i+1),
                 rain_probability=0, precipitation_mm=0, weather_code=3,
                 uv_index=0, cloud_cover=90, is_day=1,
                 wind={'unit': 'kmh', 'value': 5, 'gust': 10},
                 temperature={'unit': '°C', 'value': 15+i}) for i in range(count)]


class SmartChart(unittest.TestCase):
    def choose(self, data, **kwargs):
        return choose_chart(data, now=NOW, **kwargs)

    def test_rain_within_five_hours_wins_over_uv_and_wind(self):
        data = hours()
        data[4].update(rain_probability=40, uv_index=8)
        data[0]['wind']['value'] = 40
        self.assertEqual(self.choose(data).kind, 'precipitation')

    def test_later_rain_does_not_override_today(self):
        data = hours()
        data[5]['rain_probability'] = 90
        data[1]['uv_index'] = 5
        self.assertEqual(self.choose(data).kind, 'uv')

    def test_five_hour_boundary(self):
        data = hours()
        data[4]['dt'] = NOW + timedelta(hours=5)
        data[4]['precipitation_mm'] = 0.1
        self.assertEqual(self.choose(data).kind, 'precipitation')
        data[4]['dt'] += timedelta(minutes=1)
        self.assertEqual(self.choose(data).kind, 'temperature')

    def test_snow_and_thunder_are_precipitation(self):
        for code in (71, 85, 95):
            data = hours()
            data[0]['weather_code'] = code
            self.assertEqual(self.choose(data).kind, 'precipitation')

    def test_sunny_uv_and_cloudy_wind(self):
        data = hours()
        data[1].update(cloud_cover=10, uv_index=2)
        self.assertEqual(self.choose(data).kind, 'uv')
        data[1]['wind']['value'] = 25
        self.assertEqual(self.choose(data).kind, 'wind')

    def test_cloudy_windy_hour_prioritizes_wind_but_sunny_hour_prioritizes_uv(self):
        data = hours()
        data[1].update(uv_index=4, cloud_cover=90)
        data[1]['wind']['value'] = 25
        self.assertEqual(self.choose(data).kind, 'wind')
        data[1]['cloud_cover'] = 10
        self.assertEqual(self.choose(data).kind, 'uv')

    def test_strong_wind_over_uv(self):
        data = hours()
        data[1]['uv_index'] = 7
        data[1]['wind']['gust'] = 45
        self.assertEqual(self.choose(data).kind, 'wind')

    def test_imperial_speed_threshold_and_labels(self):
        data = hours()
        for row in data:
            row['wind'] = {'unit': 'mph', 'value': 20, 'gust': 30}
        chart = self.choose(data)
        self.assertEqual(chart.kind, 'wind')
        self.assertEqual(chart.unit, 'mph')
        self.assertEqual(chart.values[0], 20)
        self.assertIn('30 mph', chart.reason)

    def test_night_does_not_show_uv(self):
        data = hours()
        for row in data:
            row.update(is_day=0, uv_index=6, cloud_cover=0)
        self.assertEqual(self.choose(data).kind, 'temperature')

    def test_missing_values_are_not_zero_and_empty_data_is_safe(self):
        data = hours()
        data[0]['rain_probability'] = None
        data[1]['rain_probability'] = 70
        self.assertIsNone(self.choose(data).values[0])
        self.assertIsNone(self.choose([]))
        self.assertIsNone(self.choose([{'dt': NOW + timedelta(hours=1)}]))
        data[2]['rain_probability'] = float('nan')
        self.assertIsNone(self.choose(data).values[2])

    def test_tomorrow_checks_every_hour_and_preserves_between_label_peak(self):
        data = hours(16)
        for i, row in enumerate(data):
            row['dt'] = NOW.replace(hour=6, minute=0) + timedelta(days=1, hours=i)
        data[9]['rain_probability'] = 85  # 3pm, omitted by the old step=2 fetch
        chart = self.choose(data, tomorrow=True)
        self.assertEqual(chart.kind, 'precipitation')
        self.assertEqual(len(chart.hours), 8)
        self.assertEqual(chart.values[4], 85)
        self.assertIn('3pm', chart.reason)

    def test_tomorrow_uv_and_negative_temperature(self):
        data = hours()
        for row in data:
            row['dt'] += timedelta(days=1)
            row['temperature']['value'] = -12
        self.assertEqual(self.choose(data, tomorrow=True).values[0], -12)
        data[3]['uv_index'] = 6
        chart = self.choose(data, tomorrow=True)
        self.assertEqual(chart.kind, 'uv')
        self.assertIn(6, chart.values)

    def test_elapsed_forecasts_are_not_used(self):
        data = hours()
        data[0]['dt'] = NOW - timedelta(hours=1)
        data[0]['rain_probability'] = 100
        self.assertEqual(self.choose(data).kind, 'temperature')


if __name__ == '__main__':
    unittest.main()
