"""Shared validation rules for the batch and live learning pipelines."""

from __future__ import annotations

from math import isfinite
from typing import Any


NUMERIC_RANGES = {
    "temperature_c": (5.0, 60.0),
    "pressure_kpa": (90.0, 110.0),
    "airflow_m3_h": (100.0, 10_000.0),
    "co2_in_ppm": (350.0, 600.0),
    "co2_out_ppm": (100.0, 600.0),
    "fan_power_kw": (1.0, 100.0),
    "capture_rate_kg_h": (0.01, 20.0),
}
REQUIRED_FIELDS = ("timestamp_utc", "plant_id", *NUMERIC_RANGES)


def _is_missing(value: Any) -> bool:
    if value is None or (isinstance(value, str) and not value.strip()):
        return True
    try:
        return bool(value != value)
    except (TypeError, ValueError):
        return False


def _as_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def validate_reading(row: dict[str, Any]) -> list[str]:
    """Return plain-English rejection reasons; an empty list means valid."""
    reasons: list[str] = []
    for field in REQUIRED_FIELDS:
        value = row.get(field)
        if _is_missing(value):
            reasons.append(f"missing required value: {field}")

    numeric: dict[str, float] = {}
    for field, (minimum, maximum) in NUMERIC_RANGES.items():
        value = _as_number(row.get(field))
        if value is None:
            if not any(reason.endswith(field) for reason in reasons):
                reasons.append(f"missing or invalid value: {field}")
            continue
        numeric[field] = value
        if not minimum <= value <= maximum:
            reasons.append(f"{field} out of range")

    if {"co2_in_ppm", "co2_out_ppm"} <= numeric.keys():
        if numeric["co2_out_ppm"] >= numeric["co2_in_ppm"]:
            reasons.append("outlet CO2 not lower than inlet CO2")
    return reasons
