# EcoPulse Sample Datasets

This folder contains synthetic demo data for all three EcoPulse tracks.

## Files

- `air_observations.csv` — 10 AQI observations covering multiple risk categories.
- `water_readings.csv` — 15 cumulative meter readings across three locations, including a deliberate usage spike.
- `waste_entries.csv` — 15 waste entries with compatible mass units (`kg` and `g`).
- `seed_data.json` — all records combined with metadata.

## Important

These records are **synthetic**. They are suitable for local testing and demos, not for environmental claims or model training.

Before importing, compare fields and enum values with the current Pydantic schemas and service logic in your backend. The CSVs are generic starter data and may need field-name adjustments to match the repository exactly.

## Suggested test cases

- Air: confirm AQI category handling for low and high values.
- Water: calculate consumption between consecutive readings for the same location; `LOC-001` includes a sharp increase between October 3 and October 4.
- Waste: aggregate `g` and `kg` only after valid normalization; never treat unknown units as kilograms.
