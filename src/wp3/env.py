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

        # Model misspecification: regime-dependent fill parameters
        misspec = cfg.get("misspec", {})
        self.misspec_enabled = bool(misspec.get("enabled", False))
        self.misspec_params = misspec.get("params", {})
        # e.g. {"L": {"A": 4.0, "k": 1.8}, "M": {"A": 5.0, "k": 1.5}, "H": {"A": 6.0, "k": 1.2}}

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

        # Apply misspec: override simulator exec params based on regime_true
        if self.misspec_enabled and self._exog is not None and "regime_true" in self._exog.columns:
            idx = min(self._t, len(self._exog) - 1)
            regime_true = str(self._exog["regime_true"].iloc[idx])
            if regime_true in self.misspec_params:
                p = self.misspec_params[regime_true]
                from src.wp1.sim import ExecParams
                self._sim.e = ExecParams(
                    A=float(p.get("A", self.execp.A)),
                    k=float(p.get("k", self.execp.k)),
                    fee_bps=self.execp.fee_bps,
                    latency_steps=self.execp.latency_steps,
                )

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
