# WP6 Signal Informativeness Sweep — Full Summary

Run ID: `20260426-105115_seed42_wp6-sweep-full_ce849a0`

- trained = 480
- skipped = 0

## Cell timing distribution (train_seconds)

- min: 964.4
- median: 980.8
- max: 1277.8
- p95: 1098.1

## Per-cell mean across seeds

| condition | variant | sharpe_like_mean | inv_p99_mean |
|---|---|---:|---:|
| coarsened | combined | 0.6908 | 2.5 |
| coarsened | oracle_full | 0.7447 | 1.8 |
| coarsened | oracle_pure | 0.6632 | 2.0 |
| coarsened | regime_only | 0.6991 | 1.9 |
| coarsened | sigma_only | 0.7827 | 1.9 |
| full | combined | 0.6898 | 2.0 |
| full | oracle_full | 0.6811 | 1.6 |
| full | oracle_pure | 0.6632 | 2.0 |
| full | regime_only | 0.6991 | 1.9 |
| full | sigma_only | 0.7626 | 1.9 |
| lagged | combined | 0.6812 | 1.8 |
| lagged | oracle_full | 0.7264 | 2.0 |
| lagged | oracle_pure | 0.6632 | 2.0 |
| lagged | regime_only | 0.6991 | 1.9 |
| lagged | sigma_only | 0.7822 | 1.9 |
| noisy | combined | 0.7125 | 1.9 |
| noisy | oracle_full | 0.6736 | 1.9 |
| noisy | oracle_pure | 0.6632 | 2.0 |
| noisy | regime_only | 0.6991 | 1.9 |
| noisy | sigma_only | 0.7563 | 1.9 |
| none | combined | 0.6991 | 1.9 |
| none | oracle_full | 0.6632 | 2.0 |
| none | oracle_pure | 0.6632 | 2.0 |
| none | regime_only | 0.6991 | 1.9 |

## Reminder

FULL SWEEP — thesis Chapter 5 input. 20 seeds × 24 cells × 1M timesteps.
If interrupted, resume with --resume <run_id>.

## Next step

Review full_summary.md, then proceed with Chapter 5 analysis (per-condition × per-variant Sharpe distribution, paired-seed comparison, sensitivity check at α=0.20 / k=10).