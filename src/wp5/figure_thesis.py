"""Generate thesis figures from WP5 OOS results."""
# Tez Figür Üretimi (WP5)
# -------------------------
# Tezdeki tüm ana figürleri üretir ve results/plots/thesis/ klasörüne kaydeder:
# - fig1_sharpe_inv.png: Sharpe ve inv_p99 karşılaştırması
# - fig2_paired_seed.png: Seed bazında PPO-aware vs PPO-blind scatter
# - fig3_regime_sharpe.png: Volatilite rejimine göre Sharpe
# - fig4_detector_robustness.png: Dedektör karşılaştırması
# - fig5_action_analysis.png: Eylem dağılımı

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ── paths ────────────────────────────────────────────────────────────────

MAIN_RUN = Path("results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc")
DETECTOR_CSV = Path(
    "results/runs/20260316-223842_seed1_wp5-detector-full_a67e381"
    "/metrics_detector_pilot.csv"
)
OOS_CSV = MAIN_RUN / "metrics_wp5_oos.csv"
REGIME_CSV = MAIN_RUN / "metrics_wp5_oos_by_regime.csv"
CURVES_DIR = MAIN_RUN / "curves"
OUT_DIR = Path("results/plots/thesis")

# ── style ────────────────────────────────────────────────────────────────

COLORS = {
    "AS": "#888888",
    "naive": "#5B9BD5",
    "ppo_blind": "#ED7D31",
    "ppo_aware": "#2E75B6",
}
STRAT_ORDER = ["AS", "naive", "ppo_blind", "ppo_aware"]
STRAT_LABELS = {"AS": "AS", "naive": "Naive", "ppo_blind": "PPO-blind", "ppo_aware": "PPO-aware"}
REGIMES = ["L", "M", "H"]

plt.rcParams.update({
    "font.size": 11,
    "figure.dpi": 150,
    "figure.autolayout": True,
})


# ── helpers ──────────────────────────────────────────────────────────────

def _bar_labels(ax, bars, fmt=".2f"):
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h,
                f"{h:{fmt}}", ha="center", va="bottom", fontsize=9)


def _load_curves() -> pd.DataFrame:
    pattern = re.compile(r"seed(\d+)_(.+)_test\.csv$")
    frames = []
    for csv_path in sorted(CURVES_DIR.glob("*_test.csv")):
        m = pattern.search(csv_path.name)
        if m is None:
            continue
        seed, strategy = int(m.group(1)), m.group(2)
        df = pd.read_csv(csv_path)
        df["seed"] = seed
        df["strategy"] = strategy
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# ── figure 1 ─────────────────────────────────────────────────────────────

def fig1_sharpe_inv(oos: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    labels = [STRAT_LABELS[s] for s in STRAT_ORDER]

    for ax, col, title in [
        (ax1, "sharpe_like", "Mean Sharpe Ratio (OOS, 20 Seeds)"),
        (ax2, "inv_p99", "Inventory Risk — inv_p99 (OOS, 20 Seeds)"),
    ]:
        means, stds = [], []
        for s in STRAT_ORDER:
            sub = oos[oos["strategy"] == s][col]
            means.append(sub.mean())
            stds.append(sub.std())
        x = np.arange(len(STRAT_ORDER))
        bars = ax.bar(x, means, yerr=stds, capsize=4,
                      color=[COLORS[s] for s in STRAT_ORDER])
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylim(bottom=0)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
        _bar_labels(ax, bars)

    ax2.set_ylabel("inv_p99 (lots)")
    fig.text(0.75, -0.02, "Note: Lower inv_p99 is better.",
             ha="center", fontsize=9, style="italic")

    out = OUT_DIR / "fig1_sharpe_inv.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


# ── figure 2 ─────────────────────────────────────────────────────────────

def fig2_paired_seed(oos: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    aware = oos[oos["strategy"] == "ppo_aware"].set_index("seed")
    blind = oos[oos["strategy"] == "ppo_blind"].set_index("seed")
    seeds = sorted(set(aware.index) & set(blind.index))

    for ax, col, title, pval, win_text in [
        (ax1, "sharpe_like",
         "Sharpe Ratio: PPO-aware vs PPO-blind (per seed)", 0.261,
         "Aware > Blind: 11/20 seeds"),
        (ax2, "final_equity",
         "Final Equity: PPO-aware vs PPO-blind (per seed)", 0.023,
         "Aware > Blind: 9/20 seeds"),
    ]:
        x_vals = blind.loc[seeds, col].values
        y_vals = aware.loc[seeds, col].values
        ax.scatter(x_vals, y_vals, c=COLORS["ppo_aware"], edgecolors="k",
                   linewidths=0.5, s=40, zorder=3)
        lo = min(x_vals.min(), y_vals.min()) * 0.95
        hi = max(x_vals.max(), y_vals.max()) * 1.05
        ax.plot([lo, hi], [lo, hi], "--", color="grey", linewidth=1, zorder=1)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box")
        xlabel = "PPO-blind Sharpe" if "Sharpe" in title else "PPO-blind Equity"
        ylabel = "PPO-aware Sharpe" if "Sharpe" in title else "PPO-aware Equity"
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.text(0.05, 0.05, f"p = {pval}", transform=ax.transAxes,
                fontsize=10, verticalalignment="bottom")
        ax.text(0.05, 0.92, win_text, transform=ax.transAxes,
                fontsize=9, verticalalignment="top")
        ax.grid(alpha=0.3)

    out = OUT_DIR / "fig2_paired_seed.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


# ── figure 3 ─────────────────────────────────────────────────────────────

def fig3_regime_sharpe(regime: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(REGIMES))
    n = len(STRAT_ORDER)
    width = 0.18

    for i, s in enumerate(STRAT_ORDER):
        means, stds = [], []
        for r in REGIMES:
            sub = regime[(regime["strategy"] == s) & (regime["regime"] == r)]
            means.append(sub["sharpe_like"].mean())
            stds.append(sub["sharpe_like"].std())
        ax.bar(x + i * width, means, width, yerr=stds, capsize=3,
               color=COLORS[s], label=STRAT_LABELS[s])

    ax.set_xticks(x + width * (n - 1) / 2)
    ax.set_xticklabels(REGIMES)
    ax.set_xlabel("Volatility Regime")
    ax.set_ylabel("Mean Sharpe")
    ax.set_ylim(bottom=0)
    ax.set_title("Sharpe Ratio by Volatility Regime", fontsize=12, fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    fig.text(0.5, -0.02,
             "Regime-wise metrics are grouped by the true synthetic regime "
             "(ex-post attribution).",
             ha="center", fontsize=9, style="italic")

    out = OUT_DIR / "fig3_regime_sharpe.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


# ── figure 4 ─────────────────────────────────────────────────────────────

def fig4_detector_robustness(det: pd.DataFrame):
    detectors = ["rv_baseline", "rv_dwell", "hmm"]
    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.arange(len(detectors))
    for i, d in enumerate(detectors):
        sub = det[det["detector"] == d]
        aware_vals = sub[sub["strategy"] == "ppo_aware"]["sharpe_like"]
        blind_vals = sub[sub["strategy"] == "ppo_blind"]["sharpe_like"]
        aware_mean, aware_std = aware_vals.mean(), aware_vals.std()
        blind_mean, blind_std = blind_vals.mean(), blind_vals.std()

        # vertical line
        ax.plot([i, i], [blind_mean, aware_mean], color="grey", linewidth=1.5,
                zorder=1)
        # aware dot with error bar
        ax.errorbar(i, aware_mean, yerr=aware_std, fmt="o",
                    color=COLORS["ppo_aware"], markersize=10, capsize=4,
                    zorder=3, label="PPO-aware" if i == 0 else "")
        ax.text(i + 0.10, aware_mean, f"{aware_mean:.3f}", va="center", fontsize=9)
        # blind dot with error bar
        ax.errorbar(i, blind_mean, yerr=blind_std, fmt="s",
                    color=COLORS["ppo_blind"], markersize=9, capsize=4,
                    zorder=3, label="PPO-blind" if i == 0 else "")
        ax.text(i + 0.10, blind_mean, f"{blind_mean:.3f}", va="center", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(detectors)
    ax.set_ylim(0.60, 0.80)
    ax.set_ylabel("Mean Sharpe")
    ax.set_title("Detector Robustness: Mean Sharpe by Detector (20 Seeds)",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    annotation = ("rv_baseline: p=0.114 | rv_dwell: p=0.110 | "
                  "HMM: p=0.082 (Sharpe, paired t-test)")
    fig.text(0.5, -0.02, annotation, ha="center", fontsize=9, style="italic")
    fig.text(0.5, -0.06,
             "Y-axis is zoomed (0.60\u20130.80) to highlight detector-level differences.",
             ha="center", fontsize=9, style="italic")

    out = OUT_DIR / "fig4_detector_robustness.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


# ── figure 5 ─────────────────────────────────────────────────────────────

def fig5_action_analysis(curves: pd.DataFrame):
    curves = curves[curves["regime_hat"].isin(REGIMES)].dropna(subset=["h", "m"])

    # per-seed mean h/m by strategy+regime
    seed_agg = (curves.groupby(["seed", "strategy", "regime_hat"])
                .agg(mean_h=("h", "mean"), mean_m=("m", "mean"))
                .reset_index())

    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    fig.suptitle("Action Distribution by Regime: PPO-aware vs PPO-blind",
                 fontsize=12, fontweight="bold")

    strat_colors = {"ppo_aware": "#2E75B6", "ppo_blind": "#ED7D31"}

    configs = [
        (axes[0, 0], "ppo_aware", "mean_h", "PPO-aware: Mean Half-Spread (h)", False),
        (axes[0, 1], "ppo_blind", "mean_h", "PPO-blind: Mean Half-Spread (h)", False),
        (axes[1, 0], "ppo_aware", "mean_m", "PPO-aware: Mean Skew (m)", True),
        (axes[1, 1], "ppo_blind", "mean_m", "PPO-blind: Mean Skew (m)", True),
    ]

    for ax, strat, col, title, show_zero in configs:
        sub = seed_agg[seed_agg["strategy"] == strat]
        x = np.arange(len(REGIMES))
        means, stds = [], []
        for r in REGIMES:
            vals = sub[sub["regime_hat"] == r][col]
            means.append(vals.mean())
            stds.append(vals.std())
        bars = ax.bar(x, means, yerr=stds, capsize=4,
                      color=strat_colors[strat])
        ax.set_xticks(x)
        ax.set_xticklabels(REGIMES)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
        if show_zero:
            ax.axhline(0, color="black", linewidth=0.8, linestyle="-")

    # sync y-axis limits: h subplots 0–3.0, m subplots -0.3–0.3
    for ax in axes[0]:
        ax.set_ylim(0, 3.0)
    for ax in axes[1]:
        ax.set_ylim(-0.3, 0.3)

    out = OUT_DIR / "fig5_action_analysis.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out}")


# ── main ─────────────────────────────────────────────────────────────────

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    oos = pd.read_csv(OOS_CSV)
    oos = oos[oos["split"] == "test"]
    regime = pd.read_csv(REGIME_CSV)
    det = pd.read_csv(DETECTOR_CSV)
    curves = _load_curves()

    print(f"OOS rows: {len(oos)}, Regime rows: {len(regime)}, "
          f"Detector rows: {len(det)}, Curve rows: {len(curves)}")

    fig1_sharpe_inv(oos)
    fig2_paired_seed(oos)
    fig3_regime_sharpe(regime)
    fig4_detector_robustness(det)
    fig5_action_analysis(curves)

    print("\nAll figures saved to", OUT_DIR)


if __name__ == "__main__":
    main()
