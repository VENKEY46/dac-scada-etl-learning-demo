# Architecture

The repository has two learning paths.

## Batch path

`generate_scada_data.py` creates a reproducible CSV. `run_etl.py` separates trusted and rejected records, stores trusted records in SQLite, and creates a report and dashboard.

## Live path

`simulate_plant_stream.py` publishes one synthetic reading at a time to a local MQTT broker. `ingest_stream.py` validates each message with the shared rules in `validation.py`. Trusted readings go to InfluxDB and rejected readings go to a CSV audit log. Grafana reads InfluxDB through a provisioned data source and dashboard.

The container services bind to localhost. The configuration is suitable only for a local learning demo.

