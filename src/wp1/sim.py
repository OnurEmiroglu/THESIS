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
