"""Create simulated SCADA historian data for a small Direct Air Capture plant.

The data is intentionally synthetic. A few missing, duplicate and abnormal
records are included so the ETL pipeline has realistic quality checks to do.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import random

import pandas as pd


OUTPUT = Path("data/raw/dac_scada_readings.csv")
RANDOM_SEED = 42


def main() -> None:
    random.seed(RANDOM_SEED)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # A fixed start time makes the complete generated file reproducible.
    start = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    readings: list[dict[str, object]] = []

    # One SCADA historian record every five minutes for two days.
    for index in range(576):
        timestamp = start + timedelta(minutes=5 * index)
        temperature = 24 + random.uniform(-2.5, 2.5)
        pressure = 101.3 + random.uniform(-1.2, 1.2)
        airflow = 5_000 + random.uniform(-500, 500)
        co2_in = 425 + random.uniform(-12, 12)
        capture_efficiency = 0.42 + random.uniform(-0.05, 0.05)
        co2_out = co2_in * (1 - capture_efficiency)
        fan_power = 35 + random.uniform(-3, 3)
        capture_rate = airflow * (co2_in - co2_out) * 1.96e-6

        readings.append(
            {
                "timestamp_utc": timestamp.isoformat(),
                "plant_id": "DAC-DEMO-01",
                "source_tag": "OPCUA_SIMULATOR",
                "temperature_c": round(temperature, 2),
                "pressure_kpa": round(pressure, 2),
                "airflow_m3_h": round(airflow, 2),
                "co2_in_ppm": round(co2_in, 2),
                "co2_out_ppm": round(co2_out, 2),
                "fan_power_kw": round(fan_power, 2),
                "capture_rate_kg_h": round(capture_rate, 3),
            }
        )

    # Simulate common operational-data problems.
    readings[35]["temperature_c"] = None                 # missing sensor value
    readings[120]["airflow_m3_h"] = -20                   # invalid physical value
    readings[220]["co2_out_ppm"] = 900                    # outlet > inlet
    readings[330]["fan_power_kw"] = 500                   # unlikely spike
    readings.append(readings[250].copy())                  # duplicate historian record
    readings.append(readings[400].copy())                  # duplicate historian record

    pd.DataFrame(readings).to_csv(OUTPUT, index=False)
    print(f"Created {len(readings)} raw SCADA records: {OUTPUT}")


if __name__ == "__main__":
    main()
