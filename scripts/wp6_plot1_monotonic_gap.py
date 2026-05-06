"""WP6 Chapter 5 — Plot 1: monotonic-gap plot.

Reads docs/internal/wp6_sweep_full/metrics_sweep_full.csv, aggregates mean
sharpe_like by (condition, variant) with 95% CI across 20 seeds (t-critical,
df=n-1), and produces the monotonic-gap plot showing how each variant degrades
across the signal-degradation axis: full -> noisy -> lagged -> coarsened -> none.

By design:
  - regime_only and oracle_pure are condition-invariant (do not consume sigma_hat).
  - sigma_only is structurally undefined in the 'none' condition (NaN, not plotted).
  - 'combined' in 'none' collapses to regime_only (use_sigma=False, regime_source=hat).
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
SUMMARY_CSV = SWEEP_DIR / "summary_condition_variant.csv"

CONDITION_ORDER = ["full", "noisy", "lagged", "coarsened", "none"]
VARIANT_ORDER = [
    "sigma_only",
    "combined",
    "regime_only",
    "oracle_full",
    "oracle_pure",
]

# Visual styling: emphasize sigma_only and combined; anchors are dashed/lighter.
VARIANT_STYLE = {
    "sigma_only":  {"color": "#1f77b4", "linestyle": "-",  "linewidth": 2.4, "marker": "o", "alpha": 1.0, "label": "sigma_only (emphasized)"},
    "combined":    {"color": "#d62728", "linestyle": "-",  "linewidth": 2.4, "marker": "s", "alpha": 1.0, "label": "combined (emphasized)"},
    "regime_only": {"color": "#7f7f7f", "linestyle": "--", "linewidth": 1.4, "marker": "^", "alpha": 0.75, "label": "regime_only (anchor, condition-invariant)"},
    "oracle_full": {"color": "#2ca02c", "linestyle": "-",  "linewidth": 1.6, "marker": "D", "alpha": 0.85, "label": "oracle_full"},
    "oracle_pure": {"color": "#9467bd", "linestyle": "--", "linewidth": 1.4, "marker": "v", "alpha": 0.75, "label": "oracle_pure (anchor, condition-invariant)"},
}


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cond in CONDITION_ORDER:
        for var in VARIANT_ORDER:
            sub = df[(df["condition"] == cond) & (df["variant"] == var)]
            n = len(sub)
            if n == 0:
                rows.append({"condition": cond, "variant": var, "n": 0,
                             "mean": np.nan, "std": np.nan, "sem": np.nan,
                             "ci95_lo": np.nan, "ci95_hi": np.nan})
                continue
            vals = sub["sharpe_like"].to_numpy()
            mean = float(vals.mean())
            std = float(vals.std(ddof=1)) if n > 1 else 0.0
            sem = std / np.sqrt(n) if n > 1 else 0.0
            tcrit = float(stats.t.ppf(0.975, df=n - 1)) if n > 1 else 0.0
            half = tcrit * sem
            rows.append({"condition": cond, "variant": var, "n": n,
                         "mean": mean, "std": std, "sem": sem,
                         "ci95_lo": mean - half, "ci95_hi": mean + half})
    return pd.DataFrame(rows)


def make_plot(summary: pd.DataFrame, out_png: Path, out_pdf: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 5.6))
    x_pos = np.arange(len(CONDITION_ORDER))

    for var in VARIANT_ORDER:
        sub = summary[summary["variant"] == var].set_index("condition").reindex(CONDITION_ORDER)
        means = sub["mean"].to_numpy(dtype=float)
        lo = sub["ci95_lo"].to_numpy(dtype=float)
        hi = sub["ci95_hi"].to_numpy(dtype=float)
        yerr_lo = means - lo
        yerr_hi = hi - means
        mask = ~np.isnan(means)
        style = VARIANT_STYLE[var]
        ax.errorbar(
            x_pos[mask], means[mask],
            yerr=[yerr_lo[mask], yerr_hi[mask]],
            color=style["color"],
            linestyle=style["linestyle"],
            linewidth=style["linewidth"],
            marker=style["marker"],
            markersize=6.5,
            alpha=style["alpha"],
            label=style["label"],
            capsize=3.5,
            elinewidth=1.0,
        )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(CONDITION_ORDER)
    ax.set_xlabel("Signal degradation condition (left = informative, right = sigma removed)")
    ax.set_ylabel("Mean OOS Sharpe-like (20 seeds, 95% CI)")
    ax.set_title("WP6 Signal Informativeness Sweep — monotonic-gap plot")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(loc="lower left", fontsize=8.5, framealpha=0.92)

    caption = ("regime_only and oracle_pure are condition-invariant by design "
               "(do not consume sigma_hat); sigma_only is structurally undefined "
               "in the 'none' condition (sigma_hat = 0).")
    fig.text(0.5, 0.01, caption, ha="center", va="bottom",
             fontsize=8.0, style="italic", color="#333333", wrap=True)

    fig.tight_layout(rect=(0, 0.045, 1, 1))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=180, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(METRICS_CSV)
    summary = aggregate(df)
    summary.to_csv(SUMMARY_CSV, index=False)

    out_png = PLOTS_DIR / "monotonic_gap.png"
    out_pdf = PLOTS_DIR / "monotonic_gap.pdf"
    make_plot(summary, out_png, out_pdf)

    print("=== Mean +/- 95% CI by condition x variant ===")
    disp = summary.copy()
    disp["mean+/-CI95"] = disp.apply(
        lambda r: ("NaN" if pd.isna(r["mean"])
                   else f"{r['mean']:.4f} +/- {(r['ci95_hi'] - r['mean']):.4f}"),
        axis=1,
    )
    print(disp[["condition", "variant", "n", "mean+/-CI95"]].to_string(index=False))
    print()
    print(f"Saved summary CSV: {SUMMARY_CSV}")
    print(f"Saved plot (PNG):  {out_png}")
    print(f"Saved plot (PDF):  {out_pdf}")


if __name__ == "__main__":
    main()
