# WP5.5 Signal Calibration Audit — CSV Snapshot

Source run_id: `20260425-184732_seed42_wp55-calibration_1e806ff`

Regenerate: `python run.py --config config/w55_calibration.json`

## Files

- `metrics_calibration_per_seed.csv` — 70 rows: 5 seeds × 14 conditions (7 alpha values + 7 k values).
- `metrics_calibration_aggregated.csv` — 14 rows: mean + std of each metric across the 5 seeds, grouped by (parameter, value).

Selection rationale (α = 0.40, k = 20) is recorded in **Decision #46** of `manuscript/decisions_log_10.docx`. Source run dir lives on disk only — `results/runs/*` is gitignored per repo convention.
