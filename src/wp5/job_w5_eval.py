"""WP5 — Out-of-sample evaluation: naive, AS, PPO variants (5 ablation configs)."""
# WP5 Ana Değerlendirme
# ----------------------
# 7 stratejiyi (naive, AS + 5 PPO varyantı) 20 bağımsız seed üzerinde
# out-of-sample değerlendirir. PPO varyantları: sigma_only, regime_only,
# combined, oracle_pure, oracle_full.
# Sonuçlar: metrics_wp5_oos.csv ve metrics_wp5_oos_by_regime.csv

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

from src.w1_as_baseline import as_deltas_ticks, compute_metrics
from src.wp1.sim import ExecParams, MarketParams
from src.wp2.synth_regime import run_wp2
from src.wp3.env import MMEnv


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _run_wp2_safe(cfg, seed, ctx):
    """Call run_wp2, handling old signatures that don't accept ctx."""
    try:
        return run_wp2(cfg, seed, ctx=ctx)
    except TypeError:
        df, thresh_LM, thresh_MH = run_wp2(cfg, seed)
        return df, thresh_LM, thresh_MH


def _compute_regime_metrics(equity, inv, fills, fees, regime_labels, dt):
    """Per-regime performance breakdown."""
    n = len(fills)
    results = []
    for regime in sorted(set(regime_labels)):
        # indices where this regime is active (use first n+1 for equity/inv)
        mask = np.array([regime_labels[t] == regime for t in range(n)])
        steps_count = int(mask.sum())
        if steps_count < 10:
            continue
        step_pnl = np.diff(equity)[mask]
        mean_step_pnl = float(step_pnl.mean()) if len(step_pnl) else 0.0
        std_pnl = float(step_pnl.std(ddof=1)) if len(step_pnl) > 1 else 0.0
        sharpe_like = (mean_step_pnl / std_pnl * np.sqrt(1.0 / dt)) if std_pnl > 0 else 0.0
        fill_rate = float(fills[mask].sum() / steps_count) if steps_count > 0 else 0.0
        inv_vals = np.abs(inv[:-1][mask])
        inv_p99 = float(np.quantile(inv_vals, 0.99)) if len(inv_vals) else 0.0
        results.append({
            "regime": regime,
            "mean_step_pnl": mean_step_pnl,
            "sharpe_like": sharpe_like,
            "fill_rate": fill_rate,
            "inv_p99": inv_p99,
            "steps_count": steps_count,
        })
    return results


# ------------------------------------------------------------------
# Job entry
# ------------------------------------------------------------------

def job_entry(cfg: dict, ctx) -> None:
    out_dir = Path(ctx.run_dir)
    (out_dir / "models").mkdir(exist_ok=True)
    (out_dir / "plots").mkdir(exist_ok=True)
    (out_dir / "curves").mkdir(exist_ok=True)

    market = MarketParams(**cfg["market"])
    execp = ExecParams(**cfg["exec"])
    wp5 = cfg["wp5"]
    seeds = wp5["seeds"]
    train_frac = float(wp5["train_frac"])
    naive_h = int(wp5["naive"]["h"])
    naive_m = int(wp5["naive"]["m"])
    n_full = int(cfg["episode"]["n_steps"])
    n_train = math.floor(train_frac * n_full)
    n_test = n_full - n_train

    VARIANTS = {
        "sigma_only":  {"use_sigma": True,  "regime_source": "none"},
        "regime_only": {"use_sigma": False, "regime_source": "hat"},
        "combined":    {"use_sigma": True,  "regime_source": "hat"},
        "oracle_pure": {"use_sigma": False, "regime_source": "true"},
        "oracle_full": {"use_sigma": True,  "regime_source": "true"},
    }

    rows_oos = []
    rows_regime = []

    for seed in seeds:
        ctx.logger.info(f"=== Seed {seed} ===")

        # 1) Exog series
        df_exog, _, _ = _run_wp2_safe(cfg, seed, ctx)

        # 2) Split — +1 row trick
        exog_train = df_exog.iloc[: n_train + 1].reset_index(drop=True)
        exog_test = df_exog.iloc[n_train : n_train + n_test + 1].reset_index(drop=True)

        # 3) Train PPO variants
        for stage, vcfg in VARIANTS.items():
            ctx.logger.info(f"Training PPO-{stage} seed={seed}")
            cfg_tr = copy.deepcopy(cfg)
            cfg_tr["wp3"]["use_sigma"] = vcfg["use_sigma"]
            cfg_tr["wp3"]["regime_source"] = vcfg["regime_source"]
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

            seed_dir = out_dir / "models" / f"seed{seed}"
            seed_dir.mkdir(parents=True, exist_ok=True)
            model.save(str(seed_dir / f"ppo_{stage}"))
            ctx.logger.info(f"Saved: models/seed{seed}/ppo_{stage}.zip")
            vec_env.close()

        # 4) OOS Evaluation
        models = {
            name: PPO.load(str(out_dir / "models" / f"seed{seed}" / f"ppo_{name}"), device="cpu")
            for name in VARIANTS
        }

        def _base_eval_cfg():
            c = copy.deepcopy(cfg)
            c["episode"] = {**c["episode"], "n_steps": n_test}
            c["wp3"]["use_sigma"] = True
            c["wp3"]["regime_source"] = "hat"
            c["as"]["horizon_steps"] = n_test
            return c

        strategies = {
            "naive": (_base_eval_cfg(), None),
            "AS":    (_base_eval_cfg(), None),
        }
        for vname, vcfg in VARIANTS.items():
            cfg_ev = copy.deepcopy(cfg)
            cfg_ev["episode"] = {**cfg_ev["episode"], "n_steps": n_test}
            cfg_ev["wp3"]["use_sigma"] = vcfg["use_sigma"]
            cfg_ev["wp3"]["regime_source"] = vcfg["regime_source"]
            cfg_ev["as"]["horizon_steps"] = n_test
            strategies[f"ppo_{vname}"] = (cfg_ev, models[vname])

        for strat_name, (cfg_ev, model_ev) in strategies.items():
            env_ev = MMEnv(cfg_ev)
            obs, _ = env_ev.reset(seed=seed, options={"exog": exog_test})

            eq = np.zeros(n_test + 1)
            iv = np.zeros(n_test + 1, dtype=int)
            fl = np.zeros(n_test, dtype=int)
            fe = np.zeros(n_test)
            eq[0] = env_ev._state.equity
            iv[0] = env_ev._state.inv
            h_arr = np.full(n_test + 1, np.nan)
            m_arr = np.full(n_test + 1, np.nan)
            rh_arr = [""] * (n_test + 1)
            rh_arr[0] = str(exog_test["regime_hat"].iloc[0]) if "regime_hat" in exog_test.columns else ""

            for t in range(n_test):
                if strat_name == "naive":
                    action = np.array([naive_h - 1, naive_m + 2])
                elif strat_name == "AS":
                    db, da = as_deltas_ticks(
                        env_ev._state.mid, env_ev._state.inv, t, cfg_ev, market, execp,
                    )
                    h_as = int(np.clip((db + da) // 2, 1, 5))
                    m_as = int(np.clip((db - da) // 2, -2, 2))
                    action = np.array([h_as - 1, m_as + 2])
                else:
                    action, _ = model_ev.predict(obs, deterministic=True)

                h_val = int(action[0]) + 1
                m_val = int(action[1]) - 2
                h_arr[t] = h_val
                m_arr[t] = m_val

                obs, _r, _term, _trunc, info = env_ev.step(action)
                eq[t + 1] = info["equity"]
                iv[t + 1] = info["inv"]
                fl[t] = info["fills"]
                fe[t] = float(info.get("fee_total", 0.0))
                idx = min(t + 1, len(exog_test) - 1)
                rh_arr[t + 1] = str(exog_test["regime_hat"].iloc[idx]) if "regime_hat" in exog_test.columns else ""

            # General metrics
            m = compute_metrics(eq, iv, fl, dt=market.dt)
            total_fees = float(fe.sum())
            n_trades = int(fl.sum())
            fee_per_trade = total_fees / n_trades if n_trades > 0 else 0.0

            row = {
                "seed": seed, "strategy": strat_name, "split": "test",
                **m, "total_fees": total_fees, "fee_per_trade": fee_per_trade,
            }
            rows_oos.append(row)
            ctx.metrics.log({
                "seed": seed, "strategy": strat_name,
                "final_equity": m["final_equity"],
                "inv_p99": m["inv_p99"],
                "sharpe_like": m["sharpe_like"],
            })

            # Save curve
            # regime_true her zaman mevcut (sentetik veri)
            rt_arr = list(exog_test["regime_true"].values[:n_test + 1]) if "regime_true" in exog_test.columns else [""] * (n_test + 1)
            # obs_regime_source: bu strateji hangi kaynağı kullandı
            ev_cfg_this = strategies[strat_name][0]
            obs_regime_source = ev_cfg_this["wp3"].get("regime_source", "hat") if ev_cfg_this is not None else "hat"

            pd.DataFrame({
                "t": np.arange(n_test + 1),
                "equity": eq,
                "inv": iv,
                "h": h_arr,
                "m": m_arr,
                "regime_hat": rh_arr,
                "regime_true": rt_arr,
                "obs_regime_source": obs_regime_source,
            }).to_csv(
                out_dir / "curves" / f"seed{seed}_{strat_name}_test.csv", index=False,
            )

            # Regime-wise metrics
            if "regime_true" in exog_test.columns:
                regime_labels = list(exog_test["regime_true"].values[:n_test + 1])
            else:
                regime_labels = ["M"] * (n_test + 1)

            rw = _compute_regime_metrics(eq, iv, fl, fe, regime_labels, market.dt)
            for r in rw:
                rows_regime.append({"seed": seed, "strategy": strat_name, **r})

            ctx.logger.info(
                f"seed={seed} {strat_name}: equity={m['final_equity']:.4f} "
                f"sharpe={m['sharpe_like']:.4f}"
            )

    # 5) Save CSVs
    df_oos = pd.DataFrame(rows_oos)
    df_oos.to_csv(out_dir / "metrics_wp5_oos.csv", index=False)

    df_regime = pd.DataFrame(rows_regime)
    df_regime.to_csv(out_dir / "metrics_wp5_oos_by_regime.csv", index=False)

    # 6) Plots
    # Plot 1: Final equity by seed (grouped bar)
    strat_names = df_oos["strategy"].unique().tolist()
    seed_vals = sorted(df_oos["seed"].unique().tolist())
    x = np.arange(len(seed_vals))
    width = 0.2
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, s in enumerate(strat_names):
        vals = [
            float(df_oos[(df_oos["seed"] == sd) & (df_oos["strategy"] == s)]["final_equity"].iloc[0])
            for sd in seed_vals
        ]
        ax.bar(x + i * width, vals, width, label=s)
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels([f"seed={s}" for s in seed_vals])
    ax.set_title("WP5 Ablation OOS Final Equity by Seed")
    ax.set_ylabel("Final Equity")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "plots" / "wp5_final_equity_by_seed.png", dpi=150)
    plt.close(fig)

    # Plot 2: Mean +/- std across seeds
    agg = df_oos.groupby("strategy")["final_equity"].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(agg["strategy"], agg["mean"], yerr=agg["std"].fillna(0), capsize=5)
    ax.set_title("WP5 Ablation: Mean +/- Std Across Seeds")
    ax.set_ylabel("Final Equity")
    fig.tight_layout()
    fig.savefig(out_dir / "plots" / "wp5_final_equity_mean_std.png", dpi=150)
    plt.close(fig)

    ctx.logger.info("WP5 complete.")
    print(df_oos[["seed", "strategy", "final_equity", "sharpe_like", "inv_p99", "max_drawdown"]])
