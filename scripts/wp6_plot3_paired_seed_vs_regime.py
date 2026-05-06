"""WP6 Chapter 5 -- Plot 3: paired-seed scatter, combined vs regime_only.

Reads docs/internal/wp6_sweep_full/metrics_sweep_full.csv and produces a
2x2 paired-seed scatter (one panel per informative condition: full, noisy,
lagged, coarsened). Excludes 'none' (combined collapses to regime_only there
by construction).

Question: in the combined variant does the policy still extract value from
sigma_hat beyond what regime_only alone provides?
  (a) combined > regime_only seed-paired (sigma channel still contributes)
  (b) combined ~ regime_only seed-paired (sigma channel crowded out)

TOST direction in this script: EQUIVALENCE (H1: |diff| <= delta).
This is the OPPOSITE of Plot 2 (which tested non-equivalence). For
equivalence we require BOTH one-sided tests to reject, hence
  tost_p = max(p_lower, p_upper)
and we reject H0 of non-equivalence iff tost_p < alpha.
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
SUMMARY_CSV = SWEEP_DIR / "summary_paired_combined_vs_regime.csv"

CONDITIONS = ["full", "noisy", "lagged", "coarsened"]  # 'none' excluded by design
DELTA = 0.05
ALPHA = 0.05


def iqr(arr: np.ndarray) -> float:
    q75, q25 = np.percentile(arr, [75, 25])
    return float(q75 - q25)


def paired_stats(seeds_x: np.ndarray, x: np.ndarray,
                 seeds_y: np.ndarray, y: np.ndarray, condition: str) -> dict:
    """Compute paired stats for combined (y) vs regime_only (x).

    diff = combined - regime_only  (positive => combined adds value)
    """
    if not np.array_equal(seeds_x, seeds_y):
        raise RuntimeError(f"[{condition}] seed sets differ between regime_only and combined")

    diff = y - x
    n = len(diff)
    mean_diff = float(diff.mean())
    sd_diff = float(diff.std(ddof=1))
    se_diff = sd_diff / np.sqrt(n)
    t_stat, p_paired = stats.ttest_rel(y, x)
    cohens_dz = mean_diff / sd_diff if sd_diff > 0 else float("nan")
    n_above = int((diff > 0).sum())

    # TOST for EQUIVALENCE (standard direction, matches WP5 usage).
    # H0: |mean_diff| >  DELTA  (meaningfully different)
    # H1: |mean_diff| <= DELTA  (practically equivalent)
    # Two one-sided tests against the boundary; reject H0 iff BOTH reject.
    df_t = n - 1
    # Lower bound test: H0: mean_diff <= -DELTA vs H1: mean_diff > -DELTA
    t_lower = (mean_diff + DELTA) / se_diff
    p_lower = float(1.0 - stats.t.cdf(t_lower, df=df_t))
    # Upper bound test: H0: mean_diff >=  DELTA vs H1: mean_diff <  DELTA
    t_upper = (mean_diff - DELTA) / se_diff
    p_upper = float(stats.t.cdf(t_upper, df=df_t))
    tost_p = max(p_lower, p_upper)
    tost_reject = tost_p < ALPHA

    return {
        "condition": condition,
        "n_above": n_above,
        "n_total": int(n),
        "mean_diff": mean_diff,
        "t_stat": float(t_stat),
        "p_paired": float(p_paired),
        "cohens_dz": float(cohens_dz),
        "tost_p": float(tost_p),
        "tost_reject_h0_at_alpha_0.05": bool(tost_reject),
        "std_combined": float(np.std(y, ddof=1)),
        "std_regime_only": float(np.std(x, ddof=1)),
        "std_diff": sd_diff,
        "iqr_combined": iqr(y),
        "iqr_regime_only": iqr(x),
        "iqr_diff": iqr(diff),
    }


def collect_pairs(df: pd.DataFrame) -> dict:
    """Return {condition: (seeds, regime_only_vals, combined_vals)} sorted by seed."""
    out = {}
    for cond in CONDITIONS:
        reg_df = df[(df["condition"] == cond) & (df["variant"] == "regime_only")].sort_values("seed")
        comb_df = df[(df["condition"] == cond) & (df["variant"] == "combined")].sort_values("seed")
        seeds_r = reg_df["seed"].to_numpy()
        seeds_c = comb_df["seed"].to_numpy()
        if not np.array_equal(seeds_r, seeds_c):
            raise RuntimeError(f"[{cond}] seed mismatch: regime={seeds_r.tolist()} comb={seeds_c.tolist()}")
        out[cond] = (seeds_r,
                     reg_df["sharpe_like"].to_numpy(dtype=float),
                     comb_df["sharpe_like"].to_numpy(dtype=float))
    return out


def make_plot(pairs: dict, summary_rows: list[dict], out_png: Path, out_pdf: Path) -> None:
    all_vals = np.concatenate([np.concatenate([r, c]) for (_, r, c) in pairs.values()])
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
        ax.set_xlabel("regime_only Sharpe-like")
        ax.set_ylabel("combined Sharpe-like")

        s = summary_by_cond[cond]
        text = (f"{s['n_above']}/{s['n_total']} above identity\n"
                f"mean_diff = {s['mean_diff']:+.3f}\n"
                f"paired t p = {s['p_paired']:.2e}\n"
                f"Cohen's dz = {s['cohens_dz']:+.3f}\n"
                f"TOST equiv: p={s['tost_p']:.2e}, "
                f"reject H0: {'yes' if s['tost_reject_h0_at_alpha_0.05'] else 'no'}")
        ax.text(0.03, 0.97, text, transform=ax.transAxes,
                fontsize=8.5, va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.35",
                          facecolor="white", edgecolor="#bbbbbb", alpha=0.92))

    fig.suptitle("Paired-seed comparison: combined vs regime_only across conditions",
                 fontsize=13, fontweight="bold", y=0.995)
    caption = ("Points above identity line indicate combined adds value over "
               f"regime_only for that seed. Delta for TOST = {DELTA:.2f}.")
    fig.text(0.5, 0.005, caption, ha="center", va="bottom",
             fontsize=8.5, style="italic", color="#333333")

    fig.tight_layout(rect=(0, 0.025, 1, 0.97))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=180, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


def label_outcome(row: dict) -> str:
    if row["mean_diff"] > 0 and row["p_paired"] < 0.05:
        return "OUTCOME (a): combined > regime_only"
    if row["tost_reject_h0_at_alpha_0.05"]:
        return "OUTCOME (b): combined ~ regime_only"
    return "OUTCOME (c): inconclusive"


def main() -> None:
    df = pd.read_csv(METRICS_CSV)
    pairs = collect_pairs(df)

    summary_rows = []
    for cond, (seeds, x, y) in pairs.items():
        summary_rows.append(paired_stats(seeds, x, seeds, y, cond))

    cols = [
        "condition", "n_above", "n_total", "mean_diff", "t_stat", "p_paired",
        "cohens_dz", "tost_p", "tost_reject_h0_at_alpha_0.05",
        "std_combined", "std_regime_only", "std_diff",
        "iqr_combined", "iqr_regime_only", "iqr_diff",
    ]
    summary_df = pd.DataFrame(summary_rows, columns=cols)
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(SUMMARY_CSV, index=False)

    out_png = PLOTS_DIR / "paired_seed_combined_vs_regime.png"
    out_pdf = PLOTS_DIR / "paired_seed_combined_vs_regime.pdf"
    make_plot(pairs, summary_rows, out_png, out_pdf)

    # === Sanity checks ===
    print("=== Sanity checks ===")
    # 1. n_total == 20
    n_ok = all(r["n_total"] == 20 for r in summary_rows)
    print(f"  [1] n_total == 20 for every condition: {n_ok}")
    for r in summary_rows:
        print(f"        {r['condition']}: n_total = {r['n_total']}")
    # 2. regime_only is condition-invariant per seed
    print(f"  [2] regime_only is condition-invariant per seed (max |diff| should be 0):")
    ref_seeds, ref_vals, _ = pairs[CONDITIONS[0]]
    ref_map = dict(zip(ref_seeds.tolist(), ref_vals.tolist()))
    for cond in CONDITIONS[1:]:
        s, r, _ = pairs[cond]
        diffs = np.array([r[i] - ref_map[s[i]] for i in range(len(s))])
        max_abs = float(np.abs(diffs).max())
        print(f"        max |regime_only[{CONDITIONS[0]}] - regime_only[{cond}]| = {max_abs:.6e}")
    # 3. Seed sets paired
    print(f"  [3] Seed sets identical between regime_only and combined per condition:")
    for cond in CONDITIONS:
        rseeds = set(df[(df["condition"] == cond) & (df["variant"] == "regime_only")]["seed"].tolist())
        cseeds = set(df[(df["condition"] == cond) & (df["variant"] == "combined")]["seed"].tolist())
        match = rseeds == cseeds
        print(f"        {cond}: match = {match} (n_regime={len(rseeds)}, n_comb={len(cseeds)})")
    # 4. 'none' excluded
    excl_ok = "none" not in CONDITIONS
    print(f"  [4] 'none' excluded from analysis: {excl_ok} (CONDITIONS = {CONDITIONS})")
    # 5. delta
    print(f"  [5] DELTA used in TOST = {DELTA:.4f}")
    # 6. TOST direction
    print(f"  [6] TOST direction in this script: EQUIVALENCE (H1: |diff| <= delta)")
    print()

    # === Summary CSV contents ===
    print("=== summary_paired_combined_vs_regime.csv ===")
    with pd.option_context("display.float_format", "{:.6f}".format,
                            "display.width", 220,
                            "display.max_columns", None):
        print(summary_df.to_string(index=False))
    print()

    # === Outcome labels ===
    print("=== Per-condition outcome (auto-classified) ===")
    for r in summary_rows:
        print(f"  {r['condition']:<10s} -> {label_outcome(r)}")
    print()
    print(f"Saved summary CSV: {SUMMARY_CSV}")
    print(f"Saved plot (PNG): {out_png}")
    print(f"Saved plot (PDF): {out_pdf}")


if __name__ == "__main__":
    main()
