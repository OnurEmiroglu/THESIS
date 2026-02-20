from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.wp1.sim import MarketParams, ExecParams, MMSimulator


def compute_metrics(equity: np.ndarray, inv: np.ndarray, fills: np.ndarray, dt: float) -> dict:
    rets = np.diff(equity)
    # “Sharpe” burada kaba: mean/std of per-step PnL increments
    mu = rets.mean() if rets.size else 0.0
    sd = rets.std(ddof=1) if rets.size > 1 else 0.0
    sharpe = (mu / sd) * np.sqrt(1.0 / dt) if sd > 0 else 0.0  # scale ~ sqrt(steps/sec)

    # max drawdown
    peak = np.maximum.accumulate(equity)
    dd = equity - peak
    max_dd = dd.min() if dd.size else 0.0

    return {
        "final_equity": float(equity[-1]),
        "mean_step_pnl": float(mu),
        "std_step_pnl": float(sd),
        "sharpe_like": float(sharpe),
        "max_drawdown": float(max_dd),
        "fill_rate": float(fills.sum() / len(fills)),
        "turnover": int(fills.sum()),
        "inv_mean": float(inv.mean()),
        "inv_p95": float(np.quantile(np.abs(inv), 0.95)),
        "inv_p99": float(np.quantile(np.abs(inv), 0.99)),
    }


def save_plot(path: Path, x: np.ndarray, y: np.ndarray, title: str, xlabel: str, ylabel: str) -> None:
    plt.figure()
    plt.plot(x, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def run(cfg: dict, ctx=None) -> None:
    # output dir (WP0 context varsa onun içine yaz)
    if ctx is not None and hasattr(ctx, "run_dir"):
        out_dir = Path(ctx.run_dir)
    elif ctx is not None and hasattr(ctx, "paths") and "run_dir" in ctx.paths:
        out_dir = Path(ctx.paths["run_dir"])
    else:
        out_dir = Path("results/runs/manual_w1")
        out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "plots").mkdir(exist_ok=True)

    market = MarketParams(**cfg["market"])
    execp = ExecParams(**cfg["exec"])

    # snapshot
    (out_dir / "config_snapshot.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    rows = []
    for h in cfg["sweep"]["half_spreads_ticks"]:
        sim = MMSimulator(market, execp, seed=int(cfg["seed"]))
        s = sim.reset()

        n = int(cfg["episode"]["n_steps"])
        equity = np.zeros(n + 1)
        inv = np.zeros(n + 1, dtype=int)
        fills = np.zeros(n, dtype=int)

        equity[0] = s.equity
        inv[0] = s.inv

        for t in range(n):
            # naive: m=0 => delta_bid=delta_ask=h
            s, info = sim.step(s, delta_bid_ticks=int(h), delta_ask_ticks=int(h))
            equity[t + 1] = s.equity
            inv[t + 1] = s.inv
            fills[t] = int(info["fills"])

        m = compute_metrics(equity, inv, fills, dt=market.dt)
        row = {"half_spread_ticks": int(h), **m}
        rows.append(row)

        # save equity curve + plots per h
        df_curve = pd.DataFrame({
            "t": np.arange(n + 1),
            "equity": equity,
            "inv": inv,
        })
        df_curve.to_csv(out_dir / f"equity_curve_h{h}.csv", index=False)

        save_plot(out_dir / "plots" / f"equity_h{h}.png",
                  x=np.arange(n + 1), y=equity,
                  title=f"Equity Curve (h={h} ticks)", xlabel="step", ylabel="equity")

        save_plot(out_dir / "plots" / f"inventory_h{h}.png",
                  x=np.arange(n + 1), y=inv,
                  title=f"Inventory (h={h} ticks)", xlabel="step", ylabel="inventory")

    df = pd.DataFrame(rows).sort_values("half_spread_ticks")
    df.to_csv(out_dir / "metrics_sweep.csv", index=False)

    # quick summary print (logger yoksa bile gör)
    print(df[["half_spread_ticks", "final_equity", "fill_rate", "inv_p99", "max_drawdown", "sharpe_like"]])


# Eğer WP0 run.py bu modülü job olarak çağıracaksa:
def job_entry(cfg: dict, ctx) -> None:
    run(cfg, ctx)
