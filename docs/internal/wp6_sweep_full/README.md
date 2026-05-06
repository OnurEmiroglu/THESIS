# WP6 Full Sweep — Results Snapshot

Source run_id: `20260426-105115_seed42_wp6-sweep-full_ce849a0`
Started: 2026-04-26 13:51:15 UTC
Finished: 2026-05-01 23:10:06 UTC
Wall time: 5 days 12h 19m
Status: success (480/480 cells, 0 orphans)

## Files
- `metrics_sweep_full.csv` — 480 rows: per-cell sharpe_like,
  final_equity, fill_rate, inv_p99, train_seconds, eval_seconds
- `full_summary.md` — per-cell mean Sharpe across 20 seeds
- `status.json` — final run status
- `config_snapshot.json` — config used to launch the sweep
- `meta.json` — run metadata (git commit, python version, etc.)

## How to regenerate
`python run.py --config config/w6_sweep_full.json`
(commit ce849a0 or later)

## Pointer
Decision log entry: see decisions_log_11 (to be added with Decision #47).
The sweep ran cleanly across an unscheduled Windows restart that
occurred AFTER successful completion (status.json was already written).
