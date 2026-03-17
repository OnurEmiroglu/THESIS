# HFMM Thesis
**High-Frequency Market Making with Reinforcement Learning Under Different Volatility Regimes**
KIT Financial Engineering MSc Thesis

## Research Question
Does a regime-aware PPO market-making agent outperform a regime-blind PPO agent?
Current finding: null result — difference is statistically inconclusive (rv_baseline, 20 seeds). Pilot (3 seeds) shows null result across all three detector variants; full experiment (3 detectors x 20 seeds) in progress.

## Structure
- `src/` — all Python source code
  - `wp1/` — simulation engine (sim.py)
  - `wp2/` — synthetic regime generation and detection (synth_regime.py, job_w2_synth.py, compare_detectors.py)
  - `wp3/` — Gymnasium environment (env.py)
  - `wp4/` — PPO training (job_w4_ppo.py)
  - `wp5/` — OOS evaluation, ablations, detector comparison
- `config/` — JSON config files for all experiments
- `results/runs/` — experiment outputs (git ignored)
- `data/processed/` — intermediate data (git ignored)
- `manuscript/` — thesis text

## Strategies
- **Naive**: fixed symmetric half-spread (h=2 ticks)
- **Avellaneda-Stoikov**: inventory-aware analytical baseline
- **PPO-aware**: PPO agent with regime label in observation
- **PPO-blind**: PPO agent without regime label

## Regime Detection
Three detector variants implemented and compared:
- `rv_baseline`: rolling realized volatility, 60.7% accuracy
- `rv_dwell`: RV + dwell filter, 60.4% accuracy
- `hmm`: GaussianHMM on sigma_hat, 81.8% accuracy

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
- Both PPO variants outperform classical baselines in Sharpe (~4x); AS produces higher absolute equity
- Regime-aware vs regime-blind: null result (p=0.261 Sharpe-based paired t-test, 20 seeds)
- Pilot (3 seeds): null result observed across all three detector variants
- Full detector robustness experiment: 3 detectors x 20 seeds x 2 strategies = 120 models (in progress)

## Reproducibility
Every run produces a timestamped directory under results/runs/ containing:
config_snapshot.json, meta.json, run.log, metrics.csv, plots/
