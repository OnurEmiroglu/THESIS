from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.wp2.synth_regime import run_wp2, REGIME_LABELS


REGIME_COLORS = {"L": "#4183c4", "M": "#e8b730", "H": "#d9534f"}
REGIME_ORDER = ["L", "M", "H"]


def _plot_mid_series(df, plots_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 4))
    mid = df["mid"].values
    t = df["t"].values
    regime = df["regime_true"].values

    ax.plot(t, mid, linewidth=0.4, color="black", zorder=2)

    prev = 0
    for i in range(1, len(regime)):
        if regime[i] != regime[prev] or i == len(regime) - 1:
            end = i if regime[i] != regime[prev] else i + 1
            color = REGIME_COLORS.get(regime[prev], "gray")
            ax.axvspan(t[prev], t[min(end, len(t) - 1)], alpha=0.15, color=color, linewidth=0)
            prev = i

    ax.set_title("Mid-price series with true regime background")
    ax.set_xlabel("step")
    ax.set_ylabel("mid")
    ax.legend(
        [plt.Rectangle((0, 0), 1, 1, fc=REGIME_COLORS[r], alpha=0.3) for r in REGIME_ORDER],
        REGIME_ORDER,
        loc="upper right",
    )
    fig.tight_layout()
    fig.savefig(plots_dir / "mid_series.png", dpi=150)
    plt.close(fig)


def _plot_sigma_hat(df, thresh_LM: float, thresh_MH: float, plots_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 4))
    t = df["t"].values
    sigma_hat = df["sigma_hat"].values

    ax.plot(t, sigma_hat, linewidth=0.5, label="sigma_hat")
    ax.axhline(thresh_LM, color="blue", linestyle="--", linewidth=1, label=f"thresh_LM={thresh_LM:.4f}")
    ax.axhline(thresh_MH, color="red", linestyle="--", linewidth=1, label=f"thresh_MH={thresh_MH:.4f}")
    ax.set_title("Rolling realized volatility (sigma_hat)")
    ax.set_xlabel("step")
    ax.set_ylabel("sigma_hat (ticks)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(plots_dir / "sigma_hat.png", dpi=150)
    plt.close(fig)


def _plot_regime_comparison(df, warmup_end: int, plots_dir: Path) -> None:
    post = df[df["t"] >= warmup_end].copy()
    t = post["t"].values

    regime_map = {"L": 0, "M": 1, "H": 2}
    true_num = np.array([regime_map.get(r, -1) for r in post["regime_true"]])
    hat_num = np.array([regime_map.get(r, -1) for r in post["regime_hat"]])

    fig, axes = plt.subplots(2, 1, figsize=(14, 5), sharex=True)
    axes[0].step(t, true_num, where="post", linewidth=0.6, color="black")
    axes[0].set_yticks([0, 1, 2])
    axes[0].set_yticklabels(["L", "M", "H"])
    axes[0].set_title("True regime")
    axes[0].set_ylabel("regime")

    axes[1].step(t, hat_num, where="post", linewidth=0.6, color="blue")
    axes[1].set_yticks([0, 1, 2])
    axes[1].set_yticklabels(["L", "M", "H"])
    axes[1].set_title("Detected regime")
    axes[1].set_xlabel("step")
    axes[1].set_ylabel("regime")

    fig.tight_layout()
    fig.savefig(plots_dir / "regime_comparison.png", dpi=150)
    plt.close(fig)


def _plot_confusion_matrix(df, warmup_end: int, plots_dir: Path) -> None:
    post = df[df["t"] >= warmup_end].copy()
    true_vals = post["regime_true"].values
    hat_vals = post["regime_hat"].values

    labels = REGIME_ORDER
    n_labels = len(labels)
    cm = np.zeros((n_labels, n_labels), dtype=int)

    label_idx = {l: i for i, l in enumerate(labels)}
    for tr, pr in zip(true_vals, hat_vals):
        if tr in label_idx and pr in label_idx:
            cm[label_idx[tr], label_idx[pr]] += 1

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues")

    ax.set_xticks(range(n_labels))
    ax.set_yticks(range(n_labels))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix (post-warmup)")

    for i in range(n_labels):
        for j in range(n_labels):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=color, fontsize=12)

    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(plots_dir / "confusion_matrix.png", dpi=150)
    plt.close(fig)


def job_entry(cfg: dict, ctx) -> None:
    seed = int(cfg["seed"])
    warmup_end = int(cfg["regime"]["warmup_steps"])

    df, thresh_LM, thresh_MH = run_wp2(cfg, seed)

    # --- Detection accuracy (post-warmup) ---
    post = df[df["t"] >= warmup_end].copy()
    correct = (post["regime_true"] == post["regime_hat"]).sum()
    total = len(post)
    accuracy = correct / total if total > 0 else 0.0
    ctx.logger.info(f"Detection accuracy (post-warmup): {accuracy:.4f} ({correct}/{total})")

    # --- Per-regime counts (based on regime_true, post-warmup) ---
    regime_counts = {}
    for r in REGIME_ORDER:
        cnt = int((post["regime_true"] == r).sum())
        pct = cnt / total if total > 0 else 0.0
        regime_counts[r] = {"count": cnt, "pct": round(pct, 4)}
        ctx.logger.info(f"Regime {r}: {cnt} steps ({pct:.2%})")

    # --- Empirical transition matrix (from regime_true over full series) ---
    true_labels = df["regime_true"].values
    label_idx = {l: i for i, l in enumerate(REGIME_ORDER)}
    trans_counts = np.zeros((3, 3), dtype=int)
    for i in range(1, len(true_labels)):
        fr = true_labels[i - 1]
        to = true_labels[i]
        if fr in label_idx and to in label_idx:
            trans_counts[label_idx[fr], label_idx[to]] += 1

    row_sums = trans_counts.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    trans_probs = trans_counts / row_sums

    ctx.logger.info("Empirical transition matrix:")
    for i, r in enumerate(REGIME_ORDER):
        ctx.logger.info(f"  {r}: {trans_probs[i].round(4).tolist()}")

    # --- Expected duration per regime: 1 / (1 - p_ii) ---
    expected_duration = {}
    for i, r in enumerate(REGIME_ORDER):
        p_ii = trans_probs[i, i]
        dur = 1.0 / (1.0 - p_ii) if p_ii < 1.0 else float("inf")
        expected_duration[r] = round(dur, 2)
        ctx.logger.info(f"Expected duration {r}: {dur:.2f} steps")

    # --- Log metrics ---
    ctx.metrics.log({
        "accuracy": round(accuracy, 4),
        "thresh_LM": round(thresh_LM, 4),
        "thresh_MH": round(thresh_MH, 4),
        **{f"count_{r}": regime_counts[r]["count"] for r in REGIME_ORDER},
        **{f"pct_{r}": regime_counts[r]["pct"] for r in REGIME_ORDER},
        **{f"expected_dur_{r}": expected_duration[r] for r in REGIME_ORDER},
    })

    # --- summary.json ---
    summary = {
        "accuracy": round(accuracy, 4),
        "thresh_LM": round(thresh_LM, 4),
        "thresh_MH": round(thresh_MH, 4),
        "per_regime": regime_counts,
        "expected_duration": expected_duration,
        "empirical_transition_matrix": {
            r: trans_probs[i].round(4).tolist() for i, r in enumerate(REGIME_ORDER)
        },
    }
    summary_path = Path(ctx.run_dir) / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    ctx.logger.info(f"Summary written to {summary_path}")

    # --- Plots ---
    plots_dir = Path(ctx.plots_dir)
    _plot_mid_series(df, plots_dir)
    ctx.logger.info("Plot saved: mid_series.png")

    _plot_sigma_hat(df, thresh_LM, thresh_MH, plots_dir)
    ctx.logger.info("Plot saved: sigma_hat.png")

    _plot_regime_comparison(df, warmup_end, plots_dir)
    ctx.logger.info("Plot saved: regime_comparison.png")

    _plot_confusion_matrix(df, warmup_end, plots_dir)
    ctx.logger.info("Plot saved: confusion_matrix.png")

    ctx.logger.info("WP2 synth regime job completed.")
