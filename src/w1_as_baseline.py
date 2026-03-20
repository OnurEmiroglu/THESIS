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
