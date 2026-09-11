# Synthetic DAC Plant Data Pipeline

A reproducible Python data pipeline for analysing synthetic Direct Air Capture plant readings. The project demonstrates a practical time-series workflow: generate historian-style data, validate sensor records, calculate operational KPIs, store trusted data in SQLite, and produce a monitoring report and dashboard.

> This is an independent learning project. It uses synthetic data and does not contain proprietary plant data, internal software, or company-specific operating limits.

## Project workflow

```text
Synthetic historian data → quality checks → engineered KPIs → SQLite → dashboard/report
```

## Key questions answered

- How much CO₂ is removed between the inlet and outlet streams?
- Is the capture rate stable over time?
- What is the estimated adsorption/absorption performance of the simulated cycle?
- How much capture capacity is available relative to the defined nominal capacity?
- How much fan energy is used per kilogram of captured CO₂?
- Which records should be trusted for downstream analysis?

## Repository structure

```text
.
├── data/raw/                  # Synthetic input historian export
├── data/processed/            # Generated SQLite database (ignored by Git)
├── docs/                      # KPI definitions and data-quality rules
├── output/                    # Reproducible dashboard and run summary
├── tests/                     # Validation and pipeline tests
├── generate_scada_data.py     # Creates the reproducible input data
├── run_etl.py                 # Validates, transforms, loads and reports
├── requirements.txt
└── README.md
```

## Run locally

From the repository root:

```bash
python -m pip install -r requirements.txt
python generate_scada_data.py
python run_etl.py
```

Generated artefacts:

- `output/dac_plant_dashboard.png` — time-series monitoring view
- `output/etl_run_summary.md` — data-quality results and KPI summary
- `data/processed/dac_scada.db` — SQLite table named `plant_readings`

## KPI model

The pipeline calculates CO₂ removal, capture rate, energy intensity, adsorption/absorption performance and capacity utilisation. The performance and capacity measures are analytical indicators for this simulated dataset; they are not validated process-engineering specifications. Definitions and assumptions are documented in [`docs/kpis.md`](docs/kpis.md).

## Data-quality approach

The transformation stage parses timestamps, removes duplicate historian records, removes incomplete records, checks physical plausibility ranges, and applies the relationship `CO₂ outlet < CO₂ inlet`. Full rules are documented in [`docs/data-quality.md`](docs/data-quality.md).

## Scope and limitations

This repository is intentionally small and transparent. A production implementation would additionally require authenticated plant connectors, access control, secure secrets management, schema versioning, monitoring, retries, audit logging, alerting, approved engineering thresholds and deployment controls.

## Reproducibility

The data generator uses a fixed random seed. Running the generator and ETL script recreates the same analytical scenario and output structure.
