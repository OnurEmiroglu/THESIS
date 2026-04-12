# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

High-frequency market-making (HFMM) thesis. A PPO-based reinforcement learning agent learns to set bid/ask quotes in a simulated limit order book with Poisson-arrival fills. The agent observes regime state (low/medium/high volatility) detected from rolling realized volatility and adapts its quoting strategy. Baselines include naive fixed-spread and Avellaneda-Stoikov (AS) analytical strategies. Out-of-sample (OOS) evaluation compares all four strategies (naive, AS, PPO-aware, PPO-blind) across multiple seeds, with ablation studies on inventory penalty (eta), skew penalty, and regime detector robustness.

## Work Package Status

| WP | Description | Status |
|---|---|---|
| WP0 | Project skeleton, run/logging system | Done |
| WP1 | Naive sweep + Avellaneda-Stoikov baselines | Done |
| WP2 | Synthetic regime generation (L/M/H), rolling RV detection, 3 detectors | Done |
| WP3 | Gym environment + sanity check (ablation ready) | Done |
| WP4 | RL training (PPO aware + blind) | Done |
| WP5 | OOS evaluation, ablations (eta, skew, detector, 5-variant, oracle, eta-regime), thesis writing | Done |

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

# Standalone scripts
python -m src.wp2.compare_detectors   # Compare 3 detectors on same synthetic data (no run.py)

# Lint
ruff check src/
```

## Architecture

### Run lifecycle

`run.py` loads a JSON config, reads `cfg["job"]` to select the strategy module, calls `setup_run()` to create a unique run directory under `results/runs/<run_id>/`, then invokes the job's `job_entry(cfg, ctx)`. `finalize_run()` writes status on completion. Each run captures logs, a config snapshot, git metadata, metrics CSV, and plots.

### Key modules

| File | Role |
|---|---|
| `src/run_context.py` | `RunContext`, `setup_run()`, `finalize_run()`, `CSVMetricLogger`, seeding |
| `src/wp1/sim.py` | `MMSimulator` -- core tick-by-tick simulation engine |
| `src/w1_naive_sweep.py` | Sweep over fixed half-spreads; produces `metrics_sweep.csv` |
| `src/w1_as_baseline.py` | Single AS episode; `as_deltas_ticks()` computes reservation price + half-spread; `compute_metrics()` utility |
| `src/w1_compare.py` | Runs naive + AS with same seed for fair comparison |
| `src/wp2/synth_regime.py` | 3-regime synthetic mid-price generation + 3 detectors (see below) |
| `src/wp2/job_w2_synth.py` | WP2 job entry; plots confusion matrix, transition matrix, regime comparison |
| `src/wp2/compare_detectors.py` | Standalone script comparing rv_baseline/rv_dwell/hmm accuracy on same data |
| `src/wp3/env.py` | `MMEnv` -- Gymnasium environment wrapping MMSimulator |
| `src/w3_sanity.py` | WP3 sanity check: naive, AS, random policies through MMEnv; regime ablation |
| `src/wp4/job_w4_ppo.py` | PPO training (aware + blind); deterministic eval; comparison plots |
| `src/wp5/job_w5_eval.py` | WP5 main OOS evaluation: 4 strategies x N seeds; per-regime metrics; equity curves |
| `src/wp5/job_w5_ablation_eta.py` | Eta ablation sweep (PPO-aware, OOS test across eta values) |
| `src/wp5/job_w5_ablation_skew.py` | Skew penalty ablation (PPO-aware, OOS test with action histograms) |
| `src/wp5/job_w5_detector_compare.py` | Detector robustness: train+eval PPO with each of 3 detectors |
| `src/wp5/analyze_actions.py` | Post-hoc action analysis: h/m distributions by regime, P(h=5) plots |

### Simulation model (`src/wp1/sim.py`)

- Order fill intensity: `lambda(delta) = A * exp(-k * delta)` (Poisson arrivals)
- Fill probability per step: `P = 1 - exp(-lambda * dt)`
- Mid-price follows arithmetic Brownian motion; quote latency modelled by stale mid
- `MarketParams`, `ExecParams` are frozen dataclasses; `MMState` holds mutable trading state

### Avellaneda-Stoikov (`src/w1_as_baseline.py`)

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
- **Non-negotiable:** no look-ahead -- regime label uses only past data

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

## Thesis manuscript

Source: scripts/gen_thesis_docx.py (python-docx). Current version: thesis_18.docx / thesis_18.pdf in manuscript/. Decisions log: decisions_log_5.docx in manuscript/.
