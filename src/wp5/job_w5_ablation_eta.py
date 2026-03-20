"""WP5.1 — Eta ablation sweep (PPO-aware only, OOS test)."""
# Eta (η) Ablasyon Deneyi (WP5)
# ------------------------------
# Envanter ceza katsayısının (η) farklı değerleri için PPO performansını ölçer.
# η = [0.0001, 0.0005, 0.001, 0.005, 0.01] gibi değerler test edilir.
# Optimal η = 0.001 bu deney ile belirlendi.

from __future__ import annotations

import copy
import math
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


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _run_wp2_safe(cfg, seed, ctx):
    try:
        return run_wp2(cfg, seed, ctx=ctx)
    except TypeError:
        df, thresh_LM, thresh_MH = run_wp2(cfg, seed)
        return df, thresh_LM, thresh_MH


# ------------------------------------------------------------------
# Job entry
# ------------------------------------------------------------------

def job_entry(cfg: dict, ctx) -> None:
    out_dir = Path(ctx.run_dir)
    (out_dir / "models").mkdir(exist_ok=True)
    (out_dir / "plots").mkdir(exist_ok=True)

    wp5 = cfg["wp5"]
    seeds = wp5["seeds"]
    eta_values = wp5["eta_values"]
    train_frac = float(wp5.get("train_frac", 0.7))
    n_full = int(cfg["episode"]["n_steps"])
    n_train = math.floor(train_frac * n_full)
    n_test = n_full - n_train
    dt = float(cfg["market"]["dt"])

    rows = []

    for eta in eta_values:
        for seed in seeds:
            ctx.logger.info(f"eta={eta} seed={seed}")

            cfg_local = copy.deepcopy(cfg)
            cfg_local["seed"] = seed
            cfg_local["wp3"]["eta"] = eta
            cfg_local["wp3"]["use_regime"] = True

            # (A) Exog series
            df_exog, _, _ = _run_wp2_safe(cfg_local, seed, ctx)
            exog_train = df_exog.iloc[: n_train + 1].reset_index(drop=True)
            exog_test = df_exog.iloc[n_train : n_train + n_test + 1].reset_index(drop=True)

            # (B) Train
            cfg_train = copy.deepcopy(cfg_local)
            cfg_train["episode"]["n_steps"] = n_train

            env_tr = MMEnv(cfg_train)
            env_tr.reset(seed=seed, options={"exog": exog_train})
            vec_env = DummyVecEnv([lambda _e=Monitor(env_tr): _e])

            wp4 = cfg["wp4"]
            device = cfg.get("wp4", {}).get("device", "cpu")
            model = PPO(
                "MlpPolicy", vec_env, seed=seed,
                learning_rate=float(wp4["learning_rate"]),
                n_steps=int(wp4["n_steps"]),
                batch_size=int(wp4["batch_size"]),
                n_epochs=int(wp4["n_epochs"]),
                gamma=float(wp4["gamma"]),
                gae_lambda=float(wp4["gae_lambda"]),
                clip_range=float(wp4["clip_range"]),
                ent_coef=float(wp4["ent_coef"]),
                verbose=0,
                device=device,
            )
            model.learn(total_timesteps=int(wp4["total_timesteps"]))

            seed_dir = out_dir / "models" / f"eta{eta}" / f"seed{seed}"
            seed_dir.mkdir(parents=True, exist_ok=True)
            model.save(str(seed_dir / "ppo_aware"))
            ctx.logger.info(f"Saved: models/eta{eta}/seed{seed}/ppo_aware.zip")
            vec_env.close()

            # (C) OOS test
            cfg_test = copy.deepcopy(cfg_local)
            cfg_test["episode"]["n_steps"] = n_test

            env_test = MMEnv(cfg_test)
            obs, _ = env_test.reset(seed=seed, options={"exog": exog_test})

            eq = np.zeros(n_test + 1)
            iv = np.zeros(n_test + 1, dtype=int)
            fl = np.zeros(n_test, dtype=int)
            eq[0] = env_test._state.equity
            iv[0] = env_test._state.inv

            for t in range(n_test):
                action, _ = model.predict(obs, deterministic=True)
                obs, _r, _term, _trunc, info = env_test.step(action)
                eq[t + 1] = info["equity"]
                iv[t + 1] = info["inv"]
                fl[t] = info["fills"]

            m = compute_metrics(eq, iv, fl, dt=dt)
            row = {"eta": eta, "seed": seed, **m}
            rows.append(row)

            ctx.metrics.log({
                "eta": eta, "seed": seed,
                "final_equity": m["final_equity"],
                "inv_p99": m["inv_p99"],
                "sharpe_like": m["sharpe_like"],
                "fill_rate": m["fill_rate"],
            })
            ctx.logger.info(
                f"eta={eta} seed={seed}: equity={m['final_equity']:.4f} "
                f"sharpe={m['sharpe_like']:.4f} fill_rate={m['fill_rate']:.4f}"
            )

    # Save CSV
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "metrics_wp5_ablation_eta.csv", index=False)

    # Plots
    eta_vals_sorted = sorted(df["eta"].unique())
    seed_vals = sorted(df["seed"].unique())

    for metric, ylabel, fname in [
        ("fill_rate", "Fill Rate", "wp5_ablation_eta_fill_rate.png"),
        ("final_equity", "Final Equity", "wp5_ablation_eta_final_equity.png"),
    ]:
        fig, ax = plt.subplots(figsize=(7, 4))
        for s in seed_vals:
            sub = df[df["seed"] == s].sort_values("eta")
            ax.plot(sub["eta"], sub[metric], marker="o", label=f"seed={s}")
        ax.set_xscale("log")
        ax.set_xlabel("eta")
        ax.set_ylabel(ylabel)
        ax.set_title(f"WP5 Eta Ablation: {ylabel}")
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_dir / "plots" / fname, dpi=150)
        plt.close(fig)

    ctx.logger.info("WP5.1 eta ablation complete.")
    print(df[["eta", "seed", "final_equity", "sharpe_like", "inv_p99", "fill_rate"]])
