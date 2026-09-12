"""A small SCADA-style Extract, Transform and Load pipeline for learning.

Extract: read synthetic SCADA historian data from CSV.
Transform: validate timestamps, remove duplicates, and reject bad sensor data.
Load: save trusted records to SQLite and create a dashboard + run summary.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd

from validation import NUMERIC_RANGES, validate_reading


RAW_FILE = Path("data/raw/dac_scada_readings.csv")
DATABASE = Path("data/processed/dac_scada.db")
REPORT = Path("output/etl_run_summary.md")
DASHBOARD = Path("output/dac_plant_dashboard.png")
REJECTED = Path("output/rejected_records.csv")


def validate_and_transform(
    raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Return trusted rows, rejected rows with reasons, and run statistics."""
    stats = {"raw_records": len(raw)}
    data = raw.copy()
    data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True, errors="coerce")
    for field in NUMERIC_RANGES:
        data[field] = pd.to_numeric(data[field], errors="coerce")
    data = data.sort_values("timestamp_utc", na_position="last")

    duplicate_mask = data.duplicated(subset=["timestamp_utc", "plant_id"], keep="last")
    duplicate_rows = data.loc[duplicate_mask].copy()
    duplicate_rows["rejection_reason"] = "duplicate timestamp and plant_id"
    candidates = data.loc[~duplicate_mask].copy()

    reasons = candidates.apply(lambda row: validate_reading(row.to_dict()), axis=1)
    valid_mask = reasons.map(len).eq(0)
    clean = candidates.loc[valid_mask].copy()
    invalid_rows = candidates.loc[~valid_mask].copy()
    invalid_rows["rejection_reason"] = reasons.loc[~valid_mask].map("; ".join)
    rejected = pd.concat([duplicate_rows, invalid_rows], ignore_index=True)

    stats["duplicates_removed"] = int(duplicate_mask.sum())
    stats["invalid_records_removed"] = len(invalid_rows)
    stats["rejected_records_logged"] = len(rejected)

    clean["co2_removed_ppm"] = (clean["co2_in_ppm"] - clean["co2_out_ppm"]).round(2)
    clean["energy_intensity_kwh_per_kg"] = (
        clean["fan_power_kw"] / clean["capture_rate_kg_h"]
    ).round(2)
    clean["quality_status"] = "VALID"
    stats["valid_records_loaded"] = len(clean)
    return clean, rejected, stats


def load_to_sqlite(clean: pd.DataFrame) -> None:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE) as connection:
        clean.to_sql("plant_readings", connection, if_exists="replace", index=False)


def write_rejected_records(rejected: pd.DataFrame) -> None:
    REJECTED.parent.mkdir(parents=True, exist_ok=True)
    rejected.to_csv(REJECTED, index=False)


def create_dashboard(clean: pd.DataFrame) -> None:
    DASHBOARD.parent.mkdir(parents=True, exist_ok=True)
    chart_data = clean.set_index("timestamp_utc")
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    fig.suptitle("Synthetic DAC Plant — SCADA ETL Monitoring", fontsize=15, fontweight="bold")

    axes[0].plot(chart_data.index, chart_data["co2_in_ppm"], label="CO₂ entering", color="#1f77b4")
    axes[0].plot(chart_data.index, chart_data["co2_out_ppm"], label="CO₂ leaving", color="#2ca02c")
    axes[0].set_ylabel("CO₂ (ppm)")
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    axes[1].plot(chart_data.index, chart_data["capture_rate_kg_h"], label="Capture rate", color="#9467bd")
    axes[1].set_ylabel("kg CO₂ / hour")
    axes[1].set_xlabel("UTC timestamp")
    axes[1].grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(DASHBOARD, dpi=160)
    plt.close(fig)


def write_report(clean: pd.DataFrame, stats: dict[str, int]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    metrics = {
        "Average CO₂ removed": f"{clean['co2_removed_ppm'].mean():.1f} ppm",
        "Average capture rate": f"{clean['capture_rate_kg_h'].mean():.2f} kg/h",
        "Average fan power": f"{clean['fan_power_kw'].mean():.1f} kW",
        "Average energy intensity": f"{clean['energy_intensity_kwh_per_kg'].mean():.1f} kWh/kg",
    }
    lines = ["# SCADA ETL Run Summary", "", "## Data-quality results", ""]
    lines += [f"- **{name.replace('_', ' ').title()}:** {value}" for name, value in stats.items()]
    lines += ["", "## Plant KPIs", ""]
    lines += [f"- **{name}:** {value}" for name, value in metrics.items()]
    lines += [
        "", "## What this proves", "",
        "This learning demo simulates the basic flow from plant readings to trusted data for analysis.",
        "The values and validation ranges are synthetic; they are not real plant data or company system settings.",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not RAW_FILE.exists():
        raise FileNotFoundError("Run `python generate_scada_data.py` first.")
    raw = pd.read_csv(RAW_FILE)
    clean, rejected, stats = validate_and_transform(raw)
    write_rejected_records(rejected)
    load_to_sqlite(clean)
    create_dashboard(clean)
    write_report(clean, stats)
    print("ETL completed successfully")
    print(f"Database: {DATABASE}")
    print(f"Dashboard: {DASHBOARD}")
    print(f"Summary: {REPORT}")
    print(f"Rejected records: {REJECTED}")


if __name__ == "__main__":
    main()
