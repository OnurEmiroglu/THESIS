# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

High-frequency market-making (HFMM) thesis. A PPO-based reinforcement learning agent learns to set bid/ask quotes in a simulated limit order book with Poisson-arrival fills. The agent observes regime state (low/medium/high volatility) detected from rolling realized volatility and adapts its quoting strategy. Baselines include naive fixed-spread and Avellaneda-Stoikov (AS) analytical strategies. Out-of-sample (OOS) evaluation compares all four strategies (naive, AS, PPO-aware, PPO-blind) across multiple seeds, with ablation studies on inventory penalty (eta), skew penalty, and regime detector robustness.

## Current Final Finding

Final finding: signal redundancy. In the tested synthetic HFMM setting, explicit categorical regime labels do not improve PPO beyond the continuous `sigma_hat` volatility signal already available to the policy. The thesis does not make a live-trading deployment claim; all scientific claims are about the controlled synthetic market environment.

Interpretation must remain bounded: no mechanism proof, no claim that categorical interference is conclusively proven, and no live deployment implication. Post-hoc signal diagnostics can support interpretation, but primary evidence remains the canonical WP5/WP6 experiments.

## Work Package Status

| WP | Description | Status |
|---|---|---|
| WP0 | Project skeleton, run/logging system | Done |
| WP1 | Naive sweep + Avellaneda-Stoikov baselines | Done |
| WP2 | Synthetic regime generation (L/M/H), rolling RV detection, 3 detectors | Done |
| WP3 | Gym environment + sanity check | Done |
| WP4 | RL training infrastructure and pilot/in-sample evaluation | Done |
| WP5 | OOS evaluation, ablations (eta, skew, detector, 5-variant, oracle, eta-regime), thesis writing | Done |
| WP5.5 | Signal degradation audit/calibration | Done |
| WP6 | Signal informativeness sweep | Done |

`docs/internal/posthoc_signal_analysis/` is a read-only/frozen-output diagnostic package. Treat it as supporting interpretive diagnostics only, not primary experiment evidence unless explicitly frozen later.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt

# Run experiments (entry point dispatches on config["job"])
python run.py --config config/w1_naive_sweep.json       # WP1 naive spread sweep
python run.py --config config/w1_as_baseline.json       # WP1 Avellaneda-Stoikov
python run.py --config config/w1_compare.json           # WP1 naive vs AS comparison
python run.py --config config/w2_synth.json             # WP2 synthetic regime detection
python run.py --config config/w3_sanity.json            # WP3 sanity check (regime-aware)
python run.py --config config/w3_sanity_both.json       # WP3 sanity check (runs both aware + blind)
python run.py --config config/w4_ppo.json               # WP4 PPO training (aware + blind)
python run.py --config config/w5_main.json              # WP5 main OOS eval (20 seeds, 1M ts)
python run.py --config config/w5_eval.json              # WP5 OOS eval (3 seeds, 200k ts)
python run.py --config config/w5_ablation_eta.json      # WP5 eta ablation (3 etas x 3 seeds)
python run.py --config config/w5_ablation_skew.json     # WP5 skew penalty ablation (20 seeds)
python run.py --config config/w5_detector_pilot.json    # WP5 detector comparison (3 seeds)
python run.py --config config/w5_detector_full.json     # WP5 detector comparison (20 seeds)
python run.py --config config/w5_eta_regime.json      # WP5 regime-conditional eta (20 seeds, 1M ts)
python run.py --config config/w5_misspec_mild.json  # WP5 model misspecification mild (20 seeds, 1M ts)
python run.py --config config/w55_audit.json           # WP5.5 signal degradation audit (offline; no PPO training)
python run.py --config config/w55_runtime.json         # WP5.5 runtime profiling
python run.py --config config/w55_calibration.json     # WP5.5 degradation calibration
python run.py --config config/w6_sweep_pilot.json      # WP6 pilot signal-informativeness sweep
python run.py --config config/w6_sweep_full.json       # WP6 full signal-informativeness sweep
python run.py --config config/w6_sweep_full.json --resume <run_id>  # Resume long WP6 runs

# Standalone scripts
python -m src.wp2.compare_detectors   # Compare 3 detectors on same synthetic data (no run.py)

# Lint
ruff check src/
```

Warning: do not regenerate thesis figures, WP6 plots/summaries, protected CSVs, or canonical run outputs before defense unless a new approved version is being created. Do not rerun PPO/WP5/WP6 for documentation-only work.

## Architecture

### Run lifecycle

`run.py` loads a JSON config, reads `cfg["job"]` to select the strategy module, calls `setup_run()` to create a unique run directory under `results/runs/<run_id>/`, then invokes the selected job. `finalize_run()` writes status on completion. Each run captures logs, a config snapshot, git metadata, metrics CSV, and plots. Long WP6 runs can be resumed with `--resume <run_id>`; resume mode validates the current config against the saved `config_snapshot.json` before appending work.

### Key modules

| File | Role |
|---|---|
| `src/run_context.py` | `RunContext`, `setup_run()`, `finalize_run()`, `CSVMetricLogger`, seeding |
| `src/wp1/sim.py` | `MMSimulator` -- core tick-by-tick simulation engine |
| `src/wp1/w1_naive_sweep.py` | Sweep over fixed half-spreads; produces `metrics_sweep.csv` |
| `src/wp1/w1_as_baseline.py` | Single AS episode; `as_deltas_ticks()` computes reservation price + half-spread; `compute_metrics()` utility |
| `src/wp1/w1_compare.py` | Runs naive + AS with same seed for fair comparison |
| `src/wp2/synth_regime.py` | 3-regime synthetic mid-price generation + 3 detectors (see below) |
| `src/wp2/job_w2_synth.py` | WP2 job entry; plots confusion matrix, transition matrix, regime comparison |
| `src/wp2/compare_detectors.py` | Standalone script comparing rv_baseline/rv_dwell/hmm accuracy on same data |
| `src/wp3/env.py` | `MMEnv` -- Gymnasium environment wrapping MMSimulator |
| `src/wp3/w3_sanity.py` | WP3 sanity check: naive, AS, random policies through MMEnv; regime ablation |
| `src/wp4/job_w4_ppo.py` | PPO training (aware + blind); deterministic eval; comparison plots |
| `src/wp5/job_w5_eval.py` | WP5 main OOS evaluation: 4 strategies x N seeds; per-regime metrics; equity curves |
| `src/wp5/job_w5_ablation_eta.py` | Eta ablation sweep (PPO-aware, OOS test across eta values) |
| `src/wp5/job_w5_ablation_skew.py` | Skew penalty ablation (PPO-aware, OOS test with action histograms) |
| `src/wp5/job_w5_detector_compare.py` | Detector robustness: train+eval PPO with each of 3 detectors |
| `src/wp5/analyze_actions.py` | Post-hoc action analysis: h/m distributions by regime, P(h=5) plots |
| `src/wp5_5/job_w55_audit.py` | Offline signal degradation audit; no PPO training |
| `src/wp5_5/job_w55_runtime.py` | Runtime profiling for candidate signal-degradation sweep sizes |
| `src/wp5_5/job_w55_calibration.py` | Calibration of noisy/lagged/coarsened signal settings |
| `src/wp5_5/signal_audit.py` | Signal audit metrics: correlation, classification accuracy, separability, overlap |
| `src/wp5_5/signal_degradation.py` | Shared signal degradation transforms used by WP5.5 and WP6 |
| `src/wp6/job_w6_sweep_pilot.py` | WP6 pilot signal-informativeness sweep |
| `src/wp6/job_w6_sweep_full.py` | WP6 full 20-seed signal-informativeness sweep |

### Simulation model (`src/wp1/sim.py`)

- Order fill intensity: `lambda(delta) = A * exp(-k * delta)` (Poisson arrivals)
- Fill probability per step: `P = 1 - exp(-lambda * dt)`
- Mid-price follows arithmetic Brownian motion; quote latency modelled by stale mid
- `MarketParams`, `ExecParams` are frozen dataclasses; `MMState` holds mutable trading state

### Avellaneda-Stoikov (`src/wp1/w1_as_baseline.py`)

- Reservation price: `r = mid - q * gamma * sigma^2 * tau`
- Half-spread: `d = 0.5 * gamma * sigma^2 * tau + (1/gamma) * ln(1 + gamma/k)`
- Deltas clipped to `[delta_min, delta_max]` from config

### Gym Environment (`src/wp3/env.py`)

- **Observation space:** `[q_norm, sigma_hat, tau, regime_L, regime_M, regime_H]` (shape=6, float32)
  - `q_norm = clip(inv, -inv_max_clip, inv_max_clip) / inv_max_clip`
  - `sigma_hat`: rolling realized volatility from exogenous series (0.0 if unavailable)
  - `tau = (n_steps - t) / n_steps`
  - regime one-hot: zeros if `use_regime=False`; during warmup, `regime_hat=="warmup"` is treated as `"M"` producing `[0,1,0]` (see known limitation below)
- **Action space:** `MultiDiscrete([5, 5])`
  - `h_idx in {0..4}` -> `h = h_idx + 1` (half-spread ticks: 1..5)
  - `m_idx in {0..4}` -> `m = m_idx - 2` (skew: -2..2)
  - `delta_bid = max(1, h + m)`, `delta_ask = max(1, h - m)`
- **Reward:** `R_t = (W_{t+1} - W_t) - eta * inv_{t+1}^2`
  - Fee already deducted in sim cash update -- do NOT subtract again (double-count)
- **Exogenous series:** inject via `reset(options={"exog": df})` with columns `mid, sigma_hat, regime_hat`
- **Warmup behavior (known limitation):** during warmup, exog sigma_hat is NaN so `sh=0.0`, but regime_hat defaults to `"M"` (not a valid L/M/H label but treated as M in `_get_obs`), producing one-hot `[0,1,0]` rather than a zero vector. This means warmup steps receive a non-zero regime signal even though no detection has occurred yet. Documented as a known limitation.

### Regime detection (`src/wp2/synth_regime.py`)

- 3-state Markov chain (L/M/H) with sticky transition matrix
- Rolling realized volatility (RV) with window=50 steps
- Thresholds calibrated on warmup period (percentile 33/66)
- The main reported WP4/WP5/WP6 pipelines use causal rv_baseline labels. rv_dwell applies offline dwell smoothing and is retained only for auxiliary detector-robustness comparison. It must not be described as the main causal detector.

Three detector variants:

| Detector | Function | Description |
|---|---|---|
| `rv_baseline` | `assign_regime_hat()` | Simple threshold on rolling RV |
| `rv_dwell` | `assign_regime_hat_dwell()` | Threshold + dwell filter (`apply_dwell_filter()`, min_dwell=5) |
| `hmm` | `assign_regime_hat_hmm()` | GaussianHMM fit on warmup, causal prediction; maps states by variance |

### Config files

| Config | Job | Description |
|---|---|---|
| `w1_naive_sweep.json` | `w1_naive_sweep` | Sweep over fixed half-spreads |
| `w1_as_baseline.json` | `w1_as_baseline` | Single AS episode |
| `w1_compare.json` | `w1_compare` | Naive vs AS comparison |
| `w2_synth.json` | `w2_synth` | Synthetic regime generation + detection |
| `w3_sanity.json` | `w3_sanity` | Sanity check (regime-aware) |
| `w3_sanity_both.json` | `w3_sanity` | Sanity check (runs both aware + blind via job_entry) |
| `w4_ppo.json` | `w4_ppo` | PPO training |
| `w5_main.json` | `w5_eval` | Main OOS eval (20 seeds, 1M timesteps) |
| `w5_eval.json` | `w5_eval` | OOS eval (3 seeds, 200k timesteps) |
| `w5_ablation_eta.json` | `w5_ablation_eta` | Eta ablation (eta in {1e-4, 1e-3, 1e-2}, 3 seeds) |
| `w5_ablation_skew.json` | `w5_ablation_skew` | Skew penalty ablation (c=1e-4, 20 seeds, 1M ts) |
| `w5_detector_pilot.json` | `w5_detector_compare` | Detector robustness pilot (3 seeds) |
| `w5_detector_full.json` | `w5_detector_compare` | Detector robustness full (20 seeds, 1M ts) |
| `w5_eta_regime.json` | `w5_eval` | Regime-conditional eta experiment |
| `w5_misspec_mild.json` | `w5_eval` | Mild model misspecification experiment |
| `w55_audit.json` | `w55_audit` | Offline signal degradation audit |
| `w55_runtime.json` | `w55_runtime` | WP5.5 runtime profiling |
| `w55_calibration.json` | `w55_calibration` | WP5.5 signal degradation calibration |
| `w6_sweep_pilot.json` | `w6_sweep_pilot` | WP6 pilot signal-informativeness sweep |
| `w6_sweep_full.json` | `w6_sweep_full` | WP6 full signal-informativeness sweep |

### Config schema

All configs share `seed`, `market` (`mid0`, `tick_size`, `dt`, `sigma_mid_ticks`), `exec` (`A`, `k`, `fee_bps`, `latency_steps`), `episode.n_steps`. Additional keys by job:

| Job | Extra keys |
|---|---|
| `w1_naive_sweep` | `sweep.half_spreads_ticks` |
| `w1_as_baseline`, `w1_compare` | `as` block (`gamma`, `horizon_steps`, `min/max_delta_ticks`) |
| `w2_synth` | `regime` block (`rv_window`, `warmup_steps`, `sigma_mid_ticks_base`, `sigma_mult`, `trans_matrix`) |
| `w3_sanity` | `episode.inv_max_clip`, `wp3` (`eta`, `use_regime`), `as` block, `sweep`, `regime` block |
| `w4_ppo` | `wp3`, `wp4` (PPO hyperparams), `as`, `regime` blocks |
| `w5_eval` | `wp3`, `wp4`, `wp5` (`seeds`, `train_frac`, `naive`), `as`, `regime` blocks |
| `w5_ablation_eta` | Same as `w5_eval` + `wp5.eta_values` |
| `w5_ablation_skew` | Same as `w5_eval` + `wp3.skew_penalty_c`, `wp5.skew_c_values` |
| `w5_detector_compare` | Same as `w5_eval` (trains with each detector internally) |
| `w55_audit`, `w55_runtime`, `w55_calibration` | WP5.5 audit/calibration blocks |
| `w6_sweep_pilot`, `w6_sweep_full` | `sweep` block with conditions, variants, seeds, degradation parameters |

### Run ID format

`YYYYMMDD-HHMMSS_seed<S>_<TAG>_<COMMIT>` -- reproducibility is enforced by snapshotting config and fixing `PYTHONHASHSEED` + numpy/random seeds.

## Key design decisions

- **Fill model:** `lambda(delta) = A * exp(-k * delta)`, Poisson arrivals per Avellaneda-Stoikov
- **Reward shaping:** `R_t = delta_equity - eta * inv^2` (eta controls inventory aversion)
- **Observation:** 6-dim `[q_norm, sigma_hat, tau, regime_L, regime_M, regime_H]`
- **Action:** `MultiDiscrete([5, 5])` -> half-spread h in 1..5, skew m in -2..2
- **Three detectors** for robustness analysis: `rv_baseline`, `rv_dwell` (dwell filter), `hmm` (GaussianHMM)
- **Train/test split:** 70/30 on exogenous series (no data leakage between train and OOS)
- **PPO hyperparams:** lr=3e-4, n_steps=2048, batch=256, epochs=10, gamma=0.999, clip=0.2
- **Model misspecification:** `A` and `k` are regime-dependent in misspec experiments; `ExecParams` unfrozen; override applied per-step in `env.py` based on `regime_true`
- **WP6 interpretation:** full sweep is complete. The original informativeness-threshold hypothesis was not supported; `combined` is directionally below `sigma_only` in informative conditions. Categorical-channel degradation/interference is a descriptive interpretation, not a proven mechanism.
- **Real-data extension:** future/paper work only; it is not part of `thesis_29`.

## Reproducibility Guardrails

- `CSVMetricLogger` enforces stable schema behavior and raises on column drift.
- Resume mode validates the current config against the saved config snapshot before continuing a run.
- `.gitattributes` defines line-ending policy for CSV/TXT audit stability.
- Protected evidence artifacts remained 4/4 SHA256 MATCH through the audit-remediation sequence.

## Thesis manuscript and current docs

Current thesis: `manuscript/thesis_29.pdf`.
Current decision log: `manuscript/decisions_log_13.pdf`.
Project brain: `docs/internal/project_full_notes_13may.md`.
Audit manifest: `EVIDENCE_MANIFEST.md`.
Historical generators are under `scripts/legacy/` and are provenance/history only, not active pipeline execution.
