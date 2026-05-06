"""WP6 Chapter 5 -- Plot 2: paired-seed scatter, combined vs sigma_only.

Reads docs/internal/wp6_sweep_full/metrics_sweep_full.csv and produces a
2x2 paired-seed scatter (one panel per informative condition: full, noisy,
lagged, coarsened). Excludes 'none' (sigma_only structurally undefined).

Per panel:
  - x = sigma_only sharpe_like, y = combined sharpe_like, paired on seed
  - y=x identity line; points below identity = combined underperforms
  - paired t-test p, Cohen's dz, n_below/n_total annotated
  - TOST for NON-equivalence (delta=0.05):
      H0: |mean_diff| <= delta  (combined ~equivalent to sigma_only)
      H1: |mean_diff|  > delta  (combined meaningfully different)
    Implemented as union-intersection of two one-sided tests at alpha=0.05;
    reject H0 iff min(p_lower, p_upper) < 0.05. This is the OPPOSITE of WP5's
    TOST usage (where we proved equivalence aware ~ blind).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
SWEEP_DIR = ROOT / "docs" / "internal" / "wp6_sweep_full"
METRICS_CSV = SWEEP_DIR / "metrics_sweep_full.csv"
PLOTS_DIR = SWEEP_DIR / "plots"
SUMMARY_CSV = SWEEP_DIR / "summary_paired_combined_vs_sigma.csv"

CONDITIONS = ["full", "noisy", "lagged", "coarsened"]  # 'none' excluded by design
DELTA = 0.05
ALPHA = 0.05


def paired_stats(seeds_x: np.ndarray, x: np.ndarray,
                 seeds_y: np.ndarray, y: np.ndarray, condition: str) -> dict:
    """Compute paired stats for combined (y) vs sigma_only (x).

    diff = combined - sigma_only  (negative => combined worse)
    """
    if not np.array_equal(seeds_x, seeds_y):
        raise RuntimeError(f"[{condition}] seed sets differ between sigma_only and combined")

    diff = y - x
    n = len(diff)
    mean_diff = float(diff.mean())
    sd_diff = float(diff.std(ddof=1))
    se_diff = sd_diff / np.sqrt(n)
    t_stat, p_paired = stats.ttest_rel(y, x)
    cohens_dz = mean_diff / sd_diff if sd_diff > 0 else float("nan")
    n_below = int((diff < 0).sum())

    # TOST for non-equivalence (inverse of WP5).
    # Null (equivalence) interval: [-DELTA, +DELTA]. Reject H0 if min one-sided p < alpha.
    df_t = n - 1
    t_lower = (mean_diff + DELTA) / se_diff   # large negative => mean_diff << -DELTA
    p_lower = float(stats.t.cdf(t_lower, df=df_t))
    t_upper = (mean_diff - DELTA) / se_diff   # large positive => mean_diff >>  DELTA
    p_upper = float(1.0 - stats.t.cdf(t_upper, df=df_t))
    tost_p = min(p_lower, p_upper)
    tost_reject = tost_p < ALPHA

    return {
        "condition": condition,
        "n_below": n_below,
        "n_total": int(n),
        "mean_diff": mean_diff,
        "t_stat": float(t_stat),
        "p_paired": float(p_paired),
        "cohens_dz": float(cohens_dz),
        "tost_p": float(tost_p),
        "tost_reject_h0_at_alpha_0.05": bool(tost_reject),
    }


def collect_pairs(df: pd.DataFrame) -> dict:
    """Return {condition: (seeds, sigma_vals, combined_vals)} sorted by seed."""
    out = {}
    for cond in CONDITIONS:
        sigma_df = df[(df["condition"] == cond) & (df["variant"] == "sigma_only")].sort_values("seed")
        comb_df = df[(df["condition"] == cond) & (df["variant"] == "combined")].sort_values("seed")
        seeds_s = sigma_df["seed"].to_numpy()
        seeds_c = comb_df["seed"].to_numpy()
        if not np.array_equal(seeds_s, seeds_c):
            raise RuntimeError(f"[{cond}] seed mismatch: sigma={seeds_s.tolist()} comb={seeds_c.tolist()}")
        out[cond] = (seeds_s,
                     sigma_df["sharpe_like"].to_numpy(dtype=float),
                     comb_df["sharpe_like"].to_numpy(dtype=float))
    return out


def make_plot(pairs: dict, summary_rows: list[dict], out_png: Path, out_pdf: Path) -> None:
    # Global axis limits across all panels for visual comparability.
    all_vals = np.concatenate([np.concatenate([s, c]) for (_, s, c) in pairs.values()])
    pad = 0.03 * (all_vals.max() - all_vals.min())
    lo = float(all_vals.min() - pad)
    hi = float(all_vals.max() + pad)

    fig, axes = plt.subplots(2, 2, figsize=(10.0, 9.4), sharex=True, sharey=True)
    axes = axes.flatten()

    summary_by_cond = {r["condition"]: r for r in summary_rows}

    for ax, cond in zip(axes, CONDITIONS):
        _, x, y = pairs[cond]
        ax.plot([lo, hi], [lo, hi], color="#888888", linestyle="--", linewidth=1.2, zorder=1)
        ax.scatter(x, y, s=58, color="#1f77b4", edgecolor="black",
                   linewidth=0.7, alpha=0.7, zorder=3)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.3)
        ax.set_title(cond, fontsize=12, fontweight="bold")
        ax.set_xlabel("sigma_only Sharpe-like")
        ax.set_ylabel("combined Sharpe-like")

        s = summary_by_cond[cond]
        # Place annotation in upper-left (combined<sigma_only puts points below diag).
        text = (f"{s['n_below']}/{s['n_total']} below identity\n"
                f"mean_diff = {s['mean_diff']:+.3f}\n"
                f"paired t p = {s['p_paired']:.2e}\n"
                f"Cohen's dz = {s['cohens_dz']:+.3f}\n"
                f"TOST non-equiv: p={s['tost_p']:.2e}, "
                f"reject H0: {'yes' if s['tost_reject_h0_at_alpha_0.05'] else 'no'}")
        ax.text(0.03, 0.97, text, transform=ax.transAxes,
                fontsize=8.5, va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.35",
                          facecolor="white", edgecolor="#bbbbbb", alpha=0.92))

    fig.suptitle("Paired-seed comparison: combined vs sigma_only across conditions",
                 fontsize=13, fontweight="bold", y=0.995)
    caption = ("Points below identity line indicate combined underperforms sigma_only "
               f"for that seed. Delta for TOST = {DELTA:.2f}.")
    fig.text(0.5, 0.005, caption, ha="center", va="bottom",
             fontsize=8.5, style="italic", color="#333333")

    fig.tight_layout(rect=(0, 0.025, 1, 0.97))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=180, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(METRICS_CSV)
    pairs = collect_pairs(df)

    summary_rows = []
    for cond, (seeds, x, y) in pairs.items():
        summary_rows.append(paired_stats(seeds, x, seeds, y, cond))

    summary_df = pd.DataFrame(summary_rows, columns=[
        "condition", "n_below", "n_total", "mean_diff", "t_stat", "p_paired",
        "cohens_dz", "tost_p", "tost_reject_h0_at_alpha_0.05",
    ])
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(SUMMARY_CSV, index=False)

    out_png = PLOTS_DIR / "paired_seed_combined_vs_sigma.png"
    out_pdf = PLOTS_DIR / "paired_seed_combined_vs_sigma.pdf"
    make_plot(pairs, summary_rows, out_png, out_pdf)

    # === Sanity checks ===
    print("=== Sanity checks ===")
    # 1. n_total == 20 every condition
    n_ok = all(r["n_total"] == 20 for r in summary_rows)
    print(f"  [1] n_total == 20 for every condition: {n_ok}")
    for r in summary_rows:
        print(f"        {r['condition']}: n_total = {r['n_total']}")
    # 2. mean_diff negative everywhere
    neg_ok = all(r["mean_diff"] < 0 for r in summary_rows)
    print(f"  [2] mean_diff < 0 in all 4 conditions: {neg_ok}")
    for r in summary_rows:
        print(f"        {r['condition']}: mean_diff = {r['mean_diff']:+.6f}")
    # 3. Seed sets paired
    print(f"  [3] Seed sets identical between sigma_only and combined per condition:")
    for cond, (seeds, _, _) in pairs.items():
        sigma_seeds = set(df[(df["condition"] == cond) & (df["variant"] == "sigma_only")]["seed"].tolist())
        comb_seeds = set(df[(df["condition"] == cond) & (df["variant"] == "combined")]["seed"].tolist())
        match = sigma_seeds == comb_seeds
        print(f"        {cond}: match = {match} (n_sigma={len(sigma_seeds)}, n_comb={len(comb_seeds)})")
    # 4. 'none' excluded
    excl_ok = "none" not in CONDITIONS
    print(f"  [4] 'none' excluded from analysis: {excl_ok} (CONDITIONS = {CONDITIONS})")
    # 5. Print delta
    print(f"  [5] DELTA used in TOST = {DELTA:.4f}")
    print()

    # === Summary CSV contents ===
    print("=== summary_paired_combined_vs_sigma.csv ===")
    with pd.option_context("display.float_format", "{:.6f}".format,
                            "display.width", 200,
                            "display.max_columns", None):
        print(summary_df.to_string(index=False))
    print()
    print(f"Saved summary CSV: {SUMMARY_CSV}")
    print(f"Saved plot (PNG): {out_png}")
    print(f"Saved plot (PDF): {out_pdf}")


if __name__ == "__main__":
    main()
