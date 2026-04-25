"""WP5.5 runtime benchmark: PPO on CPU vs GPU (2 seeds each).

Purely a device-selection helper for downstream phases; training is short
(default 100k steps) and the resulting policy is discarded.
"""

from __future__ import annotations

import copy
import time
from pathlib import Path

import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from src.wp2.synth_regime import (
    REGIME_LABELS,
    assign_regime_hat,
    calibrate_thresholds,
    compute_rolling_rv,
    generate_mid_series,
    generate_regime_series,
)
from src.wp3.env import MMEnv


def _build_exog_df(cfg: dict, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_steps = int(cfg["episode"]["n_steps"])
    rv_window = int(cfg["regime"]["rv_window"])
    warmup = int(cfg["regime"]["warmup_steps"])

    regime_cfg = copy.deepcopy(cfg.get("regime", {}))
    regime_cfg.setdefault("sigma_mid_ticks_base", float(cfg["market"].get("sigma_mid_ticks", 0.5)))
    regime_cfg.setdefault("sigma_mult", [0.6, 1.0, 1.8])
    cfg_local = {**cfg, "regime": regime_cfg}

    regime_true_int = generate_regime_series(n_steps, seed, cfg=cfg_local, rng=rng)
    mid, _ = generate_mid_series(regime_true_int, cfg_local, rng)
    _, sigma_hat = compute_rolling_rv(mid, rv_window, float(cfg["market"]["tick_size"]))
    thresh_LM, thresh_MH = calibrate_thresholds(sigma_hat, warmup)
    regime_hat = assign_regime_hat(sigma_hat, thresh_LM, thresh_MH, warmup)
    regime_true_str = ["M"] + [REGIME_LABELS[int(r)] for r in regime_true_int]

    return pd.DataFrame({
        "t": np.arange(len(mid)),
        "mid": mid,
        "sigma_hat": sigma_hat,
        "regime_hat": regime_hat,
        "regime_true": regime_true_str,
    })


def _build_env_cfg(cfg: dict, seed: int) -> dict:
    env_cfg = copy.deepcopy(cfg)
    env_cfg["seed"] = int(seed)
    env_block = cfg.get("env", {})
    env_cfg["wp3"] = {
        "eta": float(env_block.get("eta", 1e-3)),
        "use_regime": bool(env_block.get("use_regime", False)),
        "use_sigma": True,
    }
    env_cfg.setdefault("episode", {})
    env_cfg["episode"].setdefault("inv_max_clip", 50)
    return env_cfg


def _train_once(cfg: dict, exog: pd.DataFrame, device: str, seed: int, timesteps: int) -> float:
    env_cfg = _build_env_cfg(cfg, seed)
    env = MMEnv(env_cfg)
    env.reset(seed=seed, options={"exog": exog})
    monitor = Monitor(env)
    vec_env = DummyVecEnv([lambda _m=monitor: _m])

    ppo_cfg = cfg["ppo"]
    model = PPO(
        ppo_cfg.get("policy", "MlpPolicy"),
        vec_env,
        seed=seed,
        learning_rate=float(ppo_cfg["learning_rate"]),
        n_steps=int(ppo_cfg["n_steps"]),
        batch_size=int(ppo_cfg["batch_size"]),
        n_epochs=int(ppo_cfg["n_epochs"]),
        gamma=float(ppo_cfg["gamma"]),
        verbose=0,
        device=device,
    )
    t0 = time.perf_counter()
    model.learn(total_timesteps=int(timesteps))
    wall = time.perf_counter() - t0
    vec_env.close()
    return wall


def _write_decision(
    ctx,
    df: pd.DataFrame,
    cpu_times: pd.Series,
    gpu_times: pd.Series,
) -> tuple[str, str, float]:
    lines = ["# WP5.5 Runtime Benchmark Decision", ""]
    lines.append("## Raw wall times")
    lines.append("")
    for _, r in df.iterrows():
        wt = r["wall_time_seconds"]
        wt_s = "NaN" if pd.isna(wt) else f"{float(wt):.2f}s"
        lines.append(
            f"- device={r['device']}, seed={int(r['seed'])}, "
            f"time={wt_s}, status={r['status']}"
        )
    lines.append("")

    if len(gpu_times) == 0:
        recommendation = "USE_CPU"
        reason = "no_cuda"
        ratio = float("nan")
        cpu_mean = float(cpu_times.mean()) if len(cpu_times) else float("nan")
        lines.append("## Means")
        lines.append("")
        lines.append(f"- CPU mean: {cpu_mean:.2f}s")
        lines.append("- GPU mean: N/A (skipped — CUDA unavailable)")
        lines.append("")
        lines.append("## Ratio: N/A")
        lines.append("")
        lines.append("## Applied rule: GPU runs skipped → USE_CPU")
    else:
        cpu_mean = float(cpu_times.mean())
        gpu_mean = float(gpu_times.mean())
        ratio = gpu_mean / cpu_mean if cpu_mean > 0 else float("nan")
        lines.append("## Means")
        lines.append("")
        lines.append(f"- CPU mean: {cpu_mean:.2f}s")
        lines.append(f"- GPU mean: {gpu_mean:.2f}s")
        lines.append("")
        lines.append(f"## Ratio (GPU/CPU): {ratio:.3f}")
        lines.append("")
        if ratio <= 0.67:
            recommendation = "USE_GPU"
            reason = f"GPU >=1.5x faster (ratio={ratio:.3f})"
            lines.append("## Applied rule: ratio <= 0.67 → USE_GPU")
        elif ratio >= 1.5:
            recommendation = "USE_CPU"
            reason = f"GPU slower than CPU (ratio={ratio:.3f})"
            lines.append("## Applied rule: ratio >= 1.5 → USE_CPU (GPU slower)")
        else:
            recommendation = "USE_CPU"
            reason = f"GPU benefit marginal (ratio={ratio:.3f})"
            lines.append("## Applied rule: 0.67 < ratio < 1.5 → USE_CPU (small/no benefit)")

    lines.append("")
    lines.append(f"## Recommendation: **{recommendation}**  ({reason})")
    lines.append("")

    out = Path(ctx.run_dir) / "runtime_decision.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return recommendation, reason, ratio


def run(cfg: dict, ctx) -> None:
    import torch

    cuda_ok = bool(torch.cuda.is_available())
    if not cuda_ok:
        ctx.logger.warning("CUDA not available — GPU runs will be skipped.")

    bench = cfg["benchmark"]
    devices = list(bench["devices"])
    seeds = list(bench["seeds"])
    timesteps = int(cfg["ppo"].get("total_timesteps", 100_000))

    exog_per_seed = {int(s): _build_exog_df(cfg, int(s)) for s in seeds}

    rows: list[dict] = []
    for device in devices:
        if device == "cuda" and not cuda_ok:
            for s in seeds:
                rows.append({
                    "device": "cuda",
                    "seed": int(s),
                    "wall_time_seconds": float("nan"),
                    "total_timesteps": timesteps,
                    "status": "skipped_no_cuda",
                })
            continue
        for s in seeds:
            s_int = int(s)
            ctx.logger.info(
                f"[benchmark] device={device} seed={s_int} timesteps={timesteps}"
            )
            wall = _train_once(cfg, exog_per_seed[s_int], device, s_int, timesteps)
            ctx.logger.info(f"[benchmark]   wall_time={wall:.2f}s")
            rows.append({
                "device": device,
                "seed": s_int,
                "wall_time_seconds": float(wall),
                "total_timesteps": timesteps,
                "status": "ok",
            })

    df = pd.DataFrame(rows, columns=[
        "device", "seed", "wall_time_seconds", "total_timesteps", "status",
    ])
    csv_path = Path(ctx.run_dir) / "runtime_summary.csv"
    df.to_csv(csv_path, index=False)
    ctx.logger.info(f"Wrote {csv_path.as_posix()}")

    cpu_times = df[(df["device"] == "cpu") & (df["status"] == "ok")]["wall_time_seconds"]
    gpu_times = df[(df["device"] == "cuda") & (df["status"] == "ok")]["wall_time_seconds"]

    recommendation, reason, ratio = _write_decision(ctx, df, cpu_times, gpu_times)
    ctx.logger.info(
        f"Runtime decision: {recommendation} (reason={reason}, ratio={ratio})"
    )
