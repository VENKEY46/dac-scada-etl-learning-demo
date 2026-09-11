from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1]))
from run_etl import validate_and_transform


def test_invalid_and_duplicate_records_are_rejected():
    raw = pd.DataFrame([
        {"timestamp_utc": "2026-01-01T00:00:00Z", "plant_id": "P1", "temperature_c": 20, "pressure_kpa": 101, "airflow_m3_h": 5000, "co2_in_ppm": 420, "co2_out_ppm": 240, "fan_power_kw": 35, "capture_rate_kg_h": 1.0},
        {"timestamp_utc": "2026-01-01T00:00:00Z", "plant_id": "P1", "temperature_c": 20, "pressure_kpa": 101, "airflow_m3_h": 5000, "co2_in_ppm": 420, "co2_out_ppm": 240, "fan_power_kw": 35, "capture_rate_kg_h": 1.0},
        {"timestamp_utc": "2026-01-01T00:05:00Z", "plant_id": "P1", "temperature_c": 20, "pressure_kpa": 101, "airflow_m3_h": -1, "co2_in_ppm": 420, "co2_out_ppm": 240, "fan_power_kw": 35, "capture_rate_kg_h": 1.0},
    ])
    clean, stats = validate_and_transform(raw)
    assert len(clean) == 1
    assert stats["duplicates_removed"] == 1
    assert stats["range_or_logic_records_removed"] == 1


def test_derived_kpis_are_present():
    raw = pd.read_csv(Path("data/raw/dac_scada_readings.csv"))
    clean, _ = validate_and_transform(raw)
    for column in ["co2_removed_ppm", "energy_intensity_kwh_per_kg", "capture_efficiency_pct", "cycle_performance_pct", "capacity_utilisation_pct"]:
        assert column in clean.columns
