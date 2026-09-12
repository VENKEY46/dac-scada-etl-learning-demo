import unittest

from validation import validate_reading


def valid_reading() -> dict:
    return {
        "timestamp_utc": "2026-09-01T00:00:00+00:00",
        "plant_id": "DAC-DEMO-01",
        "source_tag": "SIM",
        "temperature_c": 25.0,
        "pressure_kpa": 101.3,
        "airflow_m3_h": 5000.0,
        "co2_in_ppm": 430.0,
        "co2_out_ppm": 250.0,
        "fan_power_kw": 35.0,
        "capture_rate_kg_h": 2.0,
    }


class ValidationTests(unittest.TestCase):
    def test_valid_reading_passes(self):
        self.assertEqual(validate_reading(valid_reading()), [])

    def test_temperature_fault_is_rejected(self):
        row = valid_reading()
        row["temperature_c"] = 200
        self.assertIn("temperature_c out of range", validate_reading(row))

    def test_wrong_co2_direction_is_rejected(self):
        row = valid_reading()
        row["co2_out_ppm"] = 450
        self.assertIn("outlet CO2 not lower than inlet CO2", validate_reading(row))

    def test_missing_value_is_rejected(self):
        row = valid_reading()
        row["fan_power_kw"] = None
        self.assertIn("missing required value: fan_power_kw", validate_reading(row))


if __name__ == "__main__":
    unittest.main()

