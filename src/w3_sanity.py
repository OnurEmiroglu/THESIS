"""WP3 sanity check: compare naive, AS and random policies through the Gym env."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.w1_as_baseline import as_deltas_ticks, compute_metrics
from src.wp1.sim import ExecParams, MarketParams, MMSimulator
from src.wp2.synth_regime import run_wp2
from src.wp3.env import MMEnv


def _run_episode(env, n, action_fn):
    """Run one episode and return equity, inventory, fills arrays."""
    equity = np.zeros(n + 1)
    inv = np.zeros(n + 1, dtype=int)
    fills = np.zeros(n, dtype=int)

    obs, info = equity[0], None  # placeholder; caller must reset env first
    # re-read from env after caller's reset
    equity[0] = env._state.equity
    inv[0] = env._state.inv

    for t in range(n):
        action = action_fn(t)
        obs, _r, _term, _trunc, info = env.step(action)
        equity[t + 1] = info["equity"]
        inv[t + 1] = info["inv"]
        fills[t] = info["fills"]

    return equity, inv, fills


def run(cfg: dict, ctx=None) -> None:
    """Run sanity check: naive sweep, AS, random — all through MMEnv."""
    if ctx is not None and hasattr(ctx, "run_dir"):
        out_dir = Path(ctx.run_dir)
    else:
        out_dir = Path("results/runs/manual_w3_sanity")
        out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "plots").mkdir(exist_ok=True)
    (out_dir / "config_snapshot.json").write_text(
        json.dumps(cfg, indent=2), encoding="utf-8",
    )

    market = MarketParams(**cfg["market"])
    execp = ExecParams(**cfg["exec"])
    n = int(cfg["episode"]["n_steps"])
    seed = int(cfg["seed"])

    # generate exogenous WP2 series (mid, sigma_hat, regime_hat)
    df_exog, _, _ = run_wp2(cfg, seed)

    env = MMEnv(cfg)
    reset_opts = {"exog": df_exog}
    rows: list[dict] = []

    # ---- Policy 1: Naive (h=1..5, m=0) ----
    for h in cfg["sweep"]["half_spreads_ticks"]:
        env.reset(seed=seed, options=reset_opts)
        eq, iv, fl = _run_episode(
            env, n, action_fn=lambda _t, _h=int(h): np.array([_h - 1, 2]),
        )
        m = compute_metrics(eq, iv, fl, dt=market.dt)
        rows.append({"strategy": f"naive_h{h}", **m})

    # ---- Policy 2: AS (deltas clamped to action grid) ----
    env.reset(seed=seed, options=reset_opts)
    eq = np.zeros(n + 1)
    iv = np.zeros(n + 1, dtype=int)
    fl = np.zeros(n, dtype=int)
    eq[0] = env._state.equity
    iv[0] = env._state.inv

    for t in range(n):
        db, da = as_deltas_ticks(
            env._state.mid, env._state.inv, t, cfg, market, execp,
        )
        h_as = int(np.clip((db + da) // 2, 1, 5))
        m_as = int(np.clip((db - da) // 2, -2, 2))
        _obs, _r, _term, _trunc, info = env.step(
            np.array([h_as - 1, m_as + 2]),
        )
        eq[t + 1] = info["equity"]
        iv[t + 1] = info["inv"]
        fl[t] = info["fills"]

    m = compute_metrics(eq, iv, fl, dt=market.dt)
    rows.append({"strategy": "AS", **m})

    # ---- Policy 3: Random ----
    env.reset(seed=seed, options=reset_opts)
    env.action_space.seed(seed)
    eq = np.zeros(n + 1)
    iv = np.zeros(n + 1, dtype=int)
    fl = np.zeros(n, dtype=int)
    eq[0] = env._state.equity
    iv[0] = env._state.inv

    for t in range(n):
        action = env.action_space.sample()
        _obs, _r, _term, _trunc, info = env.step(action)
        eq[t + 1] = info["equity"]
        iv[t + 1] = info["inv"]
        fl[t] = info["fills"]

    m = compute_metrics(eq, iv, fl, dt=market.dt)
    rows.append({"strategy": "random", **m})

    # ---- Results ----
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "metrics_w3_sanity.csv", index=False)

    # bar plot
    plt.figure(figsize=(10, 5))
    plt.bar(df["strategy"], df["final_equity"])
    plt.xticks(rotation=45, ha="right")
    plt.title("WP3 Sanity: Final Equity Comparison")
    plt.ylabel("Final Equity")
    plt.tight_layout()
    plt.savefig(out_dir / "plots" / "compare_final_equity.png", dpi=150)
    plt.close()

    # ---- WP1 baseline comparison (direct sim, naive h=2) ----
    sim = MMSimulator(market, execp, seed=seed)
    s = sim.reset()
    eq_wp1 = np.zeros(n + 1)
    eq_wp1[0] = s.equity
    for t in range(n):
        s, _ = sim.step(s, delta_bid_ticks=2, delta_ask_ticks=2)
        eq_wp1[t + 1] = s.equity

    wp1_final = float(eq_wp1[-1])
    gym_h2 = float(df.loc[df["strategy"] == "naive_h2", "final_equity"].iloc[0])
    diff = gym_h2 - wp1_final

    log = ctx.logger if ctx else None
    if log:
        log.info(f"WP1 naive h=2 final_equity: {wp1_final:.4f}")
        log.info(f"WP3 gym naive_h2 final_equity: {gym_h2:.4f}")
        log.info(f"Diff (gym - WP1): {diff:.6f}")

    print(
        df[["strategy", "final_equity", "fill_rate",
            "inv_p99", "max_drawdown", "sharpe_like"]],
    )
    print("\nWP1 baseline comparison (naive h=2):")
    print(f"  WP1 direct:  {wp1_final:.4f}")
    print(f"  WP3 gym:     {gym_h2:.4f}")
    print(f"  Diff:        {diff:.6f}")


def job_entry(cfg: dict, ctx) -> None:
    """Entry point: run regime-aware then regime-blind, compare AS equity."""
    out_dir = Path(ctx.run_dir)

    # --- regime-aware ---
    run(cfg, ctx)
    df_aware = pd.read_csv(out_dir / "metrics_w3_sanity.csv")
    (out_dir / "metrics_w3_sanity.csv").rename(
        out_dir / "metrics_w3_sanity_aware.csv",
    )
    p_aware = out_dir / "plots" / "compare_final_equity.png"
    if p_aware.exists():
        p_aware.rename(out_dir / "plots" / "compare_final_equity_aware.png")

    # --- regime-blind ---
    cfg_blind = copy.deepcopy(cfg)
    cfg_blind["wp3"]["use_regime"] = False
    run(cfg_blind, ctx)
    df_blind = pd.read_csv(out_dir / "metrics_w3_sanity.csv")
    (out_dir / "metrics_w3_sanity.csv").rename(
        out_dir / "metrics_w3_sanity_blind.csv",
    )
    p_blind = out_dir / "plots" / "compare_final_equity.png"
    if p_blind.exists():
        p_blind.rename(out_dir / "plots" / "compare_final_equity_blind.png")

    # --- compare ---
    as_aware = float(
        df_aware.loc[df_aware["strategy"] == "AS", "final_equity"].iloc[0],
    )
    as_blind = float(
        df_blind.loc[df_blind["strategy"] == "AS", "final_equity"].iloc[0],
    )
    diff = as_aware - as_blind

    ctx.logger.info(f"regime-aware AS final_equity: {as_aware:.4f}")
    ctx.logger.info(f"regime-blind AS final_equity: {as_blind:.4f}")
    ctx.logger.info(f"diff: {diff:.6f}")
