"""Eval-only script: seed 1-7 modellerini crash run'dan yükleyip OOS eval çalıştırır."""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from stable_baselines3 import PPO

# Proje kökünü path'e ekle
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.w1_as_baseline import as_deltas_ticks, compute_metrics
from src.wp1.sim import ExecParams, MarketParams
from src.wp2.synth_regime import run_wp2
from src.wp3.env import MMEnv

# ---------- Dizinler ----------
MODEL_RUN = ROOT / "results" / "runs" / "20260327-030624_seed1_wp5-ablation_e1545a5"
OUTPUT_RUN = ROOT / "results" / "runs" / "20260327-171914_seed1_wp5-ablation_e1545a5"
CFG_PATH = ROOT / "config" / "w5_main.json"

SEEDS = list(range(1, 8))  # seed 1-7

VARIANTS = {
    "sigma_only":  {"use_sigma": True,  "regime_source": "none"},
    "regime_only": {"use_sigma": False, "regime_source": "hat"},
    "combined":    {"use_sigma": True,  "regime_source": "hat"},
    "oracle_pure": {"use_sigma": False, "regime_source": "true"},
    "oracle_full": {"use_sigma": True,  "regime_source": "true"},
}


def _compute_regime_metrics(equity, inv, fills, fees, regime_labels, dt):
    n = len(fills)
    results = []
    for regime in sorted(set(regime_labels)):
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


def main():
    with open(CFG_PATH) as f:
        cfg = json.load(f)

    # Override seeds to [1..20] for correct exog generation params
    cfg["wp5"]["seeds"] = list(range(1, 21))

    market = MarketParams(**cfg["market"])
    execp = ExecParams(**cfg["exec"])
    wp5 = cfg["wp5"]
    train_frac = float(wp5["train_frac"])
    naive_h = int(wp5["naive"]["h"])
    naive_m = int(wp5["naive"]["m"])
    n_full = int(cfg["episode"]["n_steps"])
    n_train = math.floor(train_frac * n_full)
    n_test = n_full - n_train

    rows_oos = []
    rows_regime = []

    for seed in SEEDS:
        print(f"=== Eval seed {seed} ===")

        # 1) Exog series (aynı seed -> aynı veri)
        df_exog, _, _ = run_wp2(cfg, seed)

        # 2) Split
        exog_test = df_exog.iloc[n_train: n_train + n_test + 1].reset_index(drop=True)

        # 3) Load pre-trained models
        models = {}
        for name in VARIANTS:
            model_path = MODEL_RUN / "models" / f"seed{seed}" / f"ppo_{name}"
            models[name] = PPO.load(str(model_path), device="cpu")
            print(f"  Loaded {model_path.name}")

        # 4) Build strategies
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

        # 5) Eval loop
        for strat_name, (cfg_ev, model_ev) in strategies.items():
            env_ev = MMEnv(cfg_ev)
            obs, _ = env_ev.reset(seed=seed, options={"exog": exog_test})

            eq = np.zeros(n_test + 1)
            iv = np.zeros(n_test + 1, dtype=int)
            fl = np.zeros(n_test, dtype=int)
            fe = np.zeros(n_test)
            eq[0] = env_ev._state.equity
            iv[0] = env_ev._state.inv

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

                obs, _r, _term, _trunc, info = env_ev.step(action)
                eq[t + 1] = info["equity"]
                iv[t + 1] = info["inv"]
                fl[t] = info["fills"]
                fe[t] = float(info.get("fee_total", 0.0))

            # Metrics
            m = compute_metrics(eq, iv, fl, dt=market.dt)
            total_fees = float(fe.sum())
            n_trades = int(fl.sum())
            fee_per_trade = total_fees / n_trades if n_trades > 0 else 0.0

            row = {
                "seed": seed, "strategy": strat_name, "split": "test",
                **m, "total_fees": total_fees, "fee_per_trade": fee_per_trade,
            }
            rows_oos.append(row)

            # Regime metrics
            if "regime_true" in exog_test.columns:
                regime_labels = list(exog_test["regime_true"].values[:n_test + 1])
            else:
                regime_labels = ["M"] * (n_test + 1)

            rw = _compute_regime_metrics(eq, iv, fl, fe, regime_labels, market.dt)
            for r in rw:
                rows_regime.append({"seed": seed, "strategy": strat_name, **r})

            print(f"  {strat_name}: equity={m['final_equity']:.4f} sharpe={m['sharpe_like']:.4f}")

    # 6) Save seed 1-7 CSVs
    df_oos = pd.DataFrame(rows_oos)
    df_regime = pd.DataFrame(rows_regime)

    oos_path = OUTPUT_RUN / "metrics_wp5_oos_seed1to7.csv"
    regime_path = OUTPUT_RUN / "metrics_wp5_oos_by_regime_seed1to7.csv"
    df_oos.to_csv(oos_path, index=False)
    df_regime.to_csv(regime_path, index=False)
    print(f"\nSaved: {oos_path}  ({len(df_oos)} rows)")
    print(f"Saved: {regime_path}  ({len(df_regime)} rows)")

    # 7) Merge with seed 8-20
    df_oos_8to20 = pd.read_csv(OUTPUT_RUN / "metrics_wp5_oos.csv")
    df_regime_8to20 = pd.read_csv(OUTPUT_RUN / "metrics_wp5_oos_by_regime.csv")

    df_combined = pd.concat([df_oos, df_oos_8to20], ignore_index=True).sort_values(
        ["seed", "strategy"]
    ).reset_index(drop=True)

    df_regime_combined = pd.concat([df_regime, df_regime_8to20], ignore_index=True).sort_values(
        ["seed", "strategy", "regime"]
    ).reset_index(drop=True)

    combined_path = OUTPUT_RUN / "metrics_wp5_oos_combined.csv"
    regime_combined_path = OUTPUT_RUN / "metrics_wp5_oos_by_regime_combined.csv"
    df_combined.to_csv(combined_path, index=False)
    df_regime_combined.to_csv(regime_combined_path, index=False)

    print(f"\n=== Combined ===")
    print(f"metrics_wp5_oos_combined.csv: {len(df_combined)} rows (expected 140)")
    print(f"metrics_wp5_oos_by_regime_combined.csv: {len(df_regime_combined)} rows (expected ~420)")

    # Doğrulama
    seeds_in = sorted(df_combined["seed"].unique())
    strats_in = sorted(df_combined["strategy"].unique())
    print(f"Seeds: {seeds_in}")
    print(f"Strategies: {strats_in}")
    print(f"Seeds x Strategies = {len(seeds_in)} x {len(strats_in)} = {len(seeds_in) * len(strats_in)}")


if __name__ == "__main__":
    main()
