"""Full WP6 Signal Informativeness Sweep — 20 seeds × 24 cells × 1M timesteps.

This is the thesis's central empirical experiment. Outputs feed Chapter 5
directly. Do not interpret partial results as final until all 480 cells
have completed. Do not interrupt unless necessary; if interrupted, resume
with `python run.py --config config/w6_sweep_full.json --resume <run_id>`
where <run_id> is the original run dir name.

Uses the same pipeline as the pilot (verified bug-free in commit 3144051).
The `none` condition forces use_sigma=False at the variant level — see
src/wp6/job_w6_sweep_pilot.py docstring for the full design rationale.
By design, regime_only and oracle_pure are condition-invariant: the
regime detector operates on the clean upstream sigma, so the regime
label quality is constant across conditions; the experiment isolates the
marginal value of the explicit regime label given a fixed-quality regime
estimate.

Coarse-layer checkpointing: a model file already on disk causes the cell
to be skipped. In --resume mode, both the model .zip and the
corresponding metrics row must exist; orphan state raises a RuntimeError
(see src/wp6/_resume.py).
"""

from __future__ import annotations

import copy
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from src.wp1.w1_as_baseline import compute_metrics
from src.wp2.synth_regime import run_wp2
from src.wp3.env import MMEnv
from src.wp5_5.signal_degradation import (
    apply_coarsen,
    apply_lag,
    apply_noise,
    compute_clean_cutpoints,
)
from src.wp6._resume import check_cell_consistency, load_completed_set


VARIANT_FLAGS = {
    "sigma_only":  {"use_sigma": True,  "regime_source": "none"},
    "regime_only": {"use_sigma": False, "regime_source": "hat"},
    "combined":    {"use_sigma": True,  "regime_source": "hat"},
    "oracle_pure": {"use_sigma": False, "regime_source": "true"},
    "oracle_full": {"use_sigma": True,  "regime_source": "true"},
}

FULL_BANNER_NOTE = (
    "FULL SWEEP — thesis Chapter 5 input. 20 seeds × 24 cells × 1M timesteps.\n"
    "If interrupted, resume with --resume <run_id>."
)


def _build_degraded(condition, sigma_clean, sigma_std_post,
                    alpha, k_steps, cutpoints, rng):
    if condition == "full":
        return sigma_clean.copy()
    if condition == "noisy":
        return apply_noise(sigma_clean, alpha * sigma_std_post, rng)
    if condition == "lagged":
        return apply_lag(sigma_clean, k_steps)
    if condition == "coarsened":
        return apply_coarsen(sigma_clean, cutpoints)
    if condition == "none":
        # Series is unused: use_sigma_eff is forced False at the variant level
        # for the none condition, so MMEnv zero-fills the sigma slot.
        return sigma_clean.copy()
    raise ValueError(f"Unknown condition: {condition}")


def _eval_model(model, cfg_eval, df_exog_eval, seed):
    env = MMEnv(cfg_eval)
    obs, _ = env.reset(seed=seed, options={"exog": df_exog_eval})
    n = int(cfg_eval["episode"]["n_steps"])
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
    return compute_metrics(equity, inv, fills, dt=cfg_eval["market"]["dt"])


def run(cfg: dict, ctx) -> None:
    sweep = cfg["sweep"]
    conditions = list(sweep["conditions"])
    variants = list(sweep["variants"])
    omit_cells = [tuple(c) for c in sweep.get("omit_cells", [])]
    seeds = list(sweep["seeds"])
    alpha = float(sweep["noisy_alpha"])
    k_steps = int(sweep["lagged_k"])
    n_bins = int(sweep["coarsened_n_bins"])

    # Generic grid validation
    total_cells = len(conditions) * len(variants) - len(omit_cells)
    total_trainings = total_cells * len(seeds)
    assert total_cells > 0, f"total_cells must be > 0, got {total_cells}"
    assert total_trainings > 0, f"total_trainings must be > 0, got {total_trainings}"

    # Full-sweep-specific assertion
    is_real_full = (
        cfg.get("run_tag") == "wp6-sweep-full"
        and cfg.get("job") == "w6_sweep_full"
        and len(seeds) > 3
    )
    if is_real_full:
        assert total_cells == 24, f"Real full sweep must have 24 cells, got {total_cells}"
        assert len(seeds) == 20, f"Real full sweep must have 20 seeds, got {len(seeds)}"
        assert total_trainings == 480, f"Real full sweep must have 480 trainings, got {total_trainings}"

    est_min = total_trainings * 17
    print()
    print("=" * 72)
    print("WP6 Signal Informativeness Sweep — FULL SWEEP")
    print(f"Cells: {total_cells}  Trainings: {total_trainings}  Seeds: {len(seeds)}")
    print(f"Est. wall time @ 17 min/cell: {est_min} min "
          f"(~{est_min/60:.1f} h, ~{est_min/60/24:.1f} days)")
    print("=" * 72)
    print(FULL_BANNER_NOTE)
    print("=" * 72)
    print(flush=True)

    out_dir = Path(ctx.run_dir)
    models_root = out_dir / "models"
    models_root.mkdir(exist_ok=True)

    n_full = int(cfg["episode"]["n_steps"])
    train_frac = float(sweep.get("train_frac", 0.8))
    n_train = math.floor(train_frac * n_full)
    n_test = n_full - n_train
    warmup_end = int(cfg["regime"]["warmup_steps"])
    total_timesteps = int(cfg["wp4"]["total_timesteps"])

    metrics_path = out_dir / "metrics_sweep_full.csv"
    is_resume = getattr(ctx, "resume_run_id", None) is not None
    if is_resume:
        existing_rows, completed_set = load_completed_set(metrics_path)
        ctx.logger.info(
            f"Resume mode: {len(existing_rows)} existing metric rows, "
            f"{len(completed_set)} completed (seed, condition, variant) cells"
        )
    else:
        existing_rows, completed_set = [], set()

    rows = []
    trained = 0
    skipped = 0
    omit_set = set(omit_cells)

    idx_train_end = n_train + 1
    idx_test_start = n_train
    idx_test_end = n_train + n_test + 1

    for seed in seeds:
        ctx.logger.info(f"=== Seed {seed} ===")
        df_exog, _, _ = run_wp2(cfg, seed, ctx=ctx)
        sigma_clean = df_exog["sigma_hat"].to_numpy(dtype=np.float64, copy=True)
        sigma_std_post = float(np.nanstd(sigma_clean[warmup_end:]))
        cutpoints = compute_clean_cutpoints(sigma_clean, warmup_end, n_bins=n_bins)
        deg_rng = np.random.default_rng(seed)

        seed_dir = models_root / f"seed{seed}"
        seed_dir.mkdir(exist_ok=True)

        for condition in conditions:
            sigma_deg = _build_degraded(
                condition, sigma_clean, sigma_std_post,
                alpha, k_steps, cutpoints, deg_rng,
            )
            df_full = df_exog.copy()
            df_full["sigma_hat"] = sigma_deg

            for variant in variants:
                if (condition, variant) in omit_set:
                    continue

                model_path = seed_dir / f"{condition}__{variant}.zip"
                if is_resume:
                    decision = check_cell_consistency(
                        model_exists=model_path.exists(),
                        metric_exists=(seed, condition, variant) in completed_set,
                        seed=seed, condition=condition, variant=variant,
                    )
                    if decision == "skip":
                        msg = f"RESUME-SKIP {condition}/{variant}"
                        print(msg, flush=True)
                        ctx.logger.info(msg)
                        skipped += 1
                        continue
                else:
                    if model_path.exists():
                        msg = f"SKIP {condition}/{variant} (already trained)"
                        print(msg, flush=True)
                        ctx.logger.info(msg)
                        skipped += 1
                        continue

                vflags = VARIANT_FLAGS[variant]
                use_sigma_eff = vflags["use_sigma"] and condition != "none"
                cfg_tr = copy.deepcopy(cfg)
                cfg_tr["wp3"] = {
                    **cfg_tr.get("wp3", {}),
                    "use_sigma": use_sigma_eff,
                    "regime_source": vflags["regime_source"],
                }
                cfg_tr["episode"] = {**cfg_tr["episode"], "n_steps": n_train}

                exog_train = df_full.iloc[:idx_train_end].reset_index(drop=True)
                exog_test = df_full.iloc[idx_test_start:idx_test_end].reset_index(drop=True)

                env_tr = MMEnv(cfg_tr)
                env_tr.reset(seed=seed, options={"exog": exog_train})
                vec_env = DummyVecEnv([lambda _e=Monitor(env_tr): _e])

                wp4 = cfg["wp4"]
                t_train_start = time.time()
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
                    device=cfg.get("wp4", {}).get("device", "cpu"),
                )
                model.learn(total_timesteps=total_timesteps)
                model.save(str(model_path))
                vec_env.close()
                train_seconds = time.time() - t_train_start

                cfg_ev = copy.deepcopy(cfg)
                cfg_ev["wp3"] = {
                    **cfg_ev.get("wp3", {}),
                    "use_sigma": use_sigma_eff,
                    "regime_source": vflags["regime_source"],
                }
                cfg_ev["episode"] = {**cfg_ev["episode"], "n_steps": n_test}

                t_eval_start = time.time()
                m = _eval_model(model, cfg_ev, exog_test, seed)
                eval_seconds = time.time() - t_eval_start

                new_row = {
                    "seed": seed,
                    "condition": condition,
                    "variant": variant,
                    "sharpe_like": m["sharpe_like"],
                    "final_equity": m["final_equity"],
                    "fill_rate": m["fill_rate"],
                    "inv_p99": m["inv_p99"],
                    "train_seconds": train_seconds,
                    "eval_seconds": eval_seconds,
                }
                rows.append(new_row)
                # Persist metric rows incrementally so a kill mid-cell never leaves
                # an orphan model.zip without its metrics row in the next resume.
                pd.DataFrame(existing_rows + rows).to_csv(metrics_path, index=False)
                trained += 1
                ctx.logger.info(
                    f"[{seed}] {condition}/{variant}: trained {train_seconds:.1f}s "
                    f"eval {eval_seconds:.1f}s sharpe={m['sharpe_like']:.4f} "
                    f"inv_p99={m['inv_p99']:.0f}"
                )

    all_rows = existing_rows + rows
    df_metrics = pd.DataFrame(all_rows)
    df_metrics.to_csv(metrics_path, index=False)
    ctx.logger.info(
        f"Wrote {metrics_path.as_posix()} "
        f"(existing={len(existing_rows)}, new={len(rows)}, total={len(all_rows)})"
    )

    md = []
    md.append("# WP6 Signal Informativeness Sweep — Full Summary")
    md.append("")
    md.append(f"Run ID: `{ctx.run_id}`")
    md.append("")
    md.append(f"- trained = {trained}")
    md.append(f"- skipped = {skipped}")
    md.append("")
    if len(df_metrics) > 0:
        ts = df_metrics["train_seconds"]
        md.append("## Cell timing distribution (train_seconds)")
        md.append("")
        md.append(f"- min: {ts.min():.1f}")
        md.append(f"- median: {ts.median():.1f}")
        md.append(f"- max: {ts.max():.1f}")
        md.append(f"- p95: {ts.quantile(0.95):.1f}")
        md.append("")
        md.append("## Per-cell mean across seeds")
        md.append("")
        agg = (df_metrics
               .groupby(["condition", "variant"], sort=False)
               [["sharpe_like", "inv_p99"]]
               .mean()
               .reset_index()
               .sort_values(["condition", "variant"]))
        md.append("| condition | variant | sharpe_like_mean | inv_p99_mean |")
        md.append("|---|---|---:|---:|")
        for _, r in agg.iterrows():
            md.append(
                f"| {r['condition']} | {r['variant']} | "
                f"{r['sharpe_like']:.4f} | {r['inv_p99']:.1f} |"
            )
        md.append("")
    md.append("## Reminder")
    md.append("")
    md.append(FULL_BANNER_NOTE)
    md.append("")
    md.append("## Next step")
    md.append("")
    md.append(
        "Review full_summary.md, then proceed with Chapter 5 analysis "
        "(per-condition × per-variant Sharpe distribution, paired-seed "
        "comparison, sensitivity check at α=0.20 / k=10)."
    )
    summary_path = out_dir / "full_summary.md"
    summary_path.write_text("\n".join(md), encoding="utf-8")
    ctx.logger.info(f"Wrote {summary_path.as_posix()}")
    print(f"Trained: {trained}   Skipped: {skipped}", flush=True)
