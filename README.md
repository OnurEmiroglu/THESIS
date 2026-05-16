# HFMM Thesis
**High-Frequency Market Making with Reinforcement Learning Under Different Volatility Regimes**
KIT Financial Engineering MSc Thesis

## Research Question
Does a regime-aware PPO market-making agent outperform a regime-blind PPO agent?
Final finding: signal redundancy. In the tested synthetic HFMM setting, PPO learns strong risk-adjusted quoting, but explicit regime labels do not robustly improve performance beyond the continuous `sigma_hat` signal already available to the policy. TOST equivalence is confirmed (±0.10 bound, p=0.00067, 90% CI [−0.001, +0.063], 95% CI [−0.008, +0.069]). The result holds across detector robustness checks (ANOVA p=0.997), reward shaping (p=0.0016 favoring sigma_only), and model misspecification (TOST ±0.05, p=0.042, 90% CI [−0.040, +0.048]).

These are controlled synthetic-market claims, not live-market deployment claims.
Post-hoc signal redundancy diagnostics are retained as supporting interpretive diagnostics only: they help explain why the frozen WP5/WP6 evidence is consistent with signal redundancy, but they are not mechanistic proof and they do not replace the primary experiment evidence.

Current manuscript: `manuscript/thesis_29.pdf`; decision log: `manuscript/decisions_log_13.pdf`.

Current orientation files:
- `docs/internal/project_full_notes_13may.md` — consolidated project brain for final thesis context.
- `EVIDENCE_MANIFEST.md` — canonical audit-remediation evidence manifest.
- `docs/internal/doc_consistency_audit.md` — documentation freshness audit.

## Structure
- `src/` — all Python source code
  - `wp1/` — simulation engine (sim.py)
  - `wp2/` — synthetic regime generation and detection (synth_regime.py, job_w2_synth.py, compare_detectors.py)
  - `wp3/` — Gymnasium environment (env.py)
  - `wp4/` — PPO training (job_w4_ppo.py)
  - `wp5/` — OOS evaluation, ablations, detector comparison
  - `wp5_5/` — signal degradation audit/calibration/runtime checks
  - `wp6/` — signal informativeness sweep
- `config/` — JSON config files for all experiments
- `results/runs/` — experiment outputs (git ignored)
- `data/processed/` — intermediate data (git ignored)
- `manuscript/` — thesis text

## Strategies
- **Naive**: fixed symmetric half-spread (h=2 ticks)
- **Avellaneda-Stoikov**: inventory-aware analytical baseline
- **PPO-aware / PPO-blind**: original 4-strategy comparison with/without estimated regime label
- **5-variant PPO ablation**: `ppo_sigma_only`, `ppo_regime_only`, `ppo_combined`, `ppo_oracle_pure`, `ppo_oracle_full`

## Regime Detection
Three detector variants implemented and compared:
- `rv_baseline`: rolling realized volatility, 60.7% accuracy
- `rv_dwell`: RV + dwell filter, 60.4% accuracy
- `hmm`: GaussianHMM on sigma_hat, 81.8% accuracy

Main WP4/WP5/WP6 pipelines use causal rv_baseline. rv_dwell is retained only as an auxiliary/offline robustness comparison. HMM is used as an additional robustness detector.

## Running Experiments
```bash
# Activate environment
C:\venvs\thesis-env\.venv\Scripts\activate

# Run any experiment
python run.py --config config/<config_file>.json

# Compare detectors standalone
python -m src.wp2.compare_detectors
```

## Key Results
- Original 4-strategy OOS run: PPO-aware/blind Sharpe 0.715/0.740 vs AS 0.105 and naive 0.127. AS wins on raw equity (~5.05 vs PPO ~4.10-4.42) by taking much larger inventory risk (inv_p99 ~30 lots vs PPO ~2 lots).
- Regime-aware vs regime-blind: Sharpe difference is not significant (paired t-test p=0.261, 20 seeds); final equity favors PPO-blind (paired t-test p=0.023).
- 5-variant ablation: `ppo_sigma_only` has the highest Sharpe (0.753); `ppo_oracle_full` does not significantly beat it (Sharpe p=0.115).
- TOST equivalence test (±0.10): sigma_only and oracle_full are practically equivalent in normal environment (p=0.00067, 90% CI [−0.001, +0.063], 95% CI [−0.008, +0.069]). TOST α=0.05 corresponds to the 90% CI.
- TOST under model misspecification (±0.05): practically equivalent (p=0.042, 90% CI [−0.040, +0.048], 95% CI [−0.049, +0.057], Cohen's d=0.034).
- Regime-conditional eta run: `ppo_sigma_only` beats `ppo_combined` on Sharpe (p=0.0016), so etaH=5×etaL did not make explicit regime labels useful.
- Mild model-misspecification run: `ppo_sigma_only` and `ppo_oracle_full` remain statistically indistinguishable on Sharpe (p=0.881).
- Detector robustness full run (3 detectors × 20 seeds × 120 models): COMPLETE. rv_baseline p=0.114, rv_dwell p=0.110, HMM p=0.082. Null result confirmed across all detectors.
- WP6 signal informativeness sweep: COMPLETE. The original informativeness-threshold hypothesis was not supported; adding categorical regime labels did not reveal a robust improvement over `sigma_hat` in the tested calibration band.

## Audit Status

Lane A/B/C audit-remediation is complete through commit `045ee86`. No experiment reruns were performed during remediation, no numerical claim drift was introduced, and the protected evidence artifacts remained 4/4 SHA256 MATCH. `EVIDENCE_MANIFEST.md` is the canonical audit manifest.

Primary evidence remains the canonical WP5/WP6 experiment outputs and protected summaries. Post-hoc diagnostics, including `docs/internal/posthoc_signal_analysis/`, are supporting interpretive diagnostics only. Protected evidence remains hash-verified.

## Reproducibility
Every run produces a timestamped directory under results/runs/ containing:
config_snapshot.json, meta.json, run.log, metrics.csv, plots/
