# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

High-frequency market-making (HFMM) thesis. Simulates and compares market-making strategies (naive fixed-spread, Avellaneda-Stoikov) using a custom Poisson-arrival order fill model, with regime-aware Gym environment for RL training.

## Work Package Status

| WP | Description | Status |
|---|---|---|
| WP0 | Project skeleton, run/logging system | ✅ Done |
| WP1 | Naive sweep + Avellaneda-Stoikov baselines | ✅ Done |
| WP2 | Synthetic regime generation (L/M/H), rolling RV detection | ✅ Done |
| WP3 | Gym environment + sanity check (ablation ready) | ✅ Done |
| WP4 | RL training (PPO) | ✅ Done |
| WP5 | Evaluation + thesis writing | 🔲 Next |

## Commands

```bash
# Setup
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt

# Run experiments (entry point dispatches on config["job"])
python run.py --config config/w1_naive_sweep.json   # WP1 naive spread sweep
python run.py --config config/w1_as_baseline.json   # WP1 Avellaneda-Stoikov
python run.py --config config/w1_compare.json       # WP1 naive vs AS comparison
python run.py --config config/w2_synth.json         # WP2 synthetic regime detection
python run.py --config config/w3_sanity.json        # WP3 sanity check (regime-aware)
python run.py --config config/w3_sanity_blind.json  # WP3 sanity check (regime-blind)
python run.py --config config/w4_ppo.json           # WP4 PPO training

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
| `src/wp1/sim.py` | `MMSimulator` — core tick-by-tick simulation engine |
| `src/w1_naive_sweep.py` | Sweep over fixed half-spreads; produces `metrics_sweep.csv` |
| `src/w1_as_baseline.py` | Single AS episode; `as_deltas_ticks()` computes reservation price + half-spread |
| `src/w1_compare.py` | Runs both strategies with the same seed for fair comparison |
| `src/wp2/synth_regime.py` | Generates 3-regime (L/M/H) synthetic mid-price series + rolling RV detection |
| `src/wp2/job_w2_synth.py` | WP2 job entry; plots confusion matrix, transition matrix, regime comparison |
| `src/wp3/env.py` | `MMEnv` — Gymnasium environment wrapping MMSimulator |
| `src/w3_sanity.py` | WP3 sanity check: naive, AS, random policies through MMEnv; regime ablation |

### Simulation model (`src/wp1/sim.py`)

- Order fill intensity: `λ(δ) = A·exp(-k·δ)` (Poisson arrivals)
- Fill probability per step: `P = 1 - exp(-λ·dt)`
- Mid-price follows arithmetic Brownian motion; quote latency is modelled by using a stale mid
- `MarketParams`, `ExecParams` are frozen dataclasses; `MMState` holds mutable trading state

### Avellaneda-Stoikov (`src/w1_as_baseline.py`)

- Reservation price: `r = mid - q·γ·σ²·τ`
- Half-spread: `d = ½·γ·σ²·τ + (1/γ)·ln(1 + γ/k)`
- Deltas clipped to `[delta_min, delta_max]` from config

### Gym Environment (`src/wp3/env.py`)

- **Observation space:** `[q_norm, sigma_hat, tau, regime_L, regime_M, regime_H]` (shape=6, float32)
  - `q_norm = clip(inv, -inv_max_clip, inv_max_clip) / inv_max_clip`
  - `sigma_hat`: rolling realized volatility from exogenous series (0.0 if unavailable)
  - `tau = (n_steps - t) / n_steps`
  - regime one-hot: zeros if `use_regime=False` or `regime_hat=="warmup"`
- **Action space:** `MultiDiscrete([5, 5])`
  - `h_idx ∈ {0..4}` → `h = h_idx + 1` (half-spread ticks: 1..5)
  - `m_idx ∈ {0..4}` → `m = m_idx - 2` (skew: -2..2)
  - `delta_bid = max(1, h + m)`, `delta_ask = max(1, h - m)`
- **Reward:** `R_t = (W_{t+1} - W_t) - η · inv_{t+1}²`
  - Fee already deducted in sim cash update — do NOT subtract again (double-count)
- **Exogenous series:** inject via `reset(options={"exog": df})` with columns `mid, sigma_hat, regime_hat`

### Regime detection (`src/wp2/synth_regime.py`)

- 3-state Markov chain (L/M/H) with sticky transition matrix
- Rolling realized volatility (RV) with window=50 steps
- Thresholds calibrated on warmup period (percentile 33/66)
- Detection accuracy ~60.7% (post-warmup)
- **Non-negotiable:** no look-ahead — regime label uses only past data

### Config schema

All configs share `seed`, `market` (`mid0`, `tick_size`, `dt`, `sigma_mid_ticks`), `exec` (`A`, `k`, `fee_bps`, `latency_steps`), `episode.n_steps`. Additional keys by job:

| Job | Extra keys |
|---|---|
| `w1_naive_sweep` | `sweep.half_spreads_ticks` |
| `w1_as_baseline`, `w1_compare` | `as` block (`gamma`, `horizon_steps`, `min/max_delta_ticks`) |
| `w2_synth` | `regime` block (`rv_window`, `warmup_steps`, `sigma_mid_ticks_base`, `sigma_mult`, `trans_matrix`) |
| `w3_sanity` | `episode.inv_max_clip`, `wp3` (`eta`, `use_regime`), `as` block, `sweep`, `regime` block |

### Run ID format

`YYYYMMDD-HHMMSS_seed<S>_<TAG>_<COMMIT>` — reproducibility is enforced by snapshotting config and fixing `PYTHONHASHSEED` + numpy/random seeds.

## Thesis manuscript

Source: `manuscript/thesis.md`. Build to DOCX via VS Code task "Build thesis (DOCX)" (requires pandoc).
