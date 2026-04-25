"""WP5.5 signal calibration sweep.

Two separate one-dimensional sweeps over the noise alpha and lag k
parameters of the volatility-signal degradation transforms. NO PPO,
NO training — pure offline numpy diagnostic to inform parameter
choices for the upcoming Signal Informativeness Sweep.

For each seed, the same clean signal is generated once, then:
  - alpha sweep (k = 0): degraded = apply_noise(clean, alpha * sigma_std)
  - k     sweep (alpha = 0): degraded = apply_lag(clean, k)

Metrics per (parameter, value, seed):
  pearson, nrmse, classification_accuracy, accuracy_drop, regime_crossing_rate.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.wp5_5.job_w55_audit import _build_clean_signal
from src.wp5_5.signal_audit import (
    nrmse,
    pearson_correlation,
    regime_classification_accuracy,
    regime_crossing_rate,
)
from src.wp5_5.signal_degradation import apply_lag, apply_noise


METRIC_COLS = [
    "pearson",
    "nrmse",
    "classification_accuracy",
    "accuracy_drop",
    "regime_crossing_rate",
]


def _compute_metrics(
    clean: np.ndarray,
    degraded: np.ndarray,
    regime_true: list,
    thresh_LM: float,
    thresh_MH: float,
    warmup_end: int,
    clean_acc: float,
) -> dict:
    n = len(clean)
    post_mask = np.zeros(n, dtype=bool)
    post_mask[warmup_end:] = True
    deg_acc = regime_classification_accuracy(
        degraded, regime_true, thresh_LM, thresh_MH, warmup_end
    )
    return {
        "pearson": pearson_correlation(clean, degraded, post_mask),
        "nrmse": nrmse(clean, degraded, post_mask),
        "classification_accuracy": deg_acc,
        "accuracy_drop": clean_acc - deg_acc,
        "regime_crossing_rate": regime_crossing_rate(
            degraded, thresh_LM, thresh_MH, warmup_end
        ),
    }


def run(cfg: dict, ctx) -> None:
    cal = cfg["calibration"]
    alpha_values = [float(a) for a in cal["alpha_values"]]
    k_values = [int(k) for k in cal["k_values"]]
    n_seeds = int(cal["n_seeds"])
    base_seed = int(cfg["seed"])

    rows: list[dict] = []
    for seed_idx in range(n_seeds):
        seed = base_seed + seed_idx
        sigma_clean, regime_true, warmup_end, thresh_LM, thresh_MH = (
            _build_clean_signal(cfg, seed)
        )
        n = len(sigma_clean)
        sigma_std_post = float(np.nanstd(sigma_clean[warmup_end:]))
        clean_acc = regime_classification_accuracy(
            sigma_clean, regime_true, thresh_LM, thresh_MH, warmup_end
        )
        ctx.logger.info(
            f"seed={seed} n={n} warmup_end={warmup_end} "
            f"sigma_std_post={sigma_std_post:.6f} clean_acc={clean_acc:.4f} "
            f"thresh_LM={thresh_LM:.6f} thresh_MH={thresh_MH:.6f}"
        )

        rng = np.random.default_rng(seed)
        for alpha in alpha_values:
            noise_std = alpha * sigma_std_post
            degraded = apply_noise(sigma_clean, noise_std, rng)
            m = _compute_metrics(
                sigma_clean, degraded, regime_true,
                thresh_LM, thresh_MH, warmup_end, clean_acc,
            )
            rows.append({"parameter": "alpha", "value": float(alpha), "seed": seed, **m})

        for k in k_values:
            degraded = apply_lag(sigma_clean, k)
            m = _compute_metrics(
                sigma_clean, degraded, regime_true,
                thresh_LM, thresh_MH, warmup_end, clean_acc,
            )
            rows.append({"parameter": "k", "value": float(k), "seed": seed, **m})

    df_per_seed = pd.DataFrame(rows)
    per_seed_path = Path(ctx.run_dir) / "metrics_calibration_per_seed.csv"
    df_per_seed.to_csv(per_seed_path, index=False)
    ctx.logger.info(f"Wrote {per_seed_path.as_posix()}")

    agg = (
        df_per_seed
        .groupby(["parameter", "value"], sort=False)[METRIC_COLS]
        .agg(["mean", "std"])
    )
    agg.columns = [f"{m}_{stat}" for m, stat in agg.columns]
    agg = agg.reset_index()
    agg_path = Path(ctx.run_dir) / "metrics_calibration_aggregated.csv"
    agg.to_csv(agg_path, index=False)
    ctx.logger.info(f"Wrote {agg_path.as_posix()}")

    print()
    print(
        "| parameter | value | pearson_mean | nrmse_mean | accuracy_drop_mean | crossing_rate_mean |"
    )
    print("|---|---:|---:|---:|---:|---:|")
    for _, r in agg.iterrows():
        print(
            f"| {r['parameter']} | {r['value']:g} | "
            f"{r['pearson_mean']:.4f} | {r['nrmse_mean']:.4f} | "
            f"{r['accuracy_drop_mean']:.4f} | {r['regime_crossing_rate_mean']:.4f} |"
        )
    print()
