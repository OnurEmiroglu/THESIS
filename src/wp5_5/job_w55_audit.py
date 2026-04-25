"""WP5.5 signal audit job.

Generates a clean synthetic volatility signal, builds four degraded variants
(noisy, lagged, coarsened, none) using cutpoints fixed from the clean warmup
distribution, computes a small audit metric ladder, and writes a summary.

No PPO training here — the audit is purely offline and must finish in <10 min.
"""

from __future__ import annotations

import copy
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.wp2.synth_regime import (
    REGIME_LABELS,
    calibrate_thresholds,
    compute_rolling_rv,
    generate_mid_series,
    generate_regime_series,
)
from src.wp5_5.signal_audit import (
    class_separability,
    pearson_correlation,
    regime_classification_accuracy,
    spearman_correlation,
    threshold_overlap_rate,
)
from src.wp5_5.signal_degradation import (
    apply_coarsen,
    apply_lag,
    apply_noise,
    apply_remove,
    compute_clean_cutpoints,
)


CONDITION_ORDER = ["clean", "noisy", "lagged", "coarsened", "none"]
METRIC_ORDER = [
    "spearman",
    "pearson",
    "classification_accuracy",
    "separability",
    "threshold_overlap",
]


def _build_clean_signal(cfg: dict, seed: int):
    """Generate clean (mid, sigma_hat, regime_true, thresholds, warmup_end)."""
    rng = np.random.default_rng(seed)
    n_steps = int(cfg["episode"]["n_steps"])
    rv_window = int(cfg["regime"]["rv_window"])
    warmup_end = int(cfg["regime"]["warmup_steps"])

    regime_cfg = copy.deepcopy(cfg.get("regime", {}))
    regime_cfg.setdefault("sigma_mid_ticks_base", float(cfg["market"].get("sigma_mid_ticks", 0.5)))
    regime_cfg.setdefault("sigma_mult", [0.6, 1.0, 1.8])
    cfg_local = {**cfg, "regime": regime_cfg}

    regime_true_int = generate_regime_series(n_steps, seed, cfg=cfg_local, rng=rng)
    mid, _ = generate_mid_series(regime_true_int, cfg_local, rng)
    _, sigma_hat = compute_rolling_rv(mid, rv_window, float(cfg["market"]["tick_size"]))
    thresh_LM, thresh_MH = calibrate_thresholds(sigma_hat, warmup_end)

    regime_true_str = ["M"] + [REGIME_LABELS[int(r)] for r in regime_true_int]
    return sigma_hat, regime_true_str, warmup_end, thresh_LM, thresh_MH


def _plot_ladder(results: dict, plots_dir: Path) -> Path:
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    flat = axes.flatten()
    for i, metric in enumerate(METRIC_ORDER):
        ax = flat[i]
        vals = [results[c][metric] for c in CONDITION_ORDER]
        colors = ["seagreen" if c == "clean" else "steelblue" for c in CONDITION_ORDER]
        ax.bar(CONDITION_ORDER, vals, color=colors)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
    flat[-1].axis("off")
    fig.suptitle("WP5.5 Signal Audit Ladder", y=1.02)
    plt.tight_layout()
    out = plots_dir / "signal_audit_ladder.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


NONE_UNGATED_METRICS = ("classification_accuracy", "threshold_overlap")


def _evaluate_flags(results: dict) -> tuple[dict, str]:
    clean = results["clean"]
    none = results["none"]

    # (a) Direction: expected monotone change from clean → none.
    # Under the constant-input 'none' condition, classification_accuracy and
    # threshold_overlap are structurally undefined (they reflect fill-value /
    # threshold geometry, not signal information), so they are reported but
    # not gated.
    direction_checks = {
        "spearman": none["spearman"] < clean["spearman"],
        "pearson": none["pearson"] < clean["pearson"],
        "classification_accuracy": (
            none["classification_accuracy"] < clean["classification_accuracy"]
        ),
        "separability": none["separability"] < clean["separability"],
        "threshold_overlap": none["threshold_overlap"] > clean["threshold_overlap"],
    }
    gated_direction_keys = [k for k in direction_checks if k not in NONE_UNGATED_METRICS]
    violations = sum(1 for k in gated_direction_keys if not direction_checks[k])
    flag_direction = violations <= 1

    # (b) Separation: no two conditions identical on every metric (tol 0.01).
    flag_separation = True
    for i in range(len(CONDITION_ORDER)):
        for j in range(i + 1, len(CONDITION_ORDER)):
            a, b = CONDITION_ORDER[i], CONDITION_ORDER[j]
            max_diff = max(abs(results[a][m] - results[b][m]) for m in METRIC_ORDER)
            if max_diff <= 0.01:
                flag_separation = False

    # (c) Coarsened must not "cheat" by beating clean classification.
    flag_coarsen_safety = (
        results["coarsened"]["classification_accuracy"]
        <= clean["classification_accuracy"] + 0.05
    )

    # (d) Monotonicity across the full ladder, for ≥3 of 5 metrics.
    # For the ungated metrics on the 'none' condition (classification_accuracy,
    # threshold_overlap) the 'none' endpoint is excluded from the monotonicity
    # check: those values are structurally undefined under constant input.
    mono_count = 0
    mono_detail = {}
    for metric in METRIC_ORDER:
        if metric in NONE_UNGATED_METRICS:
            vals = [results[c][metric] for c in CONDITION_ORDER if c != "none"]
        else:
            vals = [results[c][metric] for c in CONDITION_ORDER]
        if metric == "threshold_overlap":
            is_mono = all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))
        else:
            is_mono = all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))
        mono_detail[metric] = is_mono
        if is_mono:
            mono_count += 1
    flag_monotonicity = mono_count >= 3

    flags = {
        "direction": flag_direction,
        "separation": flag_separation,
        "coarsen_safety": flag_coarsen_safety,
        "monotonicity": flag_monotonicity,
    }

    n_fail = sum(1 for v in flags.values() if not v)
    if n_fail == 0:
        recommendation = "PROCEED"
    elif n_fail == 1:
        recommendation = "REVIEW"
    else:
        recommendation = "REDESIGN"

    flags["_direction_detail"] = direction_checks
    flags["_monotonicity_detail"] = mono_detail
    return flags, recommendation


def _write_summary(
    ctx,
    results: dict,
    flags: dict,
    recommendation: str,
    cutpoints: np.ndarray,
    clean_sigma_std: float,
    thresh_LM: float,
    thresh_MH: float,
    noise_std: float,
    lag_k: int,
    n_bins: int,
    fill_value: float,
    band_pct: float,
) -> Path:
    md = []
    md.append("# WP5.5 Signal Audit Summary")
    md.append("")
    md.append(f"Run ID: `{ctx.run_id}`")
    md.append("")
    md.append("## Parameters")
    md.append("")
    ratio = noise_std / clean_sigma_std if clean_sigma_std > 0 else float("nan")
    md.append(f"- clean_sigma_std (post-warmup): {clean_sigma_std:.6f}")
    md.append(f"- noise_std: {noise_std}  (noise_std / clean_sigma_std = {ratio:.4f})")
    md.append(f"- lag_k_steps: {lag_k}")
    md.append(f"- n_bins: {n_bins}")
    md.append(f"- fill_value: {fill_value}")
    md.append(f"- threshold_band_pct: {band_pct}")
    md.append(f"- thresh_LM: {thresh_LM:.6f}")
    md.append(f"- thresh_MH: {thresh_MH:.6f}")
    md.append(f"- cutpoints (interior, len={len(cutpoints)}): {cutpoints.tolist()}")
    md.append("")
    md.append("## Metric Table")
    md.append("")
    header = "| condition | " + " | ".join(METRIC_ORDER) + " |"
    sep = "|" + "---|" * (len(METRIC_ORDER) + 1)
    md.append(header)
    md.append(sep)
    for c in CONDITION_ORDER:
        row = " | ".join(f"{results[c][m]:.4f}" for m in METRIC_ORDER)
        md.append(f"| {c} | {row} |")
    md.append("")
    md.append("## Policy: ungated metrics under the none condition")
    md.append("")
    md.append(
        "Under constant-input conditions, regime_classification_accuracy and "
        "threshold_overlap_rate become structurally undefined; they reflect the "
        "relationship between the chosen fill value and calibrated thresholds "
        "rather than signal information content. These metrics are therefore "
        "reported but not used in PASS/FAIL evaluation for the none condition."
    )
    md.append("")
    md.append("## Flags")
    md.append("")
    for key in ("direction", "separation", "coarsen_safety", "monotonicity"):
        status = "PASS" if flags[key] else "FAIL"
        md.append(f"- {key}: **{status}**")
    md.append("")
    md.append("### Direction detail (clean → none)")
    for k, v in flags["_direction_detail"].items():
        ungated_tag = " [REPORTED, NOT GATED]" if k in NONE_UNGATED_METRICS else ""
        md.append(f"  - {k}: {'OK' if v else 'VIOLATION'}{ungated_tag}")
    md.append("")
    md.append("### Monotonicity detail (clean → noisy → lagged → coarsened → none)")
    for k, v in flags["_monotonicity_detail"].items():
        ungated_tag = (
            " [none endpoint excluded; REPORTED, NOT GATED]"
            if k in NONE_UNGATED_METRICS
            else ""
        )
        md.append(f"  - {k}: {'monotone' if v else 'non-monotone'}{ungated_tag}")
    md.append("")
    md.append(f"## Overall Recommendation: **{recommendation}**")
    md.append("")

    out = Path(ctx.run_dir) / "audit_summary.md"
    out.write_text("\n".join(md), encoding="utf-8")
    return out


def run(cfg: dict, ctx) -> None:
    seed = int(cfg["seed"])
    audit_cfg = cfg["audit"]
    noise_std_raw = audit_cfg["noise_std"]
    lag_k = int(audit_cfg["lag_k_steps"])
    n_bins = int(audit_cfg["n_bins"])
    fill_value = float(audit_cfg["fill_value"])
    band_pct = float(audit_cfg.get("threshold_band_pct", 0.05))

    # 1. Clean signal
    sigma_hat_clean, regime_true_str, warmup_end, thresh_LM, thresh_MH = (
        _build_clean_signal(cfg, seed)
    )
    n = len(sigma_hat_clean)
    clean_sigma_std = float(np.nanstd(sigma_hat_clean[warmup_end:]))
    ctx.logger.info(
        f"Clean signal: n={n}, warmup_end={warmup_end}, "
        f"clean_sigma_std(post)={clean_sigma_std:.6f}, "
        f"thresh_LM={thresh_LM:.6f}, thresh_MH={thresh_MH:.6f}"
    )

    # Resolve noise_std: 'auto' -> 0.5 * clean_sigma_std_post_warmup.
    if isinstance(noise_std_raw, str) and noise_std_raw.strip().lower() == "auto":
        noise_std = 0.5 * clean_sigma_std
        ctx.logger.info(
            f"noise_std='auto' resolved to {noise_std:.6f} "
            f"(= 0.5 * clean_sigma_std_post_warmup = 0.5 * {clean_sigma_std:.6f})"
        )
    else:
        noise_std = float(noise_std_raw)
        ctx.logger.info(f"noise_std={noise_std:.6f} (fixed from config)")

    # 2. Fixed cutpoints — computed exactly once from the clean warmup region.
    cutpoints = compute_clean_cutpoints(sigma_hat_clean, warmup_end, n_bins=n_bins)
    ctx.logger.info(f"Clean cutpoints (n_bins={n_bins}): {cutpoints.tolist()}")

    # 3. Build four degraded versions.
    deg_rng = np.random.default_rng(seed)
    sigma_noisy = apply_noise(sigma_hat_clean, noise_std, deg_rng)
    sigma_lagged = apply_lag(sigma_hat_clean, lag_k)
    sigma_coarse = apply_coarsen(sigma_hat_clean, cutpoints)
    sigma_none = apply_remove(sigma_hat_clean, fill_value=fill_value)

    # 4. Shape/dtype assertions.
    for name, arr in [
        ("noisy", sigma_noisy),
        ("lagged", sigma_lagged),
        ("coarsened", sigma_coarse),
        ("none", sigma_none),
    ]:
        assert arr.shape == sigma_hat_clean.shape, f"{name}: shape mismatch"
        assert arr.dtype == sigma_hat_clean.dtype, f"{name}: dtype mismatch"

    # 5. None condition post-warmup must be exactly fill_value.
    assert np.all(sigma_none[warmup_end:] == fill_value), (
        "none condition post-warmup contains non-fill values"
    )

    # 6. Compute metrics for each condition.
    conditions = {
        "clean": sigma_hat_clean,
        "noisy": sigma_noisy,
        "lagged": sigma_lagged,
        "coarsened": sigma_coarse,
        "none": sigma_none,
    }
    post_mask = np.zeros(n, dtype=bool)
    post_mask[warmup_end:] = True

    rows = []
    results: dict[str, dict[str, float]] = {}
    for cond in CONDITION_ORDER:
        deg = conditions[cond]
        m = {
            "spearman": spearman_correlation(sigma_hat_clean, deg, post_mask),
            "pearson": pearson_correlation(sigma_hat_clean, deg, post_mask),
            "classification_accuracy": regime_classification_accuracy(
                deg, regime_true_str, thresh_LM, thresh_MH, warmup_end
            ),
            "separability": class_separability(deg, regime_true_str, warmup_end),
            "threshold_overlap": threshold_overlap_rate(
                deg, thresh_LM, thresh_MH, warmup_end, band_pct=band_pct
            ),
        }
        results[cond] = m
        for metric, value in m.items():
            rows.append({"condition": cond, "metric": metric, "value": float(value)})
        ctx.logger.info(
            f"[{cond}] spearman={m['spearman']:.4f} pearson={m['pearson']:.4f} "
            f"acc={m['classification_accuracy']:.4f} sep={m['separability']:.2f} "
            f"overlap={m['threshold_overlap']:.4f}"
        )

    df = pd.DataFrame(rows, columns=["condition", "metric", "value"])
    csv_path = Path(ctx.run_dir) / "metrics_signal_audit.csv"
    df.to_csv(csv_path, index=False)
    ctx.logger.info(f"Wrote {csv_path.as_posix()}")

    # 7. Ladder figure.
    fig_path = _plot_ladder(results, Path(ctx.plots_dir))
    ctx.logger.info(f"Wrote {fig_path.as_posix()}")

    # 8. Flags + markdown summary.
    flags, recommendation = _evaluate_flags(results)
    md_path = _write_summary(
        ctx,
        results=results,
        flags=flags,
        recommendation=recommendation,
        cutpoints=cutpoints,
        clean_sigma_std=clean_sigma_std,
        thresh_LM=thresh_LM,
        thresh_MH=thresh_MH,
        noise_std=noise_std,
        lag_k=lag_k,
        n_bins=n_bins,
        fill_value=fill_value,
        band_pct=band_pct,
    )
    ctx.logger.info(f"Wrote {md_path.as_posix()}")
    ctx.logger.info(
        f"Flags: direction={flags['direction']} separation={flags['separation']} "
        f"coarsen_safety={flags['coarsen_safety']} monotonicity={flags['monotonicity']}"
    )
    ctx.logger.info(f"Recommendation: {recommendation}")
