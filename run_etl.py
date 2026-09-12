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


RAW_FILE = Path("data/raw/dac_scada_readings.csv")
DATABASE = Path("data/processed/dac_scada.db")
REPORT = Path("output/etl_run_summary.md")
DASHBOARD = Path("output/dac_plant_dashboard.png")
REJECTED = Path("output/rejected_records.csv")
NOMINAL_CAPTURE_EFFICIENCY = 0.42
NOMINAL_CAPACITY_KG_H = 10.0


def validate_and_transform(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Return clean sensor records and counts useful for an ETL log."""
    stats = {"raw_records": len(raw)}
    data = raw.copy()
    data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True, errors="coerce")
    data = data.sort_values("timestamp_utc").drop_duplicates(
        subset=["timestamp_utc", "plant_id"], keep="last"
    )
    stats["duplicates_removed"] = stats["raw_records"] - len(data)

    required = [
        "timestamp_utc", "temperature_c", "pressure_kpa", "airflow_m3_h",
        "co2_in_ppm", "co2_out_ppm", "fan_power_kw", "capture_rate_kg_h",
    ]
    before_missing = len(data)
    data = data.dropna(subset=required)
    stats["missing_records_removed"] = before_missing - len(data)

    # Simple engineering plausibility ranges for this *simulated* learning plant.
    valid = (
        data["temperature_c"].between(5, 60)
        & data["pressure_kpa"].between(90, 110)
        & data["airflow_m3_h"].between(100, 10_000)
        & data["co2_in_ppm"].between(350, 600)
        & data["co2_out_ppm"].between(100, 600)
        & (data["co2_out_ppm"] < data["co2_in_ppm"])
        & data["fan_power_kw"].between(1, 100)
        & data["capture_rate_kg_h"].between(0.01, 20)
    )
    stats["range_or_logic_records_removed"] = int((~valid).sum())

    # Keep the rejected rows with a plain-English reason, instead of just
    # deleting them. A real plant engineer wants to know WHY a reading was
    # rejected, not just how many were rejected.
    rejected = data.loc[~valid].copy()
    if not rejected.empty:
        reasons = []
        for _, row in rejected.iterrows():
            row_reasons = []
            if not (5 <= row["temperature_c"] <= 60):
                row_reasons.append("temperature out of range")
            if not (90 <= row["pressure_kpa"] <= 110):
                row_reasons.append("pressure out of range")
            if not (100 <= row["airflow_m3_h"] <= 10_000):
                row_reasons.append("airflow out of range")
            if not (350 <= row["co2_in_ppm"] <= 600):
                row_reasons.append("CO2 inlet out of range")
            if not (100 <= row["co2_out_ppm"] <= 600):
                row_reasons.append("CO2 outlet out of range")
            if row["co2_out_ppm"] >= row["co2_in_ppm"]:
                row_reasons.append("outlet CO2 not lower than inlet CO2")
            if not (1 <= row["fan_power_kw"] <= 100):
                row_reasons.append("fan power out of range")
            if not (0.01 <= row["capture_rate_kg_h"] <= 20):
                row_reasons.append("capture rate out of range")
            reasons.append("; ".join(row_reasons) if row_reasons else "unknown")
        rejected["rejection_reason"] = reasons
        REJECTED.parent.mkdir(parents=True, exist_ok=True)
        rejected.to_csv(REJECTED, index=False)

    clean = data.loc[valid].copy()

    clean["co2_removed_ppm"] = (clean["co2_in_ppm"] - clean["co2_out_ppm"]).round(2)
    clean["energy_intensity_kwh_per_kg"] = (
        clean["fan_power_kw"] / clean["capture_rate_kg_h"]
    ).round(2)
    clean["capture_efficiency_pct"] = (
        clean["co2_removed_ppm"] / clean["co2_in_ppm"] * 100
    ).round(2)
    clean["cycle_performance_pct"] = (
        clean["capture_efficiency_pct"] / (NOMINAL_CAPTURE_EFFICIENCY * 100) * 100
    ).round(2)
    clean["capacity_utilisation_pct"] = (
        clean["capture_rate_kg_h"] / NOMINAL_CAPACITY_KG_H * 100
    ).round(2)
    clean["quality_status"] = "VALID"
    stats["valid_records_loaded"] = len(clean)
    return clean, stats


def load_to_sqlite(clean: pd.DataFrame) -> None:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE) as connection:
        clean.to_sql("plant_readings", connection, if_exists="replace", index=False)


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
        "Average capture efficiency": f"{clean['capture_efficiency_pct'].mean():.1f}%",
        "Average cycle performance": f"{clean['cycle_performance_pct'].mean():.1f}% of nominal",
        "Average capacity utilisation": f"{clean['capacity_utilisation_pct'].mean():.1f}% of nominal",
    }
    lines = ["# SCADA ETL Run Summary", "", "## Data-quality results", ""]
    lines += [f"- **{name.replace('_', ' ').title()}:** {value}" for name, value in stats.items()]
    lines += ["", "## Plant KPIs", ""]
    lines += [f"- **{name}:** {value}" for name, value in metrics.items()]
    lines += [
        "", "## What this proves", "",
        "This learning demo simulates the basic flow from plant readings to trusted data for analysis.",
        "The values and validation ranges are synthetic; they are not DACMA plant data or DACMA system settings.",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not RAW_FILE.exists():
        raise FileNotFoundError("Run `python generate_scada_data.py` first.")
    raw = pd.read_csv(RAW_FILE)
    clean, stats = validate_and_transform(raw)
    load_to_sqlite(clean)
    create_dashboard(clean)
    write_report(clean, stats)
    print("ETL completed successfully")
    print(f"Database: {DATABASE}")
    print(f"Dashboard: {DASHBOARD}")
    print(f"Summary: {REPORT}")


if __name__ == "__main__":
    main()
