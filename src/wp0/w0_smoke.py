"""
WP0 Smoke Test
--------------
Projenin temel kurulumunu doğrular: env import, config okuma,
tek adım simülasyon. CI/CD benzeri basit sağlık kontrolü.
"""

from __future__ import annotations

try:
    import numpy as np
except Exception:
    np = None

import matplotlib.pyplot as plt

from src.run_context import RunContext, save_json


def wp0_smoke(ctx: RunContext) -> None:
    n_steps = int(ctx.config.get("n_steps", 200))
    seed = int(ctx.config["seed"])

    if np is None:
        raise RuntimeError("numpy is required for smoke test. Install numpy and rerun.")

    rng = np.random.default_rng(seed)
    rets = rng.normal(loc=0.0, scale=0.01, size=n_steps)

    equity_series = np.cumprod(1.0 + rets)

    for t in range(n_steps):
        ctx.metrics.log({"step": t, "ret": float(rets[t]), "equity": float(equity_series[t])})

    plt.figure()
    plt.plot(equity_series)
    plt.title("WP0 Smoke: Equity Curve")
    plt.xlabel("step")
    plt.ylabel("equity")
    out_path = ctx.plots_dir / "equity_curve.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    summary = {
        "n_steps": n_steps,
        "seed": seed,
        "final_equity": float(equity_series[-1]),
        "mean_ret": float(np.mean(rets)),
        "vol_ret": float(np.std(rets)),
    }
    save_json(ctx.run_dir / "summary.json", summary)

    ctx.logger.info(f"Saved plot: {out_path.as_posix()}")
    ctx.logger.info(f"Final equity: {summary['final_equity']:.6f}")
