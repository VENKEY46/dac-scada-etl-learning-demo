# Data-quality rules

The pipeline treats the CSV as an untrusted historian export and records how many rows are removed at each stage.

1. Parse `timestamp_utc` as timezone-aware UTC.
2. Remove duplicate records for the same timestamp and plant, keeping the latest occurrence.
3. Remove records missing any required measurement.
4. Apply plausible ranges to temperature, pressure, airflow, inlet/outlet CO₂, fan power and capture rate.
5. Apply the process logic check that outlet CO₂ must be lower than inlet CO₂.
6. Calculate derived fields only after validation.

The ranges are deliberately labelled as simulated plausibility checks. They are not operating envelopes for a real DAC facility.
