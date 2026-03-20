"""WP5 action analysis: h/m distributions by regime across strategies."""
# Eylem Dağılımı Analizi (WP5)
# ------------------------------
# PPO ajanlarının rejim bazında half-spread (h) ve skew (m) dağılımlarını analiz eder.
# Cross-seed standart sapma kullanır (seed-level aggregation).
# Tez Şekil 3'ü (Action Distribution by Regime) üretir.

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _find_latest_eval_run() -> Path:
    runs = list(Path("results/runs").glob("*wp5-eval*"))
    if not runs:
        raise FileNotFoundError("No wp5-eval run found under results/runs/")
    return max(runs, key=lambda p: p.stat().st_mtime)


def _load_curves(run_dir: Path) -> pd.DataFrame:
    """Load all *_test.csv from curves/, parse strategy & seed from filename."""
    curves_dir = run_dir / "curves"
    pattern = re.compile(r"seed(\d+)_(.+)_test\.csv$")
    frames = []
    for csv_path in sorted(curves_dir.glob("*_test.csv")):
        m = pattern.search(csv_path.name)
        if m is None:
            continue
        seed, strategy = int(m.group(1)), m.group(2)
        df = pd.read_csv(csv_path)
        df["seed"] = seed
        df["strategy"] = strategy
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No *_test.csv files in {curves_dir}")
    return pd.concat(frames, ignore_index=True)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop warmup rows and rows with NaN h/m."""
    df = df[df["regime_hat"].isin(["L", "M", "H"])].copy()
    df = df.dropna(subset=["h", "m"])
    return df


def _seed_level_stats(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["seed", "strategy", "regime_hat"], as_index=False)
    out = g.agg(
        mean_h=("h", "mean"),
        mean_m=("m", "mean"),
        ph5=("h", lambda x: float((x == 5).mean())),
    )
    return out


# ── plots ────────────────────────────────────────────────────────────────

REGIMES = ["L", "M", "H"]
REGIME_COLORS = {"L": "#4CAF50", "M": "#FF9800", "H": "#F44336"}


STRATEGIES = ["AS", "naive", "ppo_aware", "ppo_blind"]


def _grouped_bar(ax, agg: pd.DataFrame, val_col: str, err_col: str, title: str):
    strategies = STRATEGIES
    x = np.arange(len(strategies))
    width = 0.25
    for i, reg in enumerate(REGIMES):
        sub = agg[agg["regime_hat"] == reg]
        # align on strategy order
        vals = [sub.loc[sub["strategy"] == s, val_col].values[0] for s in strategies]
        errs = [sub.loc[sub["strategy"] == s, err_col].values[0] for s in strategies]
        ax.bar(x + i * width, vals, width, yerr=errs, label=reg,
               color=REGIME_COLORS[reg], capsize=3)
    ax.set_xticks(x + width)
    ax.set_xticklabels(strategies)
    ax.set_title(title)
    ax.legend(title="Regime")
    ax.grid(axis="y", alpha=0.3)


def plot_h_by_regime(df: pd.DataFrame, out: Path):
    df_seed = _seed_level_stats(df)
    agg = (df_seed.groupby(["strategy", "regime_hat"])["mean_h"]
             .agg(mean_h="mean", std_h="std").reset_index())
    fig, ax = plt.subplots(figsize=(7, 4))
    _grouped_bar(ax, agg, "mean_h", "std_h", "Mean Half-Spread by Regime")
    ax.set_ylabel("h (ticks)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  saved {out}")


def plot_m_by_regime(df: pd.DataFrame, out: Path):
    df_seed = _seed_level_stats(df)
    agg = (df_seed.groupby(["strategy", "regime_hat"])["mean_m"]
             .agg(mean_m="mean", std_m="std").reset_index())
    fig, ax = plt.subplots(figsize=(7, 4))
    _grouped_bar(ax, agg, "mean_m", "std_m", "Mean Skew by Regime")
    ax.set_ylabel("m (ticks)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  saved {out}")


def plot_ph5_by_regime(df: pd.DataFrame, out: Path):
    df_seed = _seed_level_stats(df)
    agg = (df_seed.groupby(["strategy", "regime_hat"])["ph5"]
             .agg(ph5="mean", std_ph5="std").reset_index())
    x = np.arange(len(STRATEGIES))
    width = 0.25
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, reg in enumerate(REGIMES):
        sub = agg[agg["regime_hat"] == reg]
        vals = [sub.loc[sub["strategy"] == s, "ph5"].values[0] for s in STRATEGIES]
        errs = [sub.loc[sub["strategy"] == s, "std_ph5"].values[0] for s in STRATEGIES]
        ax.bar(x + i * width, vals, width, yerr=errs, label=reg,
               color=REGIME_COLORS[reg], capsize=3)
    ax.set_xticks(x + width)
    ax.set_xticklabels(STRATEGIES)
    ax.set_ylabel("P(h=5)")
    ax.set_title("P(h=5 | Regime) — Undertrading Indicator")
    ax.legend(title="Regime")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  saved {out}")


def print_table(df: pd.DataFrame):
    df_seed = _seed_level_stats(df)
    rows = []
    for (strat, reg), g in df_seed.groupby(["strategy", "regime_hat"]):
        rows.append({
            "strategy": strat,
            "regime": reg,
            "mean_h": g["mean_h"].mean(),
            "std_h": g["mean_h"].std(),
            "mean_m": g["mean_m"].mean(),
            "std_m": g["mean_m"].std(),
            "P(h=5)": g["ph5"].mean(),
            "std_ph5": g["ph5"].std(),
        })
    tbl = pd.DataFrame(rows)
    fmt = {"mean_h": "{:.2f}", "std_h": "{:.2f}",
           "mean_m": "{:.2f}", "std_m": "{:.2f}", "P(h=5)": "{:.3f}",
           "std_ph5": "{:.3f}"}
    print("\n" + tbl.to_string(index=False, formatters={
        k: v.format for k, v in fmt.items()
    }))


# ── main ─────────────────────────────────────────────────────────────────

def main():
    run_dir = _find_latest_eval_run()
    print(f"Run dir: {run_dir}")

    df = _load_curves(run_dir)
    print(f"Loaded {len(df)} rows, strategies: {sorted(df['strategy'].unique())}")

    df = _clean(df)
    print(f"After clean: {len(df)} rows")

    plots_dir = run_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    plot_h_by_regime(df, plots_dir / "action_h_by_regime.png")
    plot_m_by_regime(df, plots_dir / "action_m_by_regime.png")
    plot_ph5_by_regime(df, plots_dir / "ph5_by_regime.png")
    print_table(df)


if __name__ == "__main__":
    main()
