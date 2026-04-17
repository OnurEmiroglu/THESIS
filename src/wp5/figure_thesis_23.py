"""Generate thesis_23 extension figures from existing WP5 result files."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


ABLATION_CSV = Path(
    "results/runs/20260327-171914_seed1_wp5-ablation_e1545a5"
    "/metrics_wp5_oos_combined.csv"
)
ETA_CSV = Path(
    "results/runs/20260330-155235_seed42_w5-eta-regime_af82a9f"
    "/metrics_wp5_oos.csv"
)
MISSPEC_CSV = Path(
    "results/runs/20260408-160248_seed1_w5-misspec-mild_5d9dc23"
    "/metrics_wp5_oos.csv"
)
OUT_DIR = Path("results/plots/thesis_23")

VARIANT_ORDER = [
    "ppo_sigma_only",
    "ppo_oracle_full",
    "ppo_regime_only",
    "ppo_combined",
    "ppo_oracle_pure",
]
SHORT_LABELS = {
    "ppo_sigma_only": "sigma_only",
    "ppo_oracle_full": "oracle_full",
    "ppo_regime_only": "regime_only",
    "ppo_combined": "combined",
    "ppo_oracle_pure": "oracle_pure",
}
COLORS = {
    "ppo_sigma_only": "#2E75B6",
    "ppo_oracle_full": "#70AD47",
    "ppo_regime_only": "#A5A5A5",
    "ppo_combined": "#ED7D31",
    "ppo_oracle_pure": "#8064A2",
}

plt.rcParams.update({
    "font.size": 10,
    "figure.dpi": 150,
    "figure.autolayout": True,
})


def _load_test(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "split" in df.columns:
        df = df[df["split"] == "test"].copy()
    return df


def _paired_t(df: pd.DataFrame, a: str, b: str, metric: str) -> float:
    aa = df[df["strategy"] == a].set_index("seed")
    bb = df[df["strategy"] == b].set_index("seed")
    seeds = sorted(set(aa.index) & set(bb.index))
    return stats.ttest_rel(aa.loc[seeds, metric], bb.loc[seeds, metric]).pvalue


def _bar_panel(ax, df: pd.DataFrame, metric: str, ylabel: str):
    means = []
    stds = []
    for strategy in VARIANT_ORDER:
        vals = df[df["strategy"] == strategy][metric]
        means.append(vals.mean())
        stds.append(vals.std())
    x = np.arange(len(VARIANT_ORDER))
    bars = ax.bar(
        x,
        means,
        yerr=stds,
        capsize=4,
        color=[COLORS[s] for s in VARIANT_ORDER],
    )
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT_LABELS[s] for s in VARIANT_ORDER], rotation=25, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.3)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h, f"{h:.3f}",
                ha="center", va="bottom", fontsize=8)


def fig6_ablation_summary(ablation: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, metric, ylabel in [
        (axes[0], "sharpe_like", "Sharpe"),
        (axes[1], "final_equity", "Final equity"),
        (axes[2], "inv_p99", "inv_p99"),
    ]:
        _bar_panel(ax, ablation, metric, ylabel)
    out = OUT_DIR / "fig6_ablation_summary.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


def _paired_scatter(ax, df: pd.DataFrame, x_strategy: str, y_strategy: str, p_value: float):
    x_df = df[df["strategy"] == x_strategy].set_index("seed")
    y_df = df[df["strategy"] == y_strategy].set_index("seed")
    seeds = sorted(set(x_df.index) & set(y_df.index))
    x_vals = x_df.loc[seeds, "sharpe_like"].values
    y_vals = y_df.loc[seeds, "sharpe_like"].values
    lo = min(x_vals.min(), y_vals.min()) * 0.96
    hi = max(x_vals.max(), y_vals.max()) * 1.04
    ax.scatter(x_vals, y_vals, s=42, c="#2E75B6", edgecolors="black", linewidths=0.5)
    ax.plot([lo, hi], [lo, hi], "--", color="grey", linewidth=1)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(f"{SHORT_LABELS[x_strategy]} Sharpe")
    ax.set_ylabel(f"{SHORT_LABELS[y_strategy]} Sharpe")
    ax.text(0.05, 0.05, f"p = {p_value:.3f}", transform=ax.transAxes,
            fontsize=10, va="bottom")
    ax.grid(alpha=0.3)


def fig7_oracle_paired_seed(ablation: pd.DataFrame):
    p_sigma_oracle = _paired_t(
        ablation, "ppo_sigma_only", "ppo_oracle_full", "sharpe_like"
    )
    p_oracle_combined = _paired_t(
        ablation, "ppo_oracle_full", "ppo_combined", "sharpe_like"
    )
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))
    _paired_scatter(
        axes[0], ablation, "ppo_sigma_only", "ppo_oracle_full", p_sigma_oracle
    )
    _paired_scatter(
        axes[1], ablation, "ppo_combined", "ppo_oracle_full", p_oracle_combined
    )
    out = OUT_DIR / "fig7_oracle_paired_seed.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


def fig8_eta_regime_summary(eta: pd.DataFrame):
    p_sharpe = _paired_t(eta, "ppo_combined", "ppo_sigma_only", "sharpe_like")
    p_equity = _paired_t(eta, "ppo_combined", "ppo_sigma_only", "final_equity")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
    _bar_panel(axes[0], eta, "sharpe_like", "Sharpe")
    _bar_panel(axes[1], eta, "final_equity", "Final equity")
    axes[0].text(0.03, 0.95, f"combined vs sigma_only: p = {p_sharpe:.4f}",
                 transform=axes[0].transAxes, va="top", fontsize=9)
    axes[1].text(0.03, 0.95, f"combined vs sigma_only: p = {p_equity:.3f}",
                 transform=axes[1].transAxes, va="top", fontsize=9)
    out = OUT_DIR / "fig8_eta_regime_summary.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


def fig9_misspec_summary(misspec: pd.DataFrame):
    p_value = _paired_t(misspec, "ppo_sigma_only", "ppo_oracle_full", "sharpe_like")
    fig, ax = plt.subplots(figsize=(7, 4))
    _bar_panel(ax, misspec, "sharpe_like", "Sharpe")
    ax.text(0.03, 0.95, f"sigma_only vs oracle_full: p = {p_value:.3f}",
            transform=ax.transAxes, va="top", fontsize=9)
    out = OUT_DIR / "fig9_misspec_summary.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ablation = _load_test(ABLATION_CSV)
    eta = _load_test(ETA_CSV)
    misspec = _load_test(MISSPEC_CSV)

    fig6_ablation_summary(ablation)
    fig7_oracle_paired_seed(ablation)
    fig8_eta_regime_summary(eta)
    fig9_misspec_summary(misspec)
    print("\nAll thesis_23 extension figures saved to", OUT_DIR)


if __name__ == "__main__":
    main()
