"""WP4: PPO training via Stable-Baselines3 on MMEnv."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from src.w1_as_baseline import compute_metrics
from src.wp2.synth_regime import run_wp2
from src.wp3.env import MMEnv


def _eval_model(model, cfg, df_exog, seed, stage, out_dir, ctx):
    """Deterministic rollout → metrics CSV + equity/inventory plots."""
    env = MMEnv(cfg)
    obs, _ = env.reset(seed=seed, options={"exog": df_exog})

    n = int(cfg["episode"]["n_steps"])
    equity = np.zeros(n + 1)
    inv = np.zeros(n + 1, dtype=int)
    fills = np.zeros(n, dtype=int)

    equity[0] = env._state.equity
    inv[0] = env._state.inv

    for t in range(n):
        action, _ = model.predict(obs, deterministic=True)
        obs, _r, _term, _trunc, info = env.step(action)
        equity[t + 1] = info["equity"]
        inv[t + 1] = info["inv"]
        fills[t] = info["fills"]

    m = compute_metrics(equity, inv, fills, dt=cfg["market"]["dt"])

    # CSV
    pd.DataFrame([m]).to_csv(
        out_dir / f"metrics_w4_eval_{stage}.csv", index=False,
    )

    # Plots
    plots_dir = out_dir / "plots"
    ts = np.arange(n + 1)

    plt.figure()
    plt.plot(ts, equity)
    plt.title(f"Equity ({stage})")
    plt.xlabel("step")
    plt.ylabel("equity")
    plt.tight_layout()
    plt.savefig(plots_dir / f"equity_{stage}.png", dpi=150)
    plt.close()

    plt.figure()
    plt.plot(ts, inv)
    plt.title(f"Inventory ({stage})")
    plt.xlabel("step")
    plt.ylabel("inventory")
    plt.tight_layout()
    plt.savefig(plots_dir / f"inventory_{stage}.png", dpi=150)
    plt.close()

    # Log to run metrics CSV
    ctx.metrics.log({
        "stage": stage,
        "total_timesteps": int(cfg["wp4"]["total_timesteps"]),
        "final_equity": m["final_equity"],
        "inv_p99": m["inv_p99"],
        "max_drawdown": m["max_drawdown"],
        "sharpe_like": m["sharpe_like"],
        "fill_rate": m["fill_rate"],
        "turnover": m["turnover"],
    })

    return m


def job_entry(cfg: dict, ctx) -> None:
    """Train PPO (regime-aware + regime-blind) and evaluate both."""
    out_dir = Path(ctx.run_dir)
    models_dir = out_dir / "models"
    models_dir.mkdir(exist_ok=True)
    (out_dir / "plots").mkdir(exist_ok=True)

    seed = int(cfg["seed"])
    wp4 = cfg["wp4"]

    # Generate exogenous WP2 series
    df_exog, _, _ = run_wp2(cfg, seed, ctx=ctx)
    ctx.logger.info(f"WP2 exog generated: {len(df_exog)} rows")

    results = {}

    for stage, use_regime in [("aware", True), ("blind", False)]:
        ctx.logger.info(f"--- Training PPO ({stage}) ---")

        cfg_local = copy.deepcopy(cfg)
        cfg_local["wp3"]["use_regime"] = use_regime

        # Build env → Monitor → DummyVecEnv
        env = MMEnv(cfg_local)
        env.reset(seed=seed, options={"exog": df_exog})
        monitor = Monitor(env)
        vec_env = DummyVecEnv([lambda _m=monitor: _m])

        device = cfg.get("wp4", {}).get("device", "cpu")
        model = PPO(
            "MlpPolicy",
            vec_env,
            seed=seed,
            learning_rate=float(wp4["learning_rate"]),
            n_steps=int(wp4["n_steps"]),
            batch_size=int(wp4["batch_size"]),
            n_epochs=int(wp4["n_epochs"]),
            gamma=float(wp4["gamma"]),
            gae_lambda=float(wp4["gae_lambda"]),
            clip_range=float(wp4["clip_range"]),
            ent_coef=float(wp4["ent_coef"]),
            verbose=1,
            device=device,
        )

        model.learn(total_timesteps=int(wp4["total_timesteps"]))
        model.save(str(models_dir / f"ppo_{stage}"))
        ctx.logger.info(f"Model saved: models/ppo_{stage}.zip")

        vec_env.close()

        # Deterministic evaluation
        m = _eval_model(model, cfg_local, df_exog, seed, stage, out_dir, ctx)
        results[stage] = m
        ctx.logger.info(
            f"Eval {stage}: equity={m['final_equity']:.4f}  "
            f"sharpe={m['sharpe_like']:.4f}  inv_p99={m['inv_p99']:.1f}",
        )

    # Compare bar plot
    stages = list(results.keys())
    equities = [results[s]["final_equity"] for s in stages]

    plt.figure(figsize=(6, 4))
    plt.bar(stages, equities, color=["steelblue", "salmon"])
    plt.title("PPO Final Equity: Aware vs Blind")
    plt.ylabel("Final Equity")
    plt.tight_layout()
    plt.savefig(
        out_dir / "plots" / "compare_final_equity_aware_vs_blind.png", dpi=150,
    )
    plt.close()

    # Summary JSON
    summary = {
        "wp4_hyperparams": wp4,
        "aware": results["aware"],
        "blind": results["blind"],
    }
    (out_dir / "summary_w4.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8",
    )
    ctx.logger.info("summary_w4.json written")
