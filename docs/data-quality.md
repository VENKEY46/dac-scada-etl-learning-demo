# Data Quality

The project rejects rows for four main reasons:

1. **Duplicate key** - an older row has the same timestamp and plant ID.
2. **Missing or invalid value** - a required field is empty or not numeric.
3. **Range failure** - a sensor value is outside the limits chosen for this synthetic demo.
4. **Process-logic failure** - outlet CO2 is not lower than inlet CO2.

Rejected rows are retained with a plain-English reason so a user can trace what happened. The validation limits are learning assumptions, not real DAC plant settings.

