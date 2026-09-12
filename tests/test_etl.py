"""Tests for the SCADA ETL validation logic.

Simple English: each test builds a tiny fake table of 1-2 rows,
runs it through validate_and_transform, and checks the result is
what we expect. This proves the rules actually work, not just that
the script runs without crashing.
"""
from __future__ import annotations

import pandas as pd

from run_etl import validate_and_transform


def _make_row(**overrides):
    """A single 'good' reading. Tests override one field to break it."""
    row = {
        "timestamp_utc": "2026-01-01T00:00:00Z",
        "plant_id": "PLANT_1",
        "temperature_c": 25.0,
        "pressure_kpa": 100.0,
        "airflow_m3_h": 5000.0,
        "co2_in_ppm": 420.0,
        "co2_out_ppm": 300.0,
        "fan_power_kw": 10.0,
        "capture_rate_kg_h": 5.0,
    }
    row.update(overrides)
    return row


def test_valid_row_is_kept():
    df = pd.DataFrame([_make_row()])
    clean, stats = validate_and_transform(df)
    assert len(clean) == 1
    assert stats["valid_records_loaded"] == 1
    assert stats["range_or_logic_records_removed"] == 0


def test_duplicate_timestamp_is_removed():
    df = pd.DataFrame([_make_row(), _make_row()])  # exact duplicate
    clean, stats = validate_and_transform(df)
    assert len(clean) == 1
    assert stats["duplicates_removed"] == 1


def test_out_of_range_temperature_is_rejected():
    df = pd.DataFrame([_make_row(temperature_c=200.0)])  # impossible value
    clean, stats = validate_and_transform(df)
    assert len(clean) == 0
    assert stats["range_or_logic_records_removed"] == 1


def test_outlet_co2_must_be_lower_than_inlet():
    # physically impossible: more CO2 leaving than entering
    df = pd.DataFrame([_make_row(co2_in_ppm=400.0, co2_out_ppm=450.0)])
    clean, stats = validate_and_transform(df)
    assert len(clean) == 0


def test_missing_required_value_is_removed():
    df = pd.DataFrame([_make_row(temperature_c=None)])
    clean, stats = validate_and_transform(df)
    assert len(clean) == 0
    assert stats["missing_records_removed"] == 1
