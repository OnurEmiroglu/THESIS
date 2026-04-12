# CODEBASE SNAPSHOT — HFMM Thesis (31 Mart 2026)
# Bu dosya yalnızca referans amaçlıdır. Çalıştırılmaz.
# Proje: KIT Financial Engineering MSc Thesis
# İçerik: Tüm Python kaynak dosyaları + JSON config dosyaları
# Güncelleme: env.py regime-conditional eta eklendi (w5_eta_regime.json)


# ============================================================
# FILE: run.py
# ============================================================
"""
Ana Çalıştırıcı (Dispatcher)
-----------------------------
Config JSON dosyasını okur ve ilgili iş paketini (WP) çalıştırır.
Kullanım: python run.py --config config/<config_dosyasi>.json

İş paketleri (job değeri):
  w0_smoke          → WP0 smoke test
  w1_naive_sweep    → WP1 naive sweep
  w1_as_baseline    → WP1 AS baseline
  w1_compare        → WP1 karşılaştırma
  w2_synth          → WP2 sentetik veri üretimi
  w3_sanity         → WP3 ortam doğrulama
  w4_ppo            → WP4 PPO eğitimi
  w5_eval           → WP5 OOS değerlendirme
  w5_ablation_eta   → WP5 η ablasyon
  w5_ablation_skew  → WP5 skew penalty ablasyon
  w5_detector_compare → WP5 detector robustness
"""

import argparse
import json

from src.run_context import setup_run, finalize_run
from src.w0_smoke import wp0_smoke
from src.w1_naive_sweep import job_entry as w1_naive_sweep
from src.w1_as_baseline import job_entry as w1_as_baseline
from src.w1_compare import job_entry as w1_compare
from src.wp2.job_w2_synth import job_entry as w2_synth
from src.w3_sanity import job_entry as w3_sanity
from src.wp4.job_w4_ppo import job_entry as w4_ppo
from src.wp5.job_w5_eval import job_entry as w5_eval
from src.wp5.job_w5_ablation_eta import job_entry as w5_ablation_eta
from src.wp5.job_w5_ablation_skew import job_entry as w5_ablation_skew
from src.wp5.job_w5_detector_compare import job_entry as w5_detector_compare



def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=str, default="config/base.json")
    return p.parse_args()


def main():
    args = parse_args()
    ctx = setup_run(args.config)

    try:
        # setup_run bazı yapılarda cfg'yi ctx içine koyar; yoksa dosyadan okuruz
        if hasattr(ctx, "cfg") and isinstance(ctx.cfg, dict):
            cfg = ctx.cfg
        else:
            with open(args.config, "r", encoding="utf-8") as f:
                cfg = json.load(f)

        job = cfg.get("job", "w0_smoke")

        if job == "w0_smoke":
            wp0_smoke(ctx)  # WP0
        elif job == "w1_naive_sweep":
            w1_naive_sweep(cfg, ctx)  # WP1
        elif job == "w1_as_baseline":
            w1_as_baseline(cfg, ctx)
        elif job == "w1_compare":
            w1_compare(cfg, ctx)
        elif job == "w2_synth":
            w2_synth(cfg, ctx)
        elif job == "w3_sanity":
            w3_sanity(cfg, ctx)
        elif job == "w4_ppo":
            w4_ppo(cfg, ctx)
        elif job == "w5_eval":
            w5_eval(cfg, ctx)
        elif job == "w5_ablation_eta":
            w5_ablation_eta(cfg, ctx)
        elif job == "w5_ablation_skew":
            w5_ablation_skew(cfg, ctx)
        elif job == "w5_detector_compare":
            w5_detector_compare(cfg, ctx)
        else:
            raise ValueError(f"Unknown job: {job}")

        finalize_run(ctx, "success")

    except Exception as e:
        ctx.logger.exception("Run crashed.")
        finalize_run(ctx, "failed", error=str(e))
        raise


if __name__ == "__main__":
    main()


# ============================================================
# FILE: src/run_context.py
# ============================================================
"""Run lifecycle management: context, seeding, logging, and metrics."""
# Çalıştırma Yaşam Döngüsü (WP0)
# ----------------------------------
# Her deneyi benzersiz run_id ile izler, config snapshot ve git bilgisi kaydeder.
# setup_run() → RunContext oluşturur, finalize_run() → durumu yazar.
# CSVMetricLogger ile metrikler satır satır CSV'ye eklenir.

from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import random

try:
    import numpy as np
except Exception:
    np = None


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def get_git_commit_short() -> str:
    """Return short git commit hash if available, otherwise 'nogit'."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8").strip()
    except Exception:
        return "nogit"


# Benzersiz çalıştırma kimliği üretir: YYYYMMDD-HHMMSS_seed<S>_<tag>_<commit>
# Tekrarlanabilirlik için seed ve git commit hash'i içerir.
def make_run_id(seed: int, run_tag: Optional[str] = None) -> str:
    """
    run_id format: YYYYMMDD-HHMMSS_seed<seed>_<tag>_<commit>
    """
    ts = _utc_timestamp()
    commit = get_git_commit_short()
    tag = (run_tag or "run").replace(" ", "-")
    return f"{ts}_seed{seed}_{tag}_{commit}"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def set_global_seed(seed: int) -> None:
    """
    Best-effort reproducibility across stdlib + numpy.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    if np is not None:
        np.random.seed(seed)


def build_logger(run_dir: Path, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("thesis")
    logger.setLevel(level.upper())
    logger.handlers.clear()
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = logging.FileHandler(run_dir / "run.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


class CSVMetricLogger:
    def __init__(self, path: Path):
        self.path = path
        self._header_written = False

    def log(self, row: Dict[str, Any]) -> None:
        import csv

        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = (not self._header_written) and (not self.path.exists())

        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
                self._header_written = True
            writer.writerow(row)


@dataclass
class RunContext:
    run_id: str
    run_dir: Path
    plots_dir: Path
    config: Dict[str, Any]
    logger: logging.Logger
    metrics: CSVMetricLogger


# Yeni bir deney çalıştırmasını başlatır: dizin oluşturur, seed ayarlar,
# config snapshot ve meta bilgilerini kaydeder, logger ve metrics nesnelerini döner.
def setup_run(config_path: str | Path, results_root: str | Path = "results/runs") -> RunContext:
    config_path = Path(config_path)
    cfg = load_json(config_path)

    if "seed" not in cfg or not isinstance(cfg["seed"], int):
        raise ValueError("Config must include an integer field: 'seed'")

    seed = int(cfg["seed"])
    run_id = make_run_id(seed=seed, run_tag=cfg.get("run_tag"))

    results_root = Path(results_root)
    run_dir = results_root / run_id
    plots_dir = run_dir / "plots"
    run_dir.mkdir(parents=True, exist_ok=False)
    plots_dir.mkdir(parents=True, exist_ok=True)

    set_global_seed(seed)

    logger = build_logger(run_dir)

    cfg = {**cfg, "run_id": run_id}
    save_json(run_dir / "config_snapshot.json", cfg)
    meta = {
        "run_id": run_id,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path.as_posix()),
        "git_commit": get_git_commit_short(),
        "python": sys.version,
        "platform": platform.platform(),
    }
    save_json(run_dir / "meta.json", meta)

    logger.info(f"Run started: {run_id}")
    logger.info(f"Run dir: {run_dir.as_posix()}")

    metrics = CSVMetricLogger(run_dir / "metrics.csv")
    return RunContext(
        run_id=run_id,
        run_dir=run_dir,
        plots_dir=plots_dir,
        config=cfg,
        logger=logger,
        metrics=metrics,
    )

# Çalıştırmayı sonlandırır: status.json dosyasına başarı/hata durumunu yazar.
def finalize_run(ctx: RunContext, status: str = "success", error: str | None = None) -> None:
    payload = {
        "run_id": ctx.run_id,
        "status": status,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }
    save_json(ctx.run_dir / "status.json", payload)

    if status == "success":
        ctx.logger.info("Run finished successfully.")
    else:
        ctx.logger.error(f"Run finished with status={status}. error={error}")





# ============================================================
# FILE: src/w0_smoke.py
# ============================================================
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

from .run_context import RunContext, save_json


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


# ============================================================
# FILE: src/wp1/sim.py
# ============================================================
"""
Piyasa Simülatörü (WP1)
-----------------------
Bu modül, piyasa yapıcı (market maker) simülasyonunun çekirdeğini oluşturur.
Aritmetik Brownian hareketi ile fiyat üretir, Poisson süreci ile emir dolumlarını (fills) simüle eder.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
from typing import Dict, Tuple

import numpy as np


# Piyasa parametrelerini tutan değişmez (frozen) veri sınıfı.
# mid0: başlangıç fiyatı, tick_size: en küçük fiyat adımı,
# dt: zaman adımı (saniye), sigma_mid_ticks: volatilite (tick/√saniye)
@dataclass(frozen=True)
class MarketParams:
    mid0: float
    tick_size: float
    dt: float
    sigma_mid_ticks: float  # mid hareketi: "tick / sqrt(sec)"


# Emir çalıştırma parametrelerini tutan değişmez veri sınıfı.
# A: delta=0 anındaki dolum yoğunluğu, k: yoğunluğun uzaklıkla azalma hızı,
# fee_bps: komisyon (baz puan), latency_steps: gecikme adım sayısı
@dataclass(frozen=True)
class ExecParams:
    A: float               # delta=0 iken intensity (fills/sec)
    k: float               # decay (per tick)
    fee_bps: float         # bps (ör: 0.2 = 0.2 bps)
    latency_steps: int     # quote için kaç adım stale mid


# Simülasyonun her adımdaki anlık durumunu tutan veri sınıfı.
# t: adım sayısı, mid: orta fiyat, cash: nakit, inv: envanter (net pozisyon)
@dataclass
class MMState:
    t: int
    mid: float
    cash: float
    inv: int

    @property
    def equity(self) -> float:
        return self.cash + self.inv * self.mid


# Poisson dolum yoğunluğunu hesaplar: λ(δ) = A * e^(-k*δ)
# δ (delta): kotasyonun mid-price'tan tick cinsinden uzaklığı
# Ne kadar uzak kotasyon verirsen, o kadar az dolum olasılığı.
def lambda_intensity(delta_ticks: float, A: float, k: float) -> float:
    """λ(δ)=A e^{-kδ}, δ tick cinsinden, clamp ile negatifleri engeller."""
    d = max(0.0, float(delta_ticks))
    return A * exp(-k * d)


# Bir zaman adımında en az bir dolumun gerçekleşme olasılığını hesaplar.
# Poisson sürecinde: P(N >= 1) = 1 - exp(-λ * dt)
def fill_prob(lmbda: float, dt: float) -> float:
    """Poisson(λ dt): P(N>=1)=1-exp(-λ dt)."""
    l = max(0.0, float(lmbda))
    return 1.0 - exp(-l * float(dt))


# Ana simülatör sınıfı. Her adımda fiyatı günceller ve dolumları simüle eder.
class MMSimulator:
    def __init__(self, market: MarketParams, execp: ExecParams, seed: int):
        self.m = market
        self.e = execp
        self.rng = np.random.default_rng(seed)
        self._mid_hist = []  # mid history for latency

    # Simülasyonu başlangıç durumuna sıfırlar. Her episode başında çağrılır.
    def reset(self) -> MMState:
        self._mid_hist = [self.m.mid0]
        return MMState(t=0, mid=self.m.mid0, cash=0.0, inv=0)

    # Aritmetik Brownian hareketi ile bir sonraki mid-price değerini üretir.
    # d_ticks = sigma * sqrt(dt) * z, z ~ N(0,1)
    def _evolve_mid(self, mid: float) -> float:
        # Arithmetic BM in ticks: dMid_ticks = sigma * sqrt(dt) * z
        z = self.rng.standard_normal()
        d_ticks = self.m.sigma_mid_ticks * sqrt(self.m.dt) * z
        return mid + d_ticks * self.m.tick_size

    # Simülasyonun bir adımını çalıştırır:
    # 1) Fiyatı güncelle (ABM)
    # 2) Gecikmeli fiyatla kotasyon fiyatlarını hesapla (latency adverse selection)
    # 3) Bid ve ask için Poisson dolum olasılıklarını hesapla
    # 4) Rastgele dolumları gerçekleştir, nakit ve envanteri güncelle
    def step(self, s: MMState, delta_bid_ticks: int, delta_ask_ticks: int) -> Tuple[MMState, Dict]:
        # 1) mid moves
        mid_new = self._evolve_mid(s.mid)
        self._mid_hist.append(mid_new)

        # 2) choose stale mid for quoting
        L = int(self.e.latency_steps)
        if L <= 0 or len(self._mid_hist) <= L:
            mid_for_quote = s.mid
        else:
            mid_for_quote = self._mid_hist[-(L + 1)]  # L steps stale

        ts = self.m.tick_size

        # 3) quote prices (based on stale mid)
        bid_px = mid_for_quote - float(delta_bid_ticks) * ts
        ask_px = mid_for_quote + float(delta_ask_ticks) * ts

        # 4) effective deltas vs CURRENT mid (latency adverse selection shows up here)
        # bid: delta_eff = (current_mid - bid_px)/tick
        # ask: delta_eff = (ask_px - current_mid)/tick
        delta_eff_bid = (mid_new - bid_px) / ts
        delta_eff_ask = (ask_px - mid_new) / ts

        lmbda_bid = lambda_intensity(delta_eff_bid, self.e.A, self.e.k)
        lmbda_ask = lambda_intensity(delta_eff_ask, self.e.A, self.e.k)

        p_bid = fill_prob(lmbda_bid, self.m.dt)
        p_ask = fill_prob(lmbda_ask, self.m.dt)

        fill_bid = (self.rng.random() < p_bid)
        fill_ask = (self.rng.random() < p_ask)

        cash = s.cash
        inv = s.inv
        fee_total = 0.0
        fills = 0

        def fee(notional: float) -> float:
            return abs(notional) * (self.e.fee_bps * 1e-4)

        if fill_bid:
            f = fee(bid_px)
            cash -= (bid_px + f)
            inv += 1
            fee_total += f
            fills += 1

        if fill_ask:
            f = fee(ask_px)
            cash += (ask_px - f)
            inv -= 1
            fee_total += f
            fills += 1

        s2 = MMState(t=s.t + 1, mid=mid_new, cash=cash, inv=inv)

        info = {
            "bid_px": bid_px,
            "ask_px": ask_px,
            "delta_eff_bid": float(delta_eff_bid),
            "delta_eff_ask": float(delta_eff_ask),
            "lambda_bid": lmbda_bid,
            "lambda_ask": lmbda_ask,
            "p_bid": p_bid,
            "p_ask": p_ask,
            "fill_bid": bool(fill_bid),
            "fill_ask": bool(fill_ask),
            "fills": fills,
            "fee_total": fee_total,
            "equity": s2.equity,
            "inv": inv,
            "mid": mid_new
        }
        return s2, info


# ============================================================
# FILE: src/w1_naive_sweep.py
# ============================================================
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.wp1.sim import MarketParams, ExecParams, MMSimulator


def compute_metrics(equity: np.ndarray, inv: np.ndarray, fills: np.ndarray, dt: float) -> dict:
    rets = np.diff(equity)
    # “Sharpe” burada kaba: mean/std of per-step PnL increments
    mu = rets.mean() if rets.size else 0.0
    sd = rets.std(ddof=1) if rets.size > 1 else 0.0
    sharpe = (mu / sd) * np.sqrt(1.0 / dt) if sd > 0 else 0.0  # scale ~ sqrt(steps/sec)

    # max drawdown
    peak = np.maximum.accumulate(equity)
    dd = equity - peak
    max_dd = dd.min() if dd.size else 0.0

    return {
        "final_equity": float(equity[-1]),
        "mean_step_pnl": float(mu),
        "std_step_pnl": float(sd),
        "sharpe_like": float(sharpe),
        "max_drawdown": float(max_dd),
        "fill_rate": float(fills.sum() / len(fills)),
        "turnover": int(fills.sum()),
        "inv_mean": float(inv.mean()),
        "inv_p95": float(np.quantile(np.abs(inv), 0.95)),
        "inv_p99": float(np.quantile(np.abs(inv), 0.99)),
    }


def save_plot(path: Path, x: np.ndarray, y: np.ndarray, title: str, xlabel: str, ylabel: str) -> None:
    plt.figure()
    plt.plot(x, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def run(cfg: dict, ctx=None) -> None:
    # output dir (WP0 context varsa onun içine yaz)
    if ctx is not None and hasattr(ctx, "run_dir"):
        out_dir = Path(ctx.run_dir)
    elif ctx is not None and hasattr(ctx, "paths") and "run_dir" in ctx.paths:
        out_dir = Path(ctx.paths["run_dir"])
    else:
        out_dir = Path("results/runs/manual_w1")
        out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "plots").mkdir(exist_ok=True)

    market = MarketParams(**cfg["market"])
    execp = ExecParams(**cfg["exec"])

    # snapshot
    (out_dir / "config_snapshot.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    rows = []
    for h in cfg["sweep"]["half_spreads_ticks"]:
        sim = MMSimulator(market, execp, seed=int(cfg["seed"]))
        s = sim.reset()

        n = int(cfg["episode"]["n_steps"])
        equity = np.zeros(n + 1)
        inv = np.zeros(n + 1, dtype=int)
        fills = np.zeros(n, dtype=int)

        equity[0] = s.equity
        inv[0] = s.inv

        for t in range(n):
            # naive: m=0 => delta_bid=delta_ask=h
            s, info = sim.step(s, delta_bid_ticks=int(h), delta_ask_ticks=int(h))
            equity[t + 1] = s.equity
            inv[t + 1] = s.inv
            fills[t] = int(info["fills"])

        m = compute_metrics(equity, inv, fills, dt=market.dt)
        row = {"half_spread_ticks": int(h), **m}
        rows.append(row)

        # save equity curve + plots per h
        df_curve = pd.DataFrame({
            "t": np.arange(n + 1),
            "equity": equity,
            "inv": inv,
        })
        df_curve.to_csv(out_dir / f"equity_curve_h{h}.csv", index=False)

        save_plot(out_dir / "plots" / f"equity_h{h}.png",
                  x=np.arange(n + 1), y=equity,
                  title=f"Equity Curve (h={h} ticks)", xlabel="step", ylabel="equity")

        save_plot(out_dir / "plots" / f"inventory_h{h}.png",
                  x=np.arange(n + 1), y=inv,
                  title=f"Inventory (h={h} ticks)", xlabel="step", ylabel="inventory")

    df = pd.DataFrame(rows).sort_values("half_spread_ticks")
    df.to_csv(out_dir / "metrics_sweep.csv", index=False)

    # quick summary print (logger yoksa bile gör)
    print(df[["half_spread_ticks", "final_equity", "fill_rate", "inv_p99", "max_drawdown", "sharpe_like"]])


# Eğer WP0 run.py bu modülü job olarak çağıracaksa:
def job_entry(cfg: dict, ctx) -> None:
    run(cfg, ctx)


# ============================================================
# FILE: src/w1_as_baseline.py
# ============================================================
"""Avellaneda-Stoikov baseline strategy for WP1."""
# Avellaneda-Stoikov Baz Stratejisi (WP1)
# -----------------------------------------
# Analitik piyasa yapıcılığı formülüne dayanan baz strateji.
# Rezervasyon fiyatı (r) ve yarı-spread (d) hesaplayarak kotasyon üretir.
# compute_metrics() fonksiyonu tüm stratejiler tarafından ortak kullanılır.

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.wp1.sim import MarketParams, ExecParams, MMSimulator


def save_plot(path: Path, x: np.ndarray, y: np.ndarray, title: str, xlabel: str, ylabel: str) -> None:
    plt.figure()
    plt.plot(x, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


# Avellaneda-Stoikov kotasyon hesabı: envantere göre asimetrik bid/ask delta üretir.
# r = mid - inv * gamma * sigma² * tau (rezervasyon fiyatı)
# d = 0.5 * gamma * sigma² * tau + (1/gamma) * ln(1 + gamma/k) (yarı-spread)
def as_deltas_ticks(mid: float, inv: int, t: int, cfg: dict, market: MarketParams, execp: ExecParams) -> tuple[int, int]:
    """
    Avellaneda–Stoikov (basit) quote:
    reservation price: r = mid - inv * gamma * sigma^2 * tau
    half-spread:      d = 0.5*gamma*sigma^2*tau + (1/gamma)*log(1 + gamma/k_price)

    Burada k_price = k_ticks / tick_size (çünkü intensity exp(-k_ticks * delta_ticks)).
    """
    ts = market.tick_size
    dt = market.dt

    gamma = float(cfg["as"]["gamma"])
    H = int(cfg["as"]["horizon_steps"])
    tau = max(0.0, (H - t) * dt)  # seconds

    sigma_price = market.sigma_mid_ticks * ts
    sigma2 = sigma_price ** 2  # price^2 / sec

    k_price = execp.k / ts  # 1/price

    r = mid - inv * gamma * sigma2 * tau
    d = 0.5 * gamma * sigma2 * tau + (1.0 / gamma) * np.log(1.0 + gamma / k_price)

    bid = r - d
    ask = r + d

    # delta ticks relative to mid (latency_steps=1 iken simulator içinde mid_for_quote == s.mid)
    delta_bid = int(np.ceil((mid - bid) / ts))
    delta_ask = int(np.ceil((ask - mid) / ts))

    min_d = int(cfg["as"].get("min_delta_ticks", 1))
    max_d = int(cfg["as"].get("max_delta_ticks", 25))
    delta_bid = int(np.clip(delta_bid, min_d, max_d))
    delta_ask = int(np.clip(delta_ask, min_d, max_d))

    return delta_bid, delta_ask


# Performans metriklerini hesaplar: Sharpe oranı, final equity, dolum oranı,
# envanter istatistikleri (ortalama, p95, p99) ve maksimum drawdown.
# Tüm stratejiler (naive, AS, PPO) bu ortak fonksiyonu kullanır.
def compute_metrics(equity: np.ndarray, inv: np.ndarray, fills: np.ndarray, dt: float) -> dict:
    rets = np.diff(equity)
    mu = rets.mean() if rets.size else 0.0
    sd = rets.std(ddof=1) if rets.size > 1 else 0.0
    sharpe = (mu / sd) * np.sqrt(1.0 / dt) if sd > 0 else 0.0

    peak = np.maximum.accumulate(equity)
    dd = equity - peak
    max_dd = dd.min() if dd.size else 0.0

    return {
        "final_equity": float(equity[-1]),
        "fill_rate": float(fills.sum() / len(fills)),
        "turnover": int(fills.sum()),
        "inv_mean": float(inv.mean()),
        "inv_p95": float(np.quantile(np.abs(inv), 0.95)),
        "inv_p99": float(np.quantile(np.abs(inv), 0.99)),
        "max_drawdown": float(max_dd),
        "sharpe_like": float(sharpe),
    }


# AS stratejisini tek episode boyunca çalıştırır.
# Her adımda as_deltas_ticks() ile kotasyon hesaplar, simülatörü ilerletir.
# Equity eğrisi, delta geçmişi ve metrikleri dosyaya yazar.
def run(cfg: dict, ctx=None) -> None:
    if ctx is not None and hasattr(ctx, "run_dir"):
        out_dir = Path(ctx.run_dir)
    elif ctx is not None and hasattr(ctx, "paths") and "run_dir" in ctx.paths:
        out_dir = Path(ctx.paths["run_dir"])
    else:
        out_dir = Path("results/runs/manual_w1_as")
        out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "plots").mkdir(exist_ok=True)

    market = MarketParams(**cfg["market"])
    execp = ExecParams(**cfg["exec"])

    (out_dir / "config_snapshot.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    sim = MMSimulator(market, execp, seed=int(cfg["seed"]))
    s = sim.reset()

    n = int(cfg["episode"]["n_steps"])
    equity = np.zeros(n + 1)
    inv = np.zeros(n + 1, dtype=int)
    fills = np.zeros(n, dtype=int)
    deltab = np.zeros(n, dtype=int)
    deltaa = np.zeros(n, dtype=int)

    equity[0] = s.equity
    inv[0] = s.inv

    for t in range(n):
        db, da = as_deltas_ticks(s.mid, s.inv, t, cfg, market, execp)
        deltab[t] = db
        deltaa[t] = da

        s, info = sim.step(s, delta_bid_ticks=db, delta_ask_ticks=da)
        equity[t + 1] = s.equity
        inv[t + 1] = s.inv
        fills[t] = int(info["fills"])

    df_curve = pd.DataFrame({
        "t": np.arange(n + 1),
        "equity": equity,
        "inv": inv
    })
    df_curve.to_csv(out_dir / "equity_curve_as.csv", index=False)

    df_deltas = pd.DataFrame({
        "t": np.arange(n),
        "delta_bid_ticks": deltab,
        "delta_ask_ticks": deltaa
    })
    df_deltas.to_csv(out_dir / "deltas_as.csv", index=False)

    m = compute_metrics(equity, inv, fills, dt=market.dt)
    pd.DataFrame([m]).to_csv(out_dir / "metrics_as.csv", index=False)

    save_plot(out_dir / "plots" / "equity_as.png", np.arange(n + 1), equity, "Equity Curve (AS)", "step", "equity")
    save_plot(out_dir / "plots" / "inventory_as.png", np.arange(n + 1), inv, "Inventory (AS)", "step", "inventory")

    print(pd.DataFrame([m]))


def job_entry(cfg: dict, ctx) -> None:
    run(cfg, ctx)


# ============================================================
# FILE: src/w1_compare.py
# ============================================================
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.wp1.sim import MarketParams, ExecParams, MMSimulator


def save_plot(path: Path, x: np.ndarray, y: np.ndarray, title: str, xlabel: str, ylabel: str) -> None:
    plt.figure()
    plt.plot(x, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def compute_metrics(equity: np.ndarray, inv: np.ndarray, fills: np.ndarray, dt: float) -> dict:
    rets = np.diff(equity)
    mu = rets.mean() if rets.size else 0.0
    sd = rets.std(ddof=1) if rets.size > 1 else 0.0
    sharpe = (mu / sd) * np.sqrt(1.0 / dt) if sd > 0 else 0.0

    peak = np.maximum.accumulate(equity)
    dd = equity - peak
    max_dd = dd.min() if dd.size else 0.0

    return {
        "final_equity": float(equity[-1]),
        "fill_rate": float(fills.sum() / len(fills)),
        "turnover": int(fills.sum()),
        "inv_mean": float(inv.mean()),
        "inv_p95": float(np.quantile(np.abs(inv), 0.95)),
        "inv_p99": float(np.quantile(np.abs(inv), 0.99)),
        "max_drawdown": float(max_dd),
        "sharpe_like": float(sharpe),
    }


def as_deltas_ticks(mid: float, inv: int, t: int, cfg: dict, market: MarketParams, execp: ExecParams) -> tuple[int, int]:
    ts = market.tick_size
    dt = market.dt

    gamma = float(cfg["as"]["gamma"])
    H = int(cfg["as"]["horizon_steps"])
    tau = max(0.0, (H - t) * dt)  # seconds remaining

    sigma_price = market.sigma_mid_ticks * ts
    sigma2 = sigma_price ** 2

    k_price = execp.k / ts  # 1/price

    r = mid - inv * gamma * sigma2 * tau
    d = 0.5 * gamma * sigma2 * tau + (1.0 / gamma) * np.log(1.0 + gamma / k_price)

    bid = r - d
    ask = r + d

    delta_bid = int(np.ceil((mid - bid) / ts))
    delta_ask = int(np.ceil((ask - mid) / ts))

    min_d = int(cfg["as"].get("min_delta_ticks", 1))
    max_d = int(cfg["as"].get("max_delta_ticks", 25))
    delta_bid = int(np.clip(delta_bid, min_d, max_d))
    delta_ask = int(np.clip(delta_ask, min_d, max_d))

    return delta_bid, delta_ask


def run(cfg: dict, ctx=None) -> None:
    if ctx is not None and hasattr(ctx, "run_dir"):
        out_dir = Path(ctx.run_dir)
    elif ctx is not None and hasattr(ctx, "paths") and "run_dir" in ctx.paths:
        out_dir = Path(ctx.paths["run_dir"])
    else:
        out_dir = Path("results/runs/manual_w1_compare")
        out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "plots").mkdir(exist_ok=True)
    (out_dir / "curves").mkdir(exist_ok=True)

    (out_dir / "config_snapshot.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    market = MarketParams(**cfg["market"])
    execp = ExecParams(**cfg["exec"])
    n = int(cfg["episode"]["n_steps"])
    seed = int(cfg["seed"])

    rows = []

    # ---- Naive sweep ----
    for h in cfg["sweep"]["half_spreads_ticks"]:
        sim = MMSimulator(market, execp, seed=seed)
        s = sim.reset()

        equity = np.zeros(n + 1)
        inv = np.zeros(n + 1, dtype=int)
        fills = np.zeros(n, dtype=int)

        equity[0] = s.equity
        inv[0] = s.inv

        for t in range(n):
            s, info = sim.step(s, delta_bid_ticks=int(h), delta_ask_ticks=int(h))
            equity[t + 1] = s.equity
            inv[t + 1] = s.inv
            fills[t] = int(info["fills"])

        m = compute_metrics(equity, inv, fills, dt=market.dt)
        rows.append({"strategy": f"naive_h{h}", **m})

        pd.DataFrame({"t": np.arange(n + 1), "equity": equity, "inv": inv}).to_csv(
            out_dir / "curves" / f"curve_naive_h{h}.csv", index=False
        )
        save_plot(out_dir / "plots" / f"equity_naive_h{h}.png", np.arange(n + 1), equity,
                  f"Equity (naive h={h})", "step", "equity")
        save_plot(out_dir / "plots" / f"inv_naive_h{h}.png", np.arange(n + 1), inv,
                  f"Inventory (naive h={h})", "step", "inventory")

    df_naive = pd.DataFrame(rows).copy()
    df_naive.to_csv(out_dir / "metrics_naive.csv", index=False)

    # ---- AS baseline ----
    sim = MMSimulator(market, execp, seed=seed)
    s = sim.reset()

    equity = np.zeros(n + 1)
    inv = np.zeros(n + 1, dtype=int)
    fills = np.zeros(n, dtype=int)

    equity[0] = s.equity
    inv[0] = s.inv

    for t in range(n):
        db, da = as_deltas_ticks(s.mid, s.inv, t, cfg, market, execp)
        s, info = sim.step(s, delta_bid_ticks=db, delta_ask_ticks=da)
        equity[t + 1] = s.equity
        inv[t + 1] = s.inv
        fills[t] = int(info["fills"])

    m_as = compute_metrics(equity, inv, fills, dt=market.dt)
    row_as = {"strategy": "AS", **m_as}

    pd.DataFrame({"t": np.arange(n + 1), "equity": equity, "inv": inv}).to_csv(
        out_dir / "curves" / "curve_as.csv", index=False
    )
    save_plot(out_dir / "plots" / "equity_as.png", np.arange(n + 1), equity, "Equity (AS)", "step", "equity")
    save_plot(out_dir / "plots" / "inv_as.png", np.arange(n + 1), inv, "Inventory (AS)", "step", "inventory")

    # ---- Compare table ----
    df_compare = pd.concat([df_naive, pd.DataFrame([row_as])], ignore_index=True)
    df_compare = df_compare.sort_values("final_equity", ascending=False)
    df_compare.to_csv(out_dir / "metrics_compare.csv", index=False)

    # quick bar plot: final equity
    plt.figure()
    plt.bar(df_compare["strategy"], df_compare["final_equity"].to_numpy())
    plt.xticks(rotation=45, ha="right")
    plt.title("Final Equity: naive sweep vs AS")
    plt.tight_layout()
    plt.savefig(out_dir / "plots" / "compare_final_equity.png", dpi=150)
    plt.close()

    print(df_compare[["strategy", "final_equity", "fill_rate", "inv_p99", "max_drawdown", "sharpe_like"]])


def job_entry(cfg: dict, ctx) -> None:
    run(cfg, ctx)


# ============================================================
# FILE: src/w3_sanity.py
# ============================================================
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


# ============================================================
# FILE: src/wp2/synth_regime.py
# ============================================================
"""Synthetic regime generation and detection for WP2."""
# Sentetik Rejim Üretimi ve Tespiti (WP2)
# ----------------------------------------
# 3 durumlu (L/M/H) Markov zinciri ile volatilite rejimi üretir.
# Rolling realized volatility (RV) tabanlı dedektörler ve HMM ile rejim tespiti yapar.
# Look-ahead yok: rejim etiketi yalnızca geçmiş veriye dayanır.

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REGIME_LABELS = {0: "L", 1: "M", 2: "H"}

# Varsayılan geçiş matrisi: yüksek köşegen değerleri "yapışkan" rejimler üretir.
# Satır i, sütun j: P(state_t+1 = j | state_t = i)
DEFAULT_TRANS_MATRIX = np.array([
    [0.9967, 0.0023, 0.0010],
    [0.0042, 0.9917, 0.0041],
    [0.0010, 0.0030, 0.9960],
])


# Markov zinciri ile rejim dizisi üretir. Başlangıç durumu M (state=1).
# Her adımda geçiş matrisinden olasılıksal örnekleme yapılır.
def generate_regime_series(
    n_steps: int,
    seed: int,
    cfg: dict | None = None,
    trans_matrix: np.ndarray | None = None,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    if rng is None:
        rng = np.random.default_rng(seed)
    if trans_matrix is None:
        if cfg is not None and "trans_matrix" in cfg.get("regime", {}):
            trans_matrix = np.array(cfg["regime"]["trans_matrix"])
        else:
            trans_matrix = DEFAULT_TRANS_MATRIX

    regime = np.empty(n_steps, dtype=int)
    state = 1  # start at M
    for t in range(n_steps):
        regime[t] = state
        state = rng.choice(3, p=trans_matrix[state])
    return regime


# Rejim dizisine bağlı olarak sentetik mid-price serisi üretir.
# Her rejimde farklı volatilite çarpanı (sigma_mult) kullanılır.
# Aritmetik Brownian hareket: dMid = sigma_regime * sqrt(dt) * z * tick_size
def generate_mid_series(
    regime_true: np.ndarray,
    cfg: dict,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    mid0 = cfg["market"]["mid0"]
    tick_size = cfg["market"]["tick_size"]
    dt = cfg["market"]["dt"]
    sigma_base = cfg["regime"]["sigma_mid_ticks_base"]
    sigma_mult = cfg["regime"]["sigma_mult"]

    sigma_per_regime = [sigma_base * m for m in sigma_mult]

    n = len(regime_true)
    mid = np.empty(n + 1)
    mid[0] = mid0

    sqrt_dt = np.sqrt(dt)
    z = rng.standard_normal(n)

    for t in range(n):
        state = regime_true[t]
        d_ticks = sigma_per_regime[state] * sqrt_dt * z[t]
        mid[t + 1] = max(tick_size, mid[t] + d_ticks * tick_size)

    ret = np.diff(mid)  # mid[t] - mid[t-1], length n
    return mid, ret


# Kayan pencere ile gerçekleşmiş volatilite (RV) hesaplar.
# İlk `window` adımda NaN döner (yetersiz veri).
# sigma_hat = RV / tick_size (tick cinsinden normalleştirilmiş volatilite)
def compute_rolling_rv(
    mid: np.ndarray,
    window: int,
    tick_size: float,
) -> tuple[np.ndarray, np.ndarray]:
    ret = np.diff(mid, prepend=mid[0])
    n = len(ret)
    rv = np.full(n, np.nan)

    for t in range(window, n):
        rv[t] = np.std(ret[t - window + 1 : t + 1], ddof=1)

    sigma_hat = rv / tick_size
    return rv, sigma_hat


# Warmup dönemindeki sigma_hat dağılımından eşik değerlerini belirler.
# 33. ve 66. persantil: L/M sınırı (thresh_LM) ve M/H sınırı (thresh_MH)
def calibrate_thresholds(
    sigma_hat: np.ndarray,
    warmup_end: int,
) -> tuple[float, float]:
    vals = sigma_hat[:warmup_end]
    vals = vals[~np.isnan(vals)]
    thresh_LM = float(np.percentile(vals, 33))
    thresh_MH = float(np.percentile(vals, 66))
    return thresh_LM, thresh_MH


# Eşik tabanlı rejim tespiti (rv_baseline dedektör).
# Warmup dönemi "warmup" etiketi alır; sonrası sigma_hat'a göre L/M/H.
def assign_regime_hat(
    sigma_hat: np.ndarray,
    thresh_LM: float,
    thresh_MH: float,
    warmup_end: int,
) -> list[str]:
    n = len(sigma_hat)
    regime_hat: list[str] = []
    for t in range(n):
        if t < warmup_end:
            regime_hat.append("warmup")
        elif sigma_hat[t] < thresh_LM:
            regime_hat.append("L")
        elif sigma_hat[t] < thresh_MH:
            regime_hat.append("M")
        else:
            regime_hat.append("H")
    return regime_hat


# Bekleme süresi filtresi: min_dwell adımdan kısa rejim geçişlerini bastırır.
# Kısa geçişleri bir önceki rejim etiketiyle değiştirir (gürültü azaltma).
def apply_dwell_filter(
    regime_labels: list[str],
    min_dwell: int = 5,
) -> list[str]:
    """Replace regime runs shorter than *min_dwell* with the previous regime.

    "warmup" labels pass through unchanged and are not counted as regime runs.
    """
    out = list(regime_labels)
    n = len(out)

    # Identify contiguous runs of non-warmup labels
    i = 0
    while i < n:
        if out[i] == "warmup":
            i += 1
            continue
        # start of a run
        j = i + 1
        while j < n and out[j] == out[i]:
            j += 1
        run_len = j - i
        if run_len < min_dwell:
            # find the previous non-warmup label (fall back to current if none)
            prev = out[i]
            for k in range(i - 1, -1, -1):
                if out[k] != "warmup":
                    prev = out[k]
                    break
            for k in range(i, j):
                out[k] = prev
        i = j
    return out


def assign_regime_hat_dwell(
    sigma_hat: np.ndarray,
    thresh_LM: float,
    thresh_MH: float,
    warmup_end: int,
    min_dwell: int = 5,
) -> list[str]:
    """Threshold-based regime detection followed by a dwell filter."""
    raw = assign_regime_hat(sigma_hat, thresh_LM, thresh_MH, warmup_end)
    return apply_dwell_filter(raw, min_dwell)


# GaussianHMM tabanlı rejim tespiti (hmm dedektör).
# Warmup verisinde eğitilir, sonrası nedensel (causal) tahmin yapar.
# HMM durumları varyansa göre L/M/H'ye eşlenir (düşük varyans → L).
def assign_regime_hat_hmm(
    sigma_hat: np.ndarray,
    warmup_end: int,
    n_states: int = 3,
    seed: int = 0,
) -> list[str]:
    """HMM-based regime detection (GaussianHMM on rolling sigma_hat).

    * Fits on non-NaN sigma_hat values up to *warmup_end* (no look-ahead).
    * Predicts causally: at each step t >= warmup_end the model uses only
      sigma_hat[warmup_end:t+1], dropping any leading NaNs.
    * Maps HMM states to L/M/H by emission variance (lowest → L, highest → H).
    """
    from hmmlearn.hmm import GaussianHMM

    n = len(sigma_hat)
    labels: list[str] = ["warmup"] * n

    # --- Fit on warmup data, dropping NaNs ---
    train = sigma_hat[:warmup_end]
    train = train[~np.isnan(train)].reshape(-1, 1)

    if len(train) < 2:
        return labels

    model = GaussianHMM(
        n_components=n_states,
        covariance_type="diag",
        n_iter=100,
        random_state=seed,
    )
    model.fit(train)

    # --- Map HMM states to L/M/H by ascending variance ---
    variances = model.covars_.flatten()
    order = np.argsort(variances)  # lowest var first
    state_map = {}
    regime_names = ["L", "M", "H"]
    for rank, state_idx in enumerate(order):
        state_map[state_idx] = regime_names[rank]

    # --- Causal prediction: expand window one step at a time ---
    for t in range(warmup_end, n):
        window = sigma_hat[warmup_end : t + 1]
        valid = window[~np.isnan(window)]
        if len(valid) == 0:
            continue
        obs = valid.reshape(-1, 1)
        hidden = model.predict(obs)
        labels[t] = state_map[hidden[-1]]

    return labels


# WP2 ana iş akışı: rejim üretimi → mid-price → RV hesaplama → eşik kalibrasyonu → tespit.
# Sonuçları data/processed/wp2_synth.csv'ye yazar.
def run_wp2(
    cfg: dict,
    seed: int,
    ctx=None,
) -> tuple[pd.DataFrame, float, float]:
    rng = np.random.default_rng(seed)

    n_steps = int(cfg["episode"]["n_steps"])
    rv_window = int(cfg["regime"]["rv_window"])
    warmup_steps = int(cfg["regime"]["warmup_steps"])

    regime_true_int = generate_regime_series(n_steps, seed, cfg=cfg, rng=rng)
    mid, ret = generate_mid_series(regime_true_int, cfg, rng)

    # mid has n_steps+1 elements; compute rv on full mid array
    rv, sigma_hat = compute_rolling_rv(mid, rv_window, cfg["market"]["tick_size"])

    # calibrate on warmup portion (indices 0..warmup_steps-1)
    thresh_LM, thresh_MH = calibrate_thresholds(sigma_hat, warmup_steps)

    # assign detected regime
    regime_hat = assign_regime_hat(sigma_hat, thresh_LM, thresh_MH, warmup_steps)

    # convert true regime to string labels
    regime_true_str = [REGIME_LABELS[r] for r in regime_true_int]

    # Build DataFrame — align to n_steps+1 length (mid array)
    # regime_true_int has n_steps elements, ret has n_steps elements
    # pad regime_true with initial state for t=0
    regime_true_full = ["M"] + regime_true_str  # length n_steps+1
    ret_full = np.concatenate([[0.0], ret])  # length n_steps+1

    df = pd.DataFrame({
        "t": np.arange(len(mid)),
        "mid": mid,
        "ret": ret_full,
        "rv": rv,
        "sigma_hat": sigma_hat,
        "regime_true": regime_true_full,
        "regime_hat": regime_hat,
    })

    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "wp2_synth.csv", index=False)

    if ctx is not None and hasattr(ctx, "run_dir"):
        snapshot_path = Path(ctx.run_dir) / "wp2_synth_snapshot.csv"
        df.to_csv(snapshot_path, index=False)

    return df, thresh_LM, thresh_MH


# ============================================================
# FILE: src/wp2/job_w2_synth.py
# ============================================================
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.wp2.synth_regime import run_wp2, REGIME_LABELS


REGIME_COLORS = {"L": "#4183c4", "M": "#e8b730", "H": "#d9534f"}
REGIME_ORDER = ["L", "M", "H"]


def _plot_mid_series(df, plots_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 4))
    mid = df["mid"].values
    t = df["t"].values
    regime = df["regime_true"].values

    ax.plot(t, mid, linewidth=0.4, color="black", zorder=2)

    prev = 0
    for i in range(1, len(regime)):
        if regime[i] != regime[prev] or i == len(regime) - 1:
            end = i if regime[i] != regime[prev] else i + 1
            color = REGIME_COLORS.get(regime[prev], "gray")
            ax.axvspan(t[prev], t[min(end, len(t) - 1)], alpha=0.15, color=color, linewidth=0)
            prev = i

    ax.set_title("Mid-price series with true regime background")
    ax.set_xlabel("step")
    ax.set_ylabel("mid")
    ax.legend(
        [plt.Rectangle((0, 0), 1, 1, fc=REGIME_COLORS[r], alpha=0.3) for r in REGIME_ORDER],
        REGIME_ORDER,
        loc="upper right",
    )
    fig.tight_layout()
    fig.savefig(plots_dir / "mid_series.png", dpi=150)
    plt.close(fig)


def _plot_sigma_hat(df, thresh_LM: float, thresh_MH: float, plots_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 4))
    t = df["t"].values
    sigma_hat = df["sigma_hat"].values

    ax.plot(t, sigma_hat, linewidth=0.5, label="sigma_hat")
    ax.axhline(thresh_LM, color="blue", linestyle="--", linewidth=1, label=f"thresh_LM={thresh_LM:.4f}")
    ax.axhline(thresh_MH, color="red", linestyle="--", linewidth=1, label=f"thresh_MH={thresh_MH:.4f}")
    ax.set_title("Rolling realized volatility (sigma_hat)")
    ax.set_xlabel("step")
    ax.set_ylabel("sigma_hat (ticks)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(plots_dir / "sigma_hat.png", dpi=150)
    plt.close(fig)


def _plot_regime_comparison(df, warmup_end: int, plots_dir: Path) -> None:
    post = df[df["t"] >= warmup_end].copy()
    t = post["t"].values

    regime_map = {"L": 0, "M": 1, "H": 2}
    true_num = np.array([regime_map.get(r, -1) for r in post["regime_true"]])
    hat_num = np.array([regime_map.get(r, -1) for r in post["regime_hat"]])

    fig, axes = plt.subplots(2, 1, figsize=(14, 5), sharex=True)
    axes[0].step(t, true_num, where="post", linewidth=0.6, color="black")
    axes[0].set_yticks([0, 1, 2])
    axes[0].set_yticklabels(["L", "M", "H"])
    axes[0].set_title("True regime")
    axes[0].set_ylabel("regime")

    axes[1].step(t, hat_num, where="post", linewidth=0.6, color="blue")
    axes[1].set_yticks([0, 1, 2])
    axes[1].set_yticklabels(["L", "M", "H"])
    axes[1].set_title("Detected regime")
    axes[1].set_xlabel("step")
    axes[1].set_ylabel("regime")

    fig.tight_layout()
    fig.savefig(plots_dir / "regime_comparison.png", dpi=150)
    plt.close(fig)


def _plot_confusion_matrix(df, warmup_end: int, plots_dir: Path) -> None:
    post = df[df["t"] >= warmup_end].copy()
    true_vals = post["regime_true"].values
    hat_vals = post["regime_hat"].values

    labels = REGIME_ORDER
    n_labels = len(labels)
    cm = np.zeros((n_labels, n_labels), dtype=int)

    label_idx = {l: i for i, l in enumerate(labels)}
    for tr, pr in zip(true_vals, hat_vals):
        if tr in label_idx and pr in label_idx:
            cm[label_idx[tr], label_idx[pr]] += 1

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues")

    ax.set_xticks(range(n_labels))
    ax.set_yticks(range(n_labels))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix (post-warmup)")

    for i in range(n_labels):
        for j in range(n_labels):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=color, fontsize=12)

    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(plots_dir / "confusion_matrix.png", dpi=150)
    plt.close(fig)


def job_entry(cfg: dict, ctx) -> None:
    seed = int(cfg["seed"])
    warmup_end = int(cfg["regime"]["warmup_steps"])

    df, thresh_LM, thresh_MH = run_wp2(cfg, seed, ctx=ctx)

    # --- Detection accuracy (post-warmup) ---
    post = df[df["t"] >= warmup_end].copy()
    correct = (post["regime_true"] == post["regime_hat"]).sum()
    total = len(post)
    accuracy = correct / total if total > 0 else 0.0
    ctx.logger.info(f"Detection accuracy (post-warmup): {accuracy:.4f} ({correct}/{total})")

    # --- Per-regime counts (based on regime_true, post-warmup) ---
    regime_counts = {}
    for r in REGIME_ORDER:
        cnt = int((post["regime_true"] == r).sum())
        pct = cnt / total if total > 0 else 0.0
        regime_counts[r] = {"count": cnt, "pct": round(pct, 4)}
        ctx.logger.info(f"Regime {r}: {cnt} steps ({pct:.2%})")

    # --- Empirical transition matrix (from regime_true over full series) ---
    true_labels = df["regime_true"].values
    label_idx = {l: i for i, l in enumerate(REGIME_ORDER)}
    trans_counts = np.zeros((3, 3), dtype=int)
    for i in range(1, len(true_labels)):
        fr = true_labels[i - 1]
        to = true_labels[i]
        if fr in label_idx and to in label_idx:
            trans_counts[label_idx[fr], label_idx[to]] += 1

    row_sums = trans_counts.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    trans_probs = trans_counts / row_sums

    ctx.logger.info("Empirical transition matrix:")
    for i, r in enumerate(REGIME_ORDER):
        ctx.logger.info(f"  {r}: {trans_probs[i].round(4).tolist()}")

    # --- Expected duration per regime: 1 / (1 - p_ii) ---
    expected_duration = {}
    for i, r in enumerate(REGIME_ORDER):
        p_ii = trans_probs[i, i]
        dur = 1.0 / (1.0 - p_ii) if p_ii < 1.0 else float("inf")
        expected_duration[r] = round(dur, 2)
        ctx.logger.info(f"Expected duration {r}: {dur:.2f} steps")

    # --- Log metrics ---
    ctx.metrics.log({
        "accuracy": round(accuracy, 4),
        "thresh_LM": round(thresh_LM, 4),
        "thresh_MH": round(thresh_MH, 4),
        **{f"count_{r}": regime_counts[r]["count"] for r in REGIME_ORDER},
        **{f"pct_{r}": regime_counts[r]["pct"] for r in REGIME_ORDER},
        **{f"expected_dur_{r}": expected_duration[r] for r in REGIME_ORDER},
    })

    # --- summary.json ---
    summary = {
        "accuracy": round(accuracy, 4),
        "thresh_LM": round(thresh_LM, 4),
        "thresh_MH": round(thresh_MH, 4),
        "per_regime": regime_counts,
        "expected_duration": expected_duration,
        "empirical_transition_matrix": {
            r: trans_probs[i].round(4).tolist() for i, r in enumerate(REGIME_ORDER)
        },
    }
    summary_path = Path(ctx.run_dir) / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    ctx.logger.info(f"Summary written to {summary_path}")

    # --- Plots ---
    plots_dir = Path(ctx.plots_dir)
    _plot_mid_series(df, plots_dir)
    ctx.logger.info("Plot saved: mid_series.png")

    _plot_sigma_hat(df, thresh_LM, thresh_MH, plots_dir)
    ctx.logger.info("Plot saved: sigma_hat.png")

    _plot_regime_comparison(df, warmup_end, plots_dir)
    ctx.logger.info("Plot saved: regime_comparison.png")

    _plot_confusion_matrix(df, warmup_end, plots_dir)
    ctx.logger.info("Plot saved: confusion_matrix.png")

    ctx.logger.info("WP2 synth regime job completed.")


# ============================================================
# FILE: src/wp2/compare_detectors.py
# ============================================================
"""Compare regime detectors on the same synthetic data."""
# Dedektör Karşılaştırması (WP2)
# -------------------------------
# rv_baseline, rv_dwell ve HMM dedektörlerinin tespit doğruluklarını
# gerçek rejim etiketlerine karşı ölçer ve raporlar.

from __future__ import annotations

import json
from pathlib import Path

from src.wp2.synth_regime import (
    assign_regime_hat_dwell,
    assign_regime_hat_hmm,
    run_wp2,
)

SEED = 123
CONFIG_PATH = Path("config/w2_synth.json")


def _accuracy(true: list[str], pred: list[str], warmup_end: int) -> float:
    """Post-warmup accuracy (fraction of matching labels)."""
    t = true[warmup_end:]
    p = pred[warmup_end:]
    return sum(a == b for a, b in zip(t, p)) / len(t)


def main() -> None:
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    warmup = int(cfg["regime"]["warmup_steps"])

    # --- generate data (also produces the RV baseline) ---
    df, thresh_LM, thresh_MH = run_wp2(cfg, seed=SEED)

    regime_true = df["regime_true"].tolist()
    sigma_hat = df["sigma_hat"].to_numpy()

    # --- Detector 1: rolling RV baseline (already in df) ---
    det_rv = df["regime_hat"].tolist()

    # --- Detector 2: RV + dwell filter ---
    det_dwell = assign_regime_hat_dwell(
        sigma_hat, thresh_LM, thresh_MH, warmup, min_dwell=5,
    )

    # --- Detector 3: HMM ---
    det_hmm = assign_regime_hat_hmm(sigma_hat, warmup_end=warmup, seed=SEED)

    # --- compute accuracies ---
    results = {
        "rv_baseline": _accuracy(regime_true, det_rv, warmup),
        "rv_dwell": _accuracy(regime_true, det_dwell, warmup),
        "hmm": _accuracy(regime_true, det_hmm, warmup),
    }

    # --- print summary ---
    print(f"{'Detector':<20} {'Accuracy':>8}")
    print("-" * 30)
    for name, acc in results.items():
        print(f"{name:<20} {acc:>8.4f}")

    # --- save per-step results ---
    df["det_rv"] = det_rv
    df["det_dwell"] = det_dwell
    df["det_hmm"] = det_hmm

    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "detector_comparison.csv", index=False)
    print(f"\nSaved to {out_dir / 'detector_comparison.csv'}")


if __name__ == "__main__":
    main()


# ============================================================
# FILE: src/wp3/env.py
# ============================================================
"""Gymnasium environment for market-making with MMSimulator backend."""
# Bu modül, PPO ajanının eğitim ve değerlendirme için kullandığı
# OpenAI Gymnasium uyumlu piyasa yapıcılığı ortamını tanımlar.
# Ajan her adımda half-spread (h) ve skew (m) seçer.

from __future__ import annotations

import gymnasium
import numpy as np
from gymnasium import spaces

from src.wp1.sim import ExecParams, MarketParams, MMSimulator, MMState


class MMEnv(gymnasium.Env):
    """Market-making env: agent chooses half-spread h and skew m each tick."""

    metadata = {"render_modes": []}

    def __init__(self, cfg: dict):
        """Initialise spaces and simulation parameters from *cfg*."""
        super().__init__()

        # Piyasa ve emir çalıştırma parametrelerini config'den yükle
        # Gözlem uzayı 6 boyutlu: [q_norm, sigma_hat, tau, r_L, r_M, r_H]
        # Eylem uzayı: h_idx(0-4) → h=1..5 tick, m_idx(0-4) → m=-2..+2 tick
        self.market = MarketParams(**cfg["market"])
        self.execp = ExecParams(**cfg["exec"])
        self.n_steps = int(cfg["episode"]["n_steps"])
        self.inv_max_clip = int(cfg["episode"].get("inv_max_clip", 50))

        wp3 = cfg.get("wp3", {})
        self.eta = float(wp3.get("eta", 0.01))
        # Regime-conditional eta: {"L": ..., "M": ..., "H": ...}
        # Eğer config'de yoksa None — fallback olarak self.eta kullanılır
        eta_regime_cfg = wp3.get("eta_regime", None)
        if eta_regime_cfg is not None:
            self.eta_regime = {
                "L": float(eta_regime_cfg["L"]),
                "M": float(eta_regime_cfg["M"]),
                "H": float(eta_regime_cfg["H"]),
            }
        else:
            self.eta_regime = None
        self.skew_penalty_c = float(wp3.get("skew_penalty_c", 0.0))
        self.use_sigma = bool(wp3.get("use_sigma", True))
        regime_source = str(wp3.get("regime_source", "hat"))
        # backward compat: eski use_regime flag'ini dönüştür
        if "regime_source" not in wp3 and "use_regime" in wp3:
            regime_source = "hat" if wp3["use_regime"] else "none"
        if regime_source not in ("none", "hat", "true"):
            raise ValueError(f"regime_source must be 'none', 'hat' or 'true', got: {regime_source!r}")
        self.regime_source = regime_source
        self.seed_val = int(cfg["seed"])
        self.cfg = cfg

        # obs: [q_norm, sigma_hat, tau, regime_L, regime_M, regime_H]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32,
        )
        # action: [h_idx(0..4), m_idx(0..4)]
        self.action_space = spaces.MultiDiscrete([5, 5])

        self._sim: MMSimulator | None = None
        self._state: MMState | None = None
        self._t: int = 0
        self._exog = None

    # ------------------------------------------------------------------
    def _get_obs(self) -> np.ndarray:
        """Build 6-dim observation vector."""
        q = np.clip(self._state.inv, -self.inv_max_clip, self.inv_max_clip)
        q_norm = q / self.inv_max_clip

        tau = (self.n_steps - self._t) / self.n_steps

        # sigma_hat
        if self._exog is not None and self.use_sigma:
            idx = min(self._t, len(self._exog) - 1)
            sh = float(self._exog["sigma_hat"].iloc[idx])
            if np.isnan(sh):
                sh = 0.0
        else:
            sh = 0.0

        # regime one-hot
        r_l = r_m = r_h = 0.0
        if self.regime_source != "none" and self._exog is not None:
            idx = min(self._t, len(self._exog) - 1)
            if self.regime_source == "true":
                label = str(self._exog["regime_true"].iloc[idx])
            else:
                label = str(self._exog["regime_hat"].iloc[idx])
            # warmup veya geçersiz label → zero one-hot (M'ye map etme)
            if label == "L":
                r_l = 1.0
            elif label == "M":
                r_m = 1.0
            elif label == "H":
                r_h = 1.0

        return np.array([q_norm, sh, tau, r_l, r_m, r_h], dtype=np.float32)

    # ------------------------------------------------------------------
    def reset(self, *, seed=None, options=None):
        """Reset env; optionally inject exogenous series via *options*."""
        super().reset(seed=seed)

        # Derive a sim seed: use explicit seed if given, else sample from
        # the Gymnasium-managed np_random (seeded by super().reset).
        if seed is not None:
            sim_seed = seed
        else:
            sim_seed = int(self.np_random.integers(0, 2**31 - 1))

        self._sim = MMSimulator(self.market, self.execp, seed=sim_seed)
        self._state = self._sim.reset()
        self._t = 0

        # Update exog only when explicitly provided; otherwise keep previous.
        if options and "exog" in options:
            self._exog = options["exog"]

        # If exog series is available, override initial mid from it.
        if self._exog is not None:
            self._state = MMState(
                t=0,
                mid=float(self._exog["mid"].iloc[0]),
                cash=0.0,
                inv=0,
            )
            self._sim._mid_hist = [self._state.mid]

        obs = self._get_obs()
        info = {"equity": self._state.equity, "inv": self._state.inv}
        return obs, info

    # ------------------------------------------------------------------
    def step(self, action):
        """Execute one tick: decode action, run sim, compute reward."""
        h_idx, m_idx = int(action[0]), int(action[1])
        # Eylem decode: h_idx → half-spread (1-5 tick), m_idx → skew (-2 ile +2 arası)
        # delta_bid = h + m (en az 1 tick), delta_ask = h - m (en az 1 tick)
        # Ödül = ΔEquity − η × inv² (PnL artışından envanter cezası düş)
        h = h_idx + 1        # ticks 1..5
        m = m_idx - 2        # skew  -2..+2

        delta_bid = max(1, h + m)
        delta_ask = max(1, h - m)

        equity_before = self._state.equity

        # when exogenous mid is available, override simulator's BM
        if self._exog is not None and (self._t + 1) < len(self._exog):
            exog_mid = float(self._exog["mid"].iloc[self._t + 1])
            orig_evolve = self._sim._evolve_mid
            self._sim._evolve_mid = lambda _mid, _m=exog_mid: _m
            try:
                self._state, info = self._sim.step(
                    self._state, delta_bid, delta_ask,
                )
            finally:
                self._sim._evolve_mid = orig_evolve
        else:
            self._state, info = self._sim.step(
                self._state, delta_bid, delta_ask,
            )

        self._t += 1

        equity_after = self._state.equity
        inv_after = self._state.inv

        # Regime-conditional eta seçimi
        if self.eta_regime is not None and self._exog is not None:
            idx = min(self._t - 1, len(self._exog) - 1)
            regime_now = str(self._exog["regime_hat"].iloc[idx])
            if regime_now not in ("L", "M", "H"):
                regime_now = "M"
            eta_now = self.eta_regime[regime_now]
        else:
            eta_now = self.eta
        # reward: PnL increment minus inventory penalty
        reward = (equity_after - equity_before) - eta_now * (inv_after ** 2) - self.skew_penalty_c * abs(m)

        terminated = self._t >= self.n_steps
        truncated = False

        obs = self._get_obs()
        info["equity"] = equity_after
        info["inv"] = inv_after

        return obs, float(reward), terminated, truncated, info


# ============================================================
# FILE: src/wp4/job_w4_ppo.py
# ============================================================
"""WP4: PPO training via Stable-Baselines3 on MMEnv."""
# PPO Eğitimi (WP4)
# -----------------
# Stable-Baselines3 ile PPO ajanını eğitir.
# ppo_aware: rejim one-hot gözlemler, ppo_blind: rejim etiketi almaz.
# Kronolojik train/test bölünmesi (%70/%30) kullanır.

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


# ============================================================
# FILE: src/wp5/job_w5_eval.py
# ============================================================
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


# ============================================================
# FILE: src/wp5/job_w5_ablation_eta.py
# ============================================================
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


# ============================================================
# FILE: src/wp5/job_w5_ablation_skew.py
# ============================================================
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


# ============================================================
# FILE: src/wp5/job_w5_detector_compare.py
# ============================================================
"""WP5 — Detector comparison: rv_baseline vs rv_dwell vs hmm (PPO-aware & PPO-blind)."""
# Detector Robustness Deneyi (WP5)
# ----------------------------------
# 3 dedektör × 20 seed × 2 strateji = 120 model eğitir ve değerlendirir.
# Dedektörler: rv_baseline (%60.7), rv_dwell (%60.4), HMM (%81.8)
# Null sonucun dedektör kalitesinden bağımsız olduğunu kanıtlar.

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
    df_out.to_csv(out_dir / "metrics_detector_pilot.csv", index=False)

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


# ============================================================
# FILE: src/wp5/analyze_actions.py
# ============================================================
"""WP5 action analysis: h/m distributions by regime across strategies."""
# Eylem Dağılımı Analizi (WP5)
# ------------------------------
# PPO ajanlarının rejim bazında half-spread (h) ve skew (m) dağılımlarını analiz eder.
# Cross-seed standart sapma kullanır (seed-level aggregation).
# Tez Şekil 3'ü (Action Distribution by Regime) üretir.

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _find_latest_eval_run() -> Path:
    runs = list(Path("results/runs").glob("*wp5-eval*"))
    if not runs:
        raise FileNotFoundError("No wp5-eval run found under results/runs/")
    return max(runs, key=lambda p: p.stat().st_mtime)


def _load_curves(run_dir: Path) -> pd.DataFrame:
    """Load all *_test.csv from curves/, parse strategy & seed from filename."""
    curves_dir = run_dir / "curves"
    pattern = re.compile(r"seed(\d+)_(.+)_test\.csv$")
    frames = []
    for csv_path in sorted(curves_dir.glob("*_test.csv")):
        m = pattern.search(csv_path.name)
        if m is None:
            continue
        seed, strategy = int(m.group(1)), m.group(2)
        df = pd.read_csv(csv_path)
        df["seed"] = seed
        df["strategy"] = strategy
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No *_test.csv files in {curves_dir}")
    return pd.concat(frames, ignore_index=True)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop warmup rows and rows with NaN h/m."""
    df = df[df["regime_hat"].isin(["L", "M", "H"])].copy()
    df = df.dropna(subset=["h", "m"])
    return df


def _seed_level_stats(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["seed", "strategy", "regime_hat"], as_index=False)
    out = g.agg(
        mean_h=("h", "mean"),
        mean_m=("m", "mean"),
        ph5=("h", lambda x: float((x == 5).mean())),
    )
    return out


# ── plots ────────────────────────────────────────────────────────────────

REGIMES = ["L", "M", "H"]
REGIME_COLORS = {"L": "#4CAF50", "M": "#FF9800", "H": "#F44336"}


STRATEGIES = ["AS", "naive", "ppo_aware", "ppo_blind"]


def _grouped_bar(ax, agg: pd.DataFrame, val_col: str, err_col: str, title: str):
    strategies = STRATEGIES
    x = np.arange(len(strategies))
    width = 0.25
    for i, reg in enumerate(REGIMES):
        sub = agg[agg["regime_hat"] == reg]
        # align on strategy order
        vals = [sub.loc[sub["strategy"] == s, val_col].values[0] for s in strategies]
        errs = [sub.loc[sub["strategy"] == s, err_col].values[0] for s in strategies]
        ax.bar(x + i * width, vals, width, yerr=errs, label=reg,
               color=REGIME_COLORS[reg], capsize=3)
    ax.set_xticks(x + width)
    ax.set_xticklabels(strategies)
    ax.set_title(title)
    ax.legend(title="Regime")
    ax.grid(axis="y", alpha=0.3)


def plot_h_by_regime(df: pd.DataFrame, out: Path):
    df_seed = _seed_level_stats(df)
    agg = (df_seed.groupby(["strategy", "regime_hat"])["mean_h"]
             .agg(mean_h="mean", std_h="std").reset_index())
    fig, ax = plt.subplots(figsize=(7, 4))
    _grouped_bar(ax, agg, "mean_h", "std_h", "Mean Half-Spread by Regime")
    ax.set_ylabel("h (ticks)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  saved {out}")


def plot_m_by_regime(df: pd.DataFrame, out: Path):
    df_seed = _seed_level_stats(df)
    agg = (df_seed.groupby(["strategy", "regime_hat"])["mean_m"]
             .agg(mean_m="mean", std_m="std").reset_index())
    fig, ax = plt.subplots(figsize=(7, 4))
    _grouped_bar(ax, agg, "mean_m", "std_m", "Mean Skew by Regime")
    ax.set_ylabel("m (ticks)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  saved {out}")


def plot_ph5_by_regime(df: pd.DataFrame, out: Path):
    df_seed = _seed_level_stats(df)
    agg = (df_seed.groupby(["strategy", "regime_hat"])["ph5"]
             .agg(ph5="mean", std_ph5="std").reset_index())
    x = np.arange(len(STRATEGIES))
    width = 0.25
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, reg in enumerate(REGIMES):
        sub = agg[agg["regime_hat"] == reg]
        vals = [sub.loc[sub["strategy"] == s, "ph5"].values[0] for s in STRATEGIES]
        errs = [sub.loc[sub["strategy"] == s, "std_ph5"].values[0] for s in STRATEGIES]
        ax.bar(x + i * width, vals, width, yerr=errs, label=reg,
               color=REGIME_COLORS[reg], capsize=3)
    ax.set_xticks(x + width)
    ax.set_xticklabels(STRATEGIES)
    ax.set_ylabel("P(h=5)")
    ax.set_title("P(h=5 | Regime) — Undertrading Indicator")
    ax.legend(title="Regime")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  saved {out}")


def print_table(df: pd.DataFrame):
    df_seed = _seed_level_stats(df)
    rows = []
    for (strat, reg), g in df_seed.groupby(["strategy", "regime_hat"]):
        rows.append({
            "strategy": strat,
            "regime": reg,
            "mean_h": g["mean_h"].mean(),
            "std_h": g["mean_h"].std(),
            "mean_m": g["mean_m"].mean(),
            "std_m": g["mean_m"].std(),
            "P(h=5)": g["ph5"].mean(),
            "std_ph5": g["ph5"].std(),
        })
    tbl = pd.DataFrame(rows)
    fmt = {"mean_h": "{:.2f}", "std_h": "{:.2f}",
           "mean_m": "{:.2f}", "std_m": "{:.2f}", "P(h=5)": "{:.3f}",
           "std_ph5": "{:.3f}"}
    print("\n" + tbl.to_string(index=False, formatters={
        k: v.format for k, v in fmt.items()
    }))


# ── main ─────────────────────────────────────────────────────────────────

def main():
    run_dir = _find_latest_eval_run()
    print(f"Run dir: {run_dir}")

    df = _load_curves(run_dir)
    print(f"Loaded {len(df)} rows, strategies: {sorted(df['strategy'].unique())}")

    df = _clean(df)
    print(f"After clean: {len(df)} rows")

    plots_dir = run_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    plot_h_by_regime(df, plots_dir / "action_h_by_regime.png")
    plot_m_by_regime(df, plots_dir / "action_m_by_regime.png")
    plot_ph5_by_regime(df, plots_dir / "ph5_by_regime.png")
    print_table(df)


if __name__ == "__main__":
    main()


# ============================================================
# FILE: src/wp5/stats_detector_robustness.py
# ============================================================
"""Statistical analysis of detector robustness experiment results."""
# İstatistiksel Testler — Detector Robustness (WP5)
# ---------------------------------------------------
# 120 modelin (3 dedektör × 20 seed × 2 strateji) istatistiksel analizini yapar.
# - Paired t-test: ppo_aware vs ppo_blind (her dedektör için ayrı)
# - One-way ANOVA: dedektör seçiminin ppo_aware'e etkisi
# - Sonuçlar: stats_detector_robustness.txt

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


def find_results_csv() -> Path:
    """Find the most recent detector-full run's metrics CSV."""
    runs_dir = Path("results/runs")
    candidates = sorted(runs_dir.glob("*detector-full*"), key=lambda p: p.name)
    if not candidates:
        print("ERROR: No detector-full run found under results/runs/")
        sys.exit(1)
    run_dir = candidates[-1]
    csv_path = run_dir / "metrics_detector_pilot.csv"
    if not csv_path.exists():
        csv_path = run_dir / "metrics_detector_compare.csv"
    if not csv_path.exists():
        print(f"ERROR: No metrics CSV in {run_dir}")
        sys.exit(1)
    return csv_path


def paired_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Paired t-test: ppo_aware vs ppo_blind for each detector x metric."""
    rows = []
    for detector in sorted(df["detector"].unique()):
        sub = df[df["detector"] == detector]
        aware = sub[sub["strategy"] == "ppo_aware"].sort_values("seed")
        blind = sub[sub["strategy"] == "ppo_blind"].sort_values("seed")

        for metric in ["sharpe_like", "final_equity"]:
            a = aware[metric].values
            b = blind[metric].values
            diff = a - b
            t_stat, p_val = stats.ttest_rel(a, b)
            rows.append({
                "detector": detector,
                "metric": metric,
                "mean_aware": float(np.mean(a)),
                "mean_blind": float(np.mean(b)),
                "mean_diff": float(np.mean(diff)),
                "t_stat": float(t_stat),
                "p_value": float(p_val),
                "significant": "Yes" if p_val < 0.05 else "No",
            })
    return pd.DataFrame(rows)


def anova_across_detectors(df: pd.DataFrame) -> dict:
    """One-way ANOVA: does ppo_aware sharpe differ across detectors?"""
    aware = df[df["strategy"] == "ppo_aware"]
    groups = [
        g["sharpe_like"].values
        for _, g in aware.groupby("detector")
    ]
    f_stat, p_val = stats.f_oneway(*groups)
    return {
        "test": "one-way ANOVA (ppo_aware sharpe_like across detectors)",
        "F_stat": float(f_stat),
        "p_value": float(p_val),
        "significant": "Yes" if p_val < 0.05 else "No",
    }


def main():
    csv_path = find_results_csv()
    print(f"Reading: {csv_path}\n")

    df = pd.read_csv(csv_path)
    print(f"Rows: {len(df)}, Detectors: {sorted(df['detector'].unique())}")
    print(f"Seeds: {sorted(df['seed'].unique())}\n")

    # --- Paired t-tests ---
    results = paired_tests(df)

    fmt = {
        "mean_aware": "{:.4f}",
        "mean_blind": "{:.4f}",
        "mean_diff": "{:.4f}",
        "t_stat": "{:.4f}",
        "p_value": "{:.4f}",
    }
    table_str = results.to_string(
        index=False,
        formatters={k: v.format for k, v in fmt.items()},
    )

    print("=" * 90)
    print("PAIRED T-TEST: ppo_aware vs ppo_blind (per detector, per metric)")
    print("=" * 90)
    print(table_str)

    # --- ANOVA ---
    anova = anova_across_detectors(df)
    anova_str = (
        f"\n{'=' * 90}\n"
        f"ONE-WAY ANOVA: ppo_aware sharpe_like across detectors\n"
        f"{'=' * 90}\n"
        f"F-stat: {anova['F_stat']:.4f}, p-value: {anova['p_value']:.4f}, "
        f"significant: {anova['significant']}\n"
    )
    print(anova_str)

    # --- Summary ---
    summary_lines = [
        "\nSUMMARY",
        "-" * 40,
    ]
    sig_count = int((results["significant"] == "Yes").sum())
    summary_lines.append(
        f"Significant tests (p<0.05): {sig_count} / {len(results)}"
    )
    if sig_count == 0:
        summary_lines.append(
            "Null result: no detector shows significant aware vs blind difference."
        )
    else:
        sig_rows = results[results["significant"] == "Yes"]
        for _, r in sig_rows.iterrows():
            direction = "aware > blind" if r["mean_diff"] > 0 else "blind > aware"
            summary_lines.append(
                f"  {r['detector']} / {r['metric']}: p={r['p_value']:.4f} ({direction})"
            )
    summary_str = "\n".join(summary_lines)
    print(summary_str)

    # --- Save to file ---
    out_path = Path("results/stats_detector_robustness.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Source: {csv_path}\n\n")
        f.write("PAIRED T-TEST: ppo_aware vs ppo_blind (per detector, per metric)\n")
        f.write(table_str + "\n")
        f.write(anova_str + "\n")
        f.write(summary_str + "\n")
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()


# ============================================================
# FILE: src/wp5/figure_thesis.py
# ============================================================
"""Generate thesis figures from WP5 OOS results."""
# Tez Figür Üretimi (WP5)
# -------------------------
# Tezdeki tüm ana figürleri üretir ve results/plots/thesis/ klasörüne kaydeder:
# - fig1_sharpe_inv.png: Sharpe ve inv_p99 karşılaştırması
# - fig2_paired_seed.png: Seed bazında PPO-aware vs PPO-blind scatter
# - fig3_regime_sharpe.png: Volatilite rejimine göre Sharpe
# - fig4_detector_robustness.png: Dedektör karşılaştırması
# - fig5_action_analysis.png: Eylem dağılımı

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ── paths ────────────────────────────────────────────────────────────────

MAIN_RUN = Path("results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc")
DETECTOR_CSV = Path(
    "results/runs/20260316-223842_seed1_wp5-detector-full_a67e381"
    "/metrics_detector_pilot.csv"
)
OOS_CSV = MAIN_RUN / "metrics_wp5_oos.csv"
REGIME_CSV = MAIN_RUN / "metrics_wp5_oos_by_regime.csv"
CURVES_DIR = MAIN_RUN / "curves"
OUT_DIR = Path("results/plots/thesis")

# ── style ────────────────────────────────────────────────────────────────

COLORS = {
    "AS": "#888888",
    "naive": "#5B9BD5",
    "ppo_blind": "#ED7D31",
    "ppo_aware": "#2E75B6",
}
STRAT_ORDER = ["AS", "naive", "ppo_blind", "ppo_aware"]
STRAT_LABELS = {"AS": "AS", "naive": "Naive", "ppo_blind": "PPO-blind", "ppo_aware": "PPO-aware"}
REGIMES = ["L", "M", "H"]

plt.rcParams.update({
    "font.size": 11,
    "figure.dpi": 150,
    "figure.autolayout": True,
})


# ── helpers ──────────────────────────────────────────────────────────────

def _bar_labels(ax, bars, fmt=".2f"):
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h,
                f"{h:{fmt}}", ha="center", va="bottom", fontsize=9)


def _load_curves() -> pd.DataFrame:
    pattern = re.compile(r"seed(\d+)_(.+)_test\.csv$")
    frames = []
    for csv_path in sorted(CURVES_DIR.glob("*_test.csv")):
        m = pattern.search(csv_path.name)
        if m is None:
            continue
        seed, strategy = int(m.group(1)), m.group(2)
        df = pd.read_csv(csv_path)
        df["seed"] = seed
        df["strategy"] = strategy
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# ── figure 1 ─────────────────────────────────────────────────────────────

def fig1_sharpe_inv(oos: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    labels = [STRAT_LABELS[s] for s in STRAT_ORDER]

    for ax, col, title in [
        (ax1, "sharpe_like", "Mean Sharpe Ratio (OOS, 20 Seeds)"),
        (ax2, "inv_p99", "Inventory Risk — inv_p99 (OOS, 20 Seeds)"),
    ]:
        means, stds = [], []
        for s in STRAT_ORDER:
            sub = oos[oos["strategy"] == s][col]
            means.append(sub.mean())
            stds.append(sub.std())
        x = np.arange(len(STRAT_ORDER))
        bars = ax.bar(x, means, yerr=stds, capsize=4,
                      color=[COLORS[s] for s in STRAT_ORDER])
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylim(bottom=0)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
        _bar_labels(ax, bars)

    ax2.set_ylabel("inv_p99 (lots)")
    fig.text(0.75, -0.02, "Note: Lower inv_p99 is better.",
             ha="center", fontsize=9, style="italic")

    out = OUT_DIR / "fig1_sharpe_inv.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


# ── figure 2 ─────────────────────────────────────────────────────────────

def fig2_paired_seed(oos: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    aware = oos[oos["strategy"] == "ppo_aware"].set_index("seed")
    blind = oos[oos["strategy"] == "ppo_blind"].set_index("seed")
    seeds = sorted(set(aware.index) & set(blind.index))

    for ax, col, title, pval, win_text in [
        (ax1, "sharpe_like",
         "Sharpe Ratio: PPO-aware vs PPO-blind (per seed)", 0.261,
         "Aware > Blind: 11/20 seeds"),
        (ax2, "final_equity",
         "Final Equity: PPO-aware vs PPO-blind (per seed)", 0.023,
         "Aware > Blind: 9/20 seeds"),
    ]:
        x_vals = blind.loc[seeds, col].values
        y_vals = aware.loc[seeds, col].values
        ax.scatter(x_vals, y_vals, c=COLORS["ppo_aware"], edgecolors="k",
                   linewidths=0.5, s=40, zorder=3)
        lo = min(x_vals.min(), y_vals.min()) * 0.95
        hi = max(x_vals.max(), y_vals.max()) * 1.05
        ax.plot([lo, hi], [lo, hi], "--", color="grey", linewidth=1, zorder=1)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box")
        xlabel = "PPO-blind Sharpe" if "Sharpe" in title else "PPO-blind Equity"
        ylabel = "PPO-aware Sharpe" if "Sharpe" in title else "PPO-aware Equity"
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.text(0.05, 0.05, f"p = {pval}", transform=ax.transAxes,
                fontsize=10, verticalalignment="bottom")
        ax.text(0.05, 0.92, win_text, transform=ax.transAxes,
                fontsize=9, verticalalignment="top")
        ax.grid(alpha=0.3)

    out = OUT_DIR / "fig2_paired_seed.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


# ── figure 3 ─────────────────────────────────────────────────────────────

def fig3_regime_sharpe(regime: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(REGIMES))
    n = len(STRAT_ORDER)
    width = 0.18

    for i, s in enumerate(STRAT_ORDER):
        means, stds = [], []
        for r in REGIMES:
            sub = regime[(regime["strategy"] == s) & (regime["regime"] == r)]
            means.append(sub["sharpe_like"].mean())
            stds.append(sub["sharpe_like"].std())
        ax.bar(x + i * width, means, width, yerr=stds, capsize=3,
               color=COLORS[s], label=STRAT_LABELS[s])

    ax.set_xticks(x + width * (n - 1) / 2)
    ax.set_xticklabels(REGIMES)
    ax.set_xlabel("Volatility Regime")
    ax.set_ylabel("Mean Sharpe")
    ax.set_ylim(bottom=0)
    ax.set_title("Sharpe Ratio by Volatility Regime", fontsize=12, fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    fig.text(0.5, -0.02,
             "Regime-wise metrics are grouped by the true synthetic regime "
             "(ex-post attribution).",
             ha="center", fontsize=9, style="italic")

    out = OUT_DIR / "fig3_regime_sharpe.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


# ── figure 4 ─────────────────────────────────────────────────────────────

def fig4_detector_robustness(det: pd.DataFrame):
    detectors = ["rv_baseline", "rv_dwell", "hmm"]
    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.arange(len(detectors))
    for i, d in enumerate(detectors):
        sub = det[det["detector"] == d]
        aware_vals = sub[sub["strategy"] == "ppo_aware"]["sharpe_like"]
        blind_vals = sub[sub["strategy"] == "ppo_blind"]["sharpe_like"]
        aware_mean, aware_std = aware_vals.mean(), aware_vals.std()
        blind_mean, blind_std = blind_vals.mean(), blind_vals.std()

        # vertical line
        ax.plot([i, i], [blind_mean, aware_mean], color="grey", linewidth=1.5,
                zorder=1)
        # aware dot with error bar
        ax.errorbar(i, aware_mean, yerr=aware_std, fmt="o",
                    color=COLORS["ppo_aware"], markersize=10, capsize=4,
                    zorder=3, label="PPO-aware" if i == 0 else "")
        ax.text(i + 0.10, aware_mean, f"{aware_mean:.3f}", va="center", fontsize=9)
        # blind dot with error bar
        ax.errorbar(i, blind_mean, yerr=blind_std, fmt="s",
                    color=COLORS["ppo_blind"], markersize=9, capsize=4,
                    zorder=3, label="PPO-blind" if i == 0 else "")
        ax.text(i + 0.10, blind_mean, f"{blind_mean:.3f}", va="center", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(detectors)
    ax.set_ylim(0.60, 0.80)
    ax.set_ylabel("Mean Sharpe")
    ax.set_title("Detector Robustness: Mean Sharpe by Detector (20 Seeds)",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    annotation = ("rv_baseline: p=0.114 | rv_dwell: p=0.110 | "
                  "HMM: p=0.082 (Sharpe, paired t-test)")
    fig.text(0.5, -0.02, annotation, ha="center", fontsize=9, style="italic")
    fig.text(0.5, -0.06,
             "Y-axis is zoomed (0.60\u20130.80) to highlight detector-level differences.",
             ha="center", fontsize=9, style="italic")

    out = OUT_DIR / "fig4_detector_robustness.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


# ── figure 5 ─────────────────────────────────────────────────────────────

def fig5_action_analysis(curves: pd.DataFrame):
    curves = curves[curves["regime_hat"].isin(REGIMES)].dropna(subset=["h", "m"])

    # per-seed mean h/m by strategy+regime
    seed_agg = (curves.groupby(["seed", "strategy", "regime_hat"])
                .agg(mean_h=("h", "mean"), mean_m=("m", "mean"))
                .reset_index())

    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    fig.suptitle("Action Distribution by Regime: PPO-aware vs PPO-blind",
                 fontsize=12, fontweight="bold")

    strat_colors = {"ppo_aware": "#2E75B6", "ppo_blind": "#ED7D31"}

    configs = [
        (axes[0, 0], "ppo_aware", "mean_h", "PPO-aware: Mean Half-Spread (h)", False),
        (axes[0, 1], "ppo_blind", "mean_h", "PPO-blind: Mean Half-Spread (h)", False),
        (axes[1, 0], "ppo_aware", "mean_m", "PPO-aware: Mean Skew (m)", True),
        (axes[1, 1], "ppo_blind", "mean_m", "PPO-blind: Mean Skew (m)", True),
    ]

    for ax, strat, col, title, show_zero in configs:
        sub = seed_agg[seed_agg["strategy"] == strat]
        x = np.arange(len(REGIMES))
        means, stds = [], []
        for r in REGIMES:
            vals = sub[sub["regime_hat"] == r][col]
            means.append(vals.mean())
            stds.append(vals.std())
        bars = ax.bar(x, means, yerr=stds, capsize=4,
                      color=strat_colors[strat])
        ax.set_xticks(x)
        ax.set_xticklabels(REGIMES)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
        if show_zero:
            ax.axhline(0, color="black", linewidth=0.8, linestyle="-")

    # sync y-axis limits: h subplots 0–3.0, m subplots -0.3–0.3
    for ax in axes[0]:
        ax.set_ylim(0, 3.0)
    for ax in axes[1]:
        ax.set_ylim(-0.3, 0.3)

    out = OUT_DIR / "fig5_action_analysis.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out}")


# ── main ─────────────────────────────────────────────────────────────────

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    oos = pd.read_csv(OOS_CSV)
    oos = oos[oos["split"] == "test"]
    regime = pd.read_csv(REGIME_CSV)
    det = pd.read_csv(DETECTOR_CSV)
    curves = _load_curves()

    print(f"OOS rows: {len(oos)}, Regime rows: {len(regime)}, "
          f"Detector rows: {len(det)}, Curve rows: {len(curves)}")

    fig1_sharpe_inv(oos)
    fig2_paired_seed(oos)
    fig3_regime_sharpe(regime)
    fig4_detector_robustness(det)
    fig5_action_analysis(curves)

    print("\nAll figures saved to", OUT_DIR)


if __name__ == "__main__":
    main()


# ============================================================
# FILE: config/base.json
# ============================================================
{
  "project": "thesis-hfmm",
  "seed": 123,
  "run_tag": "wp0-smoke",
  "n_steps": 200
}


# ============================================================
# FILE: config/w1_naive_sweep.json
# ============================================================
{
  "job": "w1_naive_sweep",
  "seed": 123,
  "market": {
    "mid0": 100.0,
    "tick_size": 0.01,
    "dt": 0.2,
    "sigma_mid_ticks": 0.8
  },
  "exec": {
    "A": 5.0,
    "k": 1.5,
    "fee_bps": 0.2,
    "latency_steps": 1
  },
  "episode": {
    "n_steps": 8000
  },
  "sweep": {
    "half_spreads_ticks": [1, 2, 3, 4, 5]
  }
}


# ============================================================
# FILE: config/w1_as_baseline.json
# ============================================================
{
  "job": "w1_as_baseline",
  "seed": 123,
  "market": {
    "mid0": 100.0,
    "tick_size": 0.01,
    "dt": 0.2,
    "sigma_mid_ticks": 0.8
  },
  "exec": {
    "A": 5.0,
    "k": 1.5,
    "fee_bps": 0.2,
    "latency_steps": 1
  },
  "episode": {
    "n_steps": 8000
  },
  "as": {
    "gamma": 0.01,
    "horizon_steps": 8000,
    "min_delta_ticks": 1,
    "max_delta_ticks": 25
  }
}


# ============================================================
# FILE: config/w1_compare.json
# ============================================================
{
  "job": "w1_compare",
  "seed": 123,
  "market": {
    "mid0": 100.0,
    "tick_size": 0.01,
    "dt": 0.2,
    "sigma_mid_ticks": 0.8
  },
  "exec": {
    "A": 5.0,
    "k": 1.5,
    "fee_bps": 0.2,
    "latency_steps": 1
  },
  "episode": {
    "n_steps": 8000
  },
  "sweep": {
    "half_spreads_ticks": [1, 2, 3, 4, 5]
  },
  "as": {
    "gamma": 0.01,
    "horizon_steps": 8000,
    "min_delta_ticks": 1,
    "max_delta_ticks": 25
  }
}


# ============================================================
# FILE: config/w2_synth.json
# ============================================================
{
  "job": "w2_synth",
  "seed": 123,
  "run_tag": "wp2-synth",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2},
  "regime": {
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.5, 1.0, 2.0],
    "rv_window": 50,
    "warmup_steps": 1000,
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "episode": {"n_steps": 10000}
}


# ============================================================
# FILE: config/w3_sanity.json
# ============================================================
{
  "job": "w3_sanity",
  "seed": 123,
  "run_tag": "wp3-sanity",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.01, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  }
}


# ============================================================
# FILE: config/w3_sanity_both.json
# ============================================================
{
  "job": "w3_sanity",
  "seed": 123,
  "run_tag": "wp3-sanity-both",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.01, "use_regime": false},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  }
}


# ============================================================
# FILE: config/w4_ppo.json
# ============================================================
{
  "job": "w4_ppo",
  "seed": 123,
  "run_tag": "wp4-ppo",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.01, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 200000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.0
  }
}


# ============================================================
# FILE: config/w5_main.json
# ============================================================
{
  "job": "w5_eval",
  "seed": 1,
  "run_tag": "wp5-ablation",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.001, "use_sigma": true, "regime_source": "hat"},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "device": "cpu"
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0}
  }
}


# ============================================================
# FILE: config/w5_ablation_eta.json
# ============================================================
{
  "job": "w5_ablation_eta",
  "seed": 11,
  "run_tag": "wp5-ablation-eta",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.01, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 200000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.0
  },
  "wp5": {
    "seeds": [11, 22, 33],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0},
    "eta_values": [0.0001, 0.001, 0.01]
  }
}


# ============================================================
# FILE: config/w5_ablation_skew.json
# ============================================================
{
  "job": "w5_ablation_skew",
  "seed": 1,
  "run_tag": "wp5-ablation-skew",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.001, "use_regime": true, "skew_penalty_c": 0.0},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0},
    "skew_c_values": [1e-4]
  }
}


# ============================================================
# FILE: config/w5_detector_pilot.json
# ============================================================
{
  "job": "w5_detector_compare",
  "seed": 1,
  "run_tag": "wp5-detector-pilot",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.001, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01
  },
  "wp5": {
    "seeds": [1, 2, 3],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0}
  }
}


# ============================================================
# FILE: config/w5_detector_full.json
# ============================================================
{
  "job": "w5_detector_compare",
  "seed": 1,
  "run_tag": "wp5-detector-full",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.001, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0}
  }
}


# ============================================================
# FILE: config/w5_eta_regime.json
# ============================================================
{
  "job": "w5_eval",
  "seed": 42,
  "run_tag": "w5-eta-regime",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {
    "eta": 0.001,
    "eta_regime": {
      "L": 0.0005,
      "M": 0.001,
      "H": 0.0025
    },
    "use_sigma": true,
    "regime_source": "hat"
  },
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "device": "cpu"
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0}
  }
}

# ============================================================
# FILE: config/w5_misspec_mild.json
# ============================================================
{
  "job": "w5_eval",
  "run_tag": "w5-misspec-mild",
  "seed": 1,
  "market": {
    "mid0": 100.0,
    "tick_size": 0.01,
    "dt": 0.2,
    "sigma_mid_ticks": 0.8
  },
  "exec": {
    "A": 5.0,
    "k": 1.5,
    "fee_bps": 0.2,
    "latency_steps": 1
  },
  "misspec": {
    "enabled": true,
    "params": {
      "L": {"A": 4.0, "k": 1.8},
      "M": {"A": 5.0, "k": 1.5},
      "H": {"A": 6.0, "k": 1.2}
    }
  },
  "episode": {
    "n_steps": 8000,
    "inv_max_clip": 50
  },
  "wp3": {
    "eta": 0.001,
    "use_regime": true,
    "use_sigma": true,
    "regime_source": "hat"
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "device": "cuda"
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0},
    "variants": ["sigma_only", "regime_only", "combined", "oracle_pure", "oracle_full"]
  },
  "as": {
    "gamma": 0.01,
    "horizon_steps": 8000,
    "min_delta_ticks": 1,
    "max_delta_ticks": 25
  },
  "regime": {
    "rv_window": 50,
    "warmup_steps": 400,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.5, 1.0, 2.0],
    "trans_matrix": [[0.9967, 0.0023, 0.001], [0.0042, 0.9917, 0.0041], [0.001, 0.003, 0.996]]
  }
}

