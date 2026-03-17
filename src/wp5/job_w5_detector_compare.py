"""WP5 — Detector comparison: rv_baseline vs rv_dwell vs hmm (PPO-aware & PPO-blind)."""

from __future__ import annotations

import copy
import math
from pathlib import Path

import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from src.w1_as_baseline import compute_metrics
from src.wp2.synth_regime import (
    assign_regime_hat_dwell,
    assign_regime_hat_hmm,
    run_wp2,
)
from src.wp3.env import MMEnv


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

DETECTOR_TYPES = ["rv_baseline", "rv_dwell", "hmm"]


def _run_wp2_safe(cfg, seed, ctx):
    try:
        return run_wp2(cfg, seed, ctx=ctx)
    except TypeError:
        return run_wp2(cfg, seed)


def _apply_detector(detector: str, df_exog: pd.DataFrame,
                    thresh_LM: float, thresh_MH: float,
                    warmup_end: int) -> pd.DataFrame:
    """Return a copy of df_exog with regime_hat replaced by the chosen detector."""
    df = df_exog.copy()
    sigma_hat = df["sigma_hat"].to_numpy()

    if detector == "rv_baseline":
        pass  # already correct from run_wp2
    elif detector == "rv_dwell":
        df["regime_hat"] = assign_regime_hat_dwell(
            sigma_hat, thresh_LM, thresh_MH, warmup_end, min_dwell=5,
        )
    elif detector == "hmm":
        df["regime_hat"] = assign_regime_hat_hmm(
            sigma_hat, warmup_end,
        )
    else:
        raise ValueError(f"Unknown detector: {detector}")

    return df


# ------------------------------------------------------------------
# Job entry
# ------------------------------------------------------------------

def job_entry(cfg: dict, ctx) -> None:
    out_dir = Path(ctx.run_dir)
    (out_dir / "models").mkdir(exist_ok=True)

    wp5 = cfg["wp5"]
    seeds = wp5["seeds"]
    train_frac = float(wp5.get("train_frac", 0.7))
    n_full = int(cfg["episode"]["n_steps"])
    n_train = math.floor(train_frac * n_full)
    n_test = n_full - n_train
    dt = float(cfg["market"]["dt"])
    warmup = int(cfg["regime"]["warmup_steps"])

    rows = []

    for detector in DETECTOR_TYPES:
        for seed in seeds:
            ctx.logger.info(f"detector={detector} seed={seed}")

            # 1) Generate exog series
            df_exog, thresh_LM, thresh_MH = _run_wp2_safe(cfg, seed, ctx)

            # 2) Replace regime_hat with chosen detector
            df_exog = _apply_detector(
                detector, df_exog, thresh_LM, thresh_MH, warmup,
            )

            # 3) Train-test split
            exog_train = df_exog.iloc[: n_train + 1].reset_index(drop=True)
            exog_test = df_exog.iloc[n_train : n_train + n_test + 1].reset_index(drop=True)

            # 4) Train PPO-aware and PPO-blind
            for stage, use_regime in [("ppo_aware", True), ("ppo_blind", False)]:
                ctx.logger.info(f"  Training {stage}")
                cfg_tr = copy.deepcopy(cfg)
                cfg_tr["wp3"]["use_regime"] = use_regime
                cfg_tr["episode"] = {**cfg_tr["episode"], "n_steps": n_train}
                cfg_tr["as"]["horizon_steps"] = n_train

                env_tr = MMEnv(cfg_tr)
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

                model_dir = out_dir / "models" / detector / f"seed{seed}"
                model_dir.mkdir(parents=True, exist_ok=True)
                model.save(str(model_dir / stage))
                vec_env.close()

                # 5) OOS evaluation
                cfg_ev = copy.deepcopy(cfg)
                cfg_ev["episode"] = {**cfg_ev["episode"], "n_steps": n_test}
                cfg_ev["wp3"]["use_regime"] = use_regime
                cfg_ev["as"]["horizon_steps"] = n_test

                env_ev = MMEnv(cfg_ev)
                obs, _ = env_ev.reset(seed=seed, options={"exog": exog_test})

                eq = np.zeros(n_test + 1)
                iv = np.zeros(n_test + 1, dtype=int)
                fl = np.zeros(n_test, dtype=int)
                eq[0] = env_ev._state.equity
                iv[0] = env_ev._state.inv

                for t in range(n_test):
                    action, _ = model.predict(obs, deterministic=True)
                    obs, _r, _term, _trunc, info = env_ev.step(action)
                    eq[t + 1] = info["equity"]
                    iv[t + 1] = info["inv"]
                    fl[t] = info["fills"]

                m = compute_metrics(eq, iv, fl, dt=dt)
                rows.append({
                    "detector": detector,
                    "seed": seed,
                    "strategy": stage,
                    "sharpe_like": m["sharpe_like"],
                    "final_equity": m["final_equity"],
                })

                ctx.logger.info(
                    f"  {stage}: equity={m['final_equity']:.4f} "
                    f"sharpe={m['sharpe_like']:.4f}"
                )

    # 6) Save results
    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / "metrics_detector_compare.csv", index=False)

    # 7) Summary table: mean sharpe_like by detector x strategy
    summary = (
        df_out.groupby(["detector", "strategy"])["sharpe_like"]
        .mean()
        .reset_index()
        .rename(columns={"sharpe_like": "mean_sharpe_like"})
    )
    print("\n=== Detector Pilot Summary (mean sharpe_like) ===")
    print(summary.to_string(index=False))

    ctx.logger.info("WP5 detector comparison complete.")
