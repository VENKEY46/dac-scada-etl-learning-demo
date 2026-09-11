# KPI definitions

The following indicators are calculated from the synthetic historian fields. They are designed to demonstrate transparent analytical reasoning, not to represent a certified process model.

| KPI | Calculation | Interpretation |
|---|---|---|
| CO₂ removed | `co2_in_ppm - co2_out_ppm` | Concentration reduction across the simulated capture stage. |
| Capture rate | Input field in `kg CO₂/h` | Estimated mass flow captured per hour in the synthetic scenario. |
| Capture efficiency | `CO₂ removed / CO₂ inlet × 100` | Relative inlet-to-outlet removal performance. |
| Energy intensity | `fan_power_kw / capture_rate_kg_h` | Estimated fan energy per kilogram captured. Lower is better, subject to process context. |
| Cycle performance | `capture_efficiency / nominal_efficiency × 100` | Relative adsorption/absorption performance against a documented nominal reference of 42%. |
| Capacity utilisation | `capture_rate / nominal_capacity × 100` | Use of a documented nominal capacity of 10 kg CO₂/h. |

The nominal efficiency and capacity are transparent simulation assumptions. They must be replaced by validated engineering values before use in a real plant.
