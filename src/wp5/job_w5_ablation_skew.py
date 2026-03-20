"""WP5 — Skew penalty ablation (PPO-aware only, OOS test with action histograms)."""
# Skew Penalty Ablasyon Deneyi (WP5)
# ------------------------------------
# Skew ceza katsayısının (c) etkisini ölçer: R_t = ΔEquity - η*inv² - c*|m|
# c=0 (kontrol grubu) ile c>0 karşılaştırılır.
# ppo_aware'in H rejimindeki bimodal skew dağılımını düzeltir.

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


REGIMES = ["L", "M", "H"]


def _hist_plot(curves_for_c: pd.DataFrame, col: str, title: str, outpath: Path):
    """Plot action distribution per regime for a single c value."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5), sharey=False)
    for j, rg in enumerate(REGIMES):
        ax = axes[j]
        x = curves_for_c[curves_for_c["regime_hat"] == rg][col].dropna().values
        if len(x) == 0:
            ax.set_title(f"{rg} (n=0)")
            continue
        vals, counts = np.unique(x, return_counts=True)
        probs = counts / counts.sum()
        ax.bar(vals, probs)
        ax.set_title(f"{rg} (n={len(x)})")
        ax.set_ylim(0, max(0.30, probs.max() * 1.2))
        ax.grid(True, axis="y", alpha=0.3)
        ax.set_xlabel(col)
    fig.suptitle(title)
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    fig.savefig(outpath, dpi=150)
    plt.close(fig)


# ------------------------------------------------------------------
# Job entry
# ------------------------------------------------------------------

def job_entry(cfg: dict, ctx) -> None:
    out_dir = Path(ctx.run_dir)
    (out_dir / "models").mkdir(exist_ok=True)
    (out_dir / "plots").mkdir(exist_ok=True)
    (out_dir / "curves").mkdir(exist_ok=True)

    wp5 = cfg["wp5"]
    seeds = wp5["seeds"]
    skew_c_values = wp5["skew_c_values"]
    train_frac = float(wp5.get("train_frac", 0.7))
    n_full = int(cfg["episode"]["n_steps"])
    n_train = math.floor(train_frac * n_full)
    n_test = n_full - n_train
    dt = float(cfg["market"]["dt"])

    rows = []

    for c_val in skew_c_values:
        all_curves_for_c = []

        for seed in seeds:
            ctx.logger.info(f"skew_c={c_val} seed={seed}")

            cfg_local = copy.deepcopy(cfg)
            cfg_local["seed"] = seed
            cfg_local["wp3"]["eta"] = float(cfg["wp3"].get("eta", 0.001))
            cfg_local["wp3"]["use_regime"] = True
            cfg_local["wp3"]["skew_penalty_c"] = c_val

            # (A) Exog series
            df_exog, _, _ = _run_wp2_safe(cfg_local, seed, ctx)
            exog_train = df_exog.iloc[: n_train + 1].reset_index(drop=True)
            exog_test = df_exog.iloc[n_train : n_train + n_test + 1].reset_index(drop=True)

            # (B) Train PPO-aware with skew penalty
            cfg_train = copy.deepcopy(cfg_local)
            cfg_train["episode"]["n_steps"] = n_train
            cfg_train["as"]["horizon_steps"] = n_train

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

            seed_dir = out_dir / "models" / f"c{c_val}" / f"seed{seed}"
            seed_dir.mkdir(parents=True, exist_ok=True)
            model.save(str(seed_dir / "ppo_aware"))
            ctx.logger.info(f"Saved: models/c{c_val}/seed{seed}/ppo_aware.zip")
            vec_env.close()

            # (C) OOS test — no skew penalty in eval env (penalty only shapes training)
            cfg_test = copy.deepcopy(cfg_local)
            cfg_test["episode"]["n_steps"] = n_test
            cfg_test["as"]["horizon_steps"] = n_test
            cfg_test["wp3"]["skew_penalty_c"] = 0.0  # eval uses raw PnL

            env_test = MMEnv(cfg_test)
            obs, _ = env_test.reset(seed=seed, options={"exog": exog_test})

            eq = np.zeros(n_test + 1)
            iv = np.zeros(n_test + 1, dtype=int)
            fl = np.zeros(n_test, dtype=int)
            h_arr = np.full(n_test + 1, np.nan)
            m_arr = np.full(n_test + 1, np.nan)
            rh_arr = [""] * (n_test + 1)
            eq[0] = env_test._state.equity
            iv[0] = env_test._state.inv
            rh_arr[0] = str(exog_test["regime_hat"].iloc[0]) if "regime_hat" in exog_test.columns else ""

            for t in range(n_test):
                action, _ = model.predict(obs, deterministic=True)
                h_val = int(action[0]) + 1
                m_val = int(action[1]) - 2
                h_arr[t] = h_val
                m_arr[t] = m_val

                obs, _r, _term, _trunc, info = env_test.step(action)
                eq[t + 1] = info["equity"]
                iv[t + 1] = info["inv"]
                fl[t] = info["fills"]
                idx = min(t + 1, len(exog_test) - 1)
                rh_arr[t + 1] = str(exog_test["regime_hat"].iloc[idx]) if "regime_hat" in exog_test.columns else ""

            # Metrics
            m = compute_metrics(eq, iv, fl, dt=dt)

            # Per-regime step PnL in H
            mask_h = np.array([rh_arr[t] == "H" for t in range(n_test)])
            step_pnl = np.diff(eq)
            mean_step_pnl_H = float(step_pnl[mask_h].mean()) if mask_h.sum() > 0 else 0.0

            row = {
                "skew_c": c_val, "seed": seed, **m,
                "mean_step_pnl_H": mean_step_pnl_H,
            }
            rows.append(row)

            ctx.metrics.log({
                "skew_c": c_val, "seed": seed,
                "final_equity": m["final_equity"],
                "inv_p99": m["inv_p99"],
                "sharpe_like": m["sharpe_like"],
            })
            ctx.logger.info(
                f"skew_c={c_val} seed={seed}: equity={m['final_equity']:.4f} "
                f"sharpe={m['sharpe_like']:.4f} inv_p99={m['inv_p99']:.0f}"
            )

            # Save curve CSV
            curve_df = pd.DataFrame({
                "t": np.arange(n_test + 1),
                "equity": eq, "inv": iv,
                "h": h_arr, "m": m_arr, "regime_hat": rh_arr,
            })
            curve_df.to_csv(
                out_dir / "curves" / f"c{c_val}_seed{seed}_ppo_aware_test.csv",
                index=False,
            )
            all_curves_for_c.append(curve_df)

        # Action histograms for this c value
        combined = pd.concat(all_curves_for_c, ignore_index=True)
        combined = combined[combined["regime_hat"].isin(REGIMES)]
        _hist_plot(
            combined, "h",
            f"h distribution (c={c_val})",
            out_dir / "plots" / f"hist_h_c{c_val}.png",
        )
        _hist_plot(
            combined, "m",
            f"m distribution (c={c_val})",
            out_dir / "plots" / f"hist_m_c{c_val}.png",
        )

    # Save summary CSV
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "metrics_wp5_ablation_skew.csv", index=False)

    # Summary plot: mean equity and inv_p99 vs c
    agg = df.groupby("skew_c").agg(
        mean_equity=("final_equity", "mean"),
        std_equity=("final_equity", "std"),
        mean_inv_p99=("inv_p99", "mean"),
        mean_sharpe=("sharpe_like", "mean"),
        mean_step_pnl_H=("mean_step_pnl_H", "mean"),
    ).reset_index()

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].errorbar(agg["skew_c"], agg["mean_equity"], yerr=agg["std_equity"], marker="o", capsize=4)
    axes[0].set_xlabel("skew_c")
    axes[0].set_ylabel("Final Equity")
    axes[0].set_title("Equity vs skew penalty c")
    axes[0].grid(alpha=0.3)

    axes[1].plot(agg["skew_c"], agg["mean_inv_p99"], marker="s", color="tab:orange")
    axes[1].set_xlabel("skew_c")
    axes[1].set_ylabel("inv_p99")
    axes[1].set_title("inv_p99 vs skew penalty c")
    axes[1].grid(alpha=0.3)

    axes[2].plot(agg["skew_c"], agg["mean_step_pnl_H"], marker="^", color="tab:red")
    axes[2].set_xlabel("skew_c")
    axes[2].set_ylabel("Mean step PnL (H regime)")
    axes[2].set_title("H-regime step PnL vs c")
    axes[2].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "plots" / "skew_ablation_summary.png", dpi=150)
    plt.close(fig)

    ctx.logger.info("WP5 skew ablation complete.")
    print(df[["skew_c", "seed", "final_equity", "sharpe_like", "inv_p99", "mean_step_pnl_H"]])
