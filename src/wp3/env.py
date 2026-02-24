"""Gymnasium environment for market-making with MMSimulator backend."""

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

        self.market = MarketParams(**cfg["market"])
        self.execp = ExecParams(**cfg["exec"])
        self.n_steps = int(cfg["episode"]["n_steps"])
        self.inv_max_clip = int(cfg["episode"].get("inv_max_clip", 50))

        wp3 = cfg.get("wp3", {})
        self.eta = float(wp3.get("eta", 0.01))
        self.use_regime = bool(wp3.get("use_regime", True))
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

        if self._exog is not None:
            idx = min(self._t, len(self._exog) - 1)
            sh = float(self._exog["sigma_hat"].iloc[idx])
            if np.isnan(sh):
                sh = 0.0
            regime = str(self._exog["regime_hat"].iloc[idx])
        else:
            sh = 0.0
            regime = "M"

        if regime not in ("L", "M", "H"):
            regime = "M"

        tau = (self.n_steps - self._t) / self.n_steps

        if self.use_regime:
            r_l = 1.0 if regime == "L" else 0.0
            r_m = 1.0 if regime == "M" else 0.0
            r_h = 1.0 if regime == "H" else 0.0
        else:
            r_l = r_m = r_h = 0.0

        return np.array([q_norm, sh, tau, r_l, r_m, r_h], dtype=np.float32)

    # ------------------------------------------------------------------
    def reset(self, *, seed=None, options=None):
        """Reset env; optionally inject exogenous series via *options*."""
        super().reset(seed=seed)

        s = seed if seed is not None else self.seed_val
        self._sim = MMSimulator(self.market, self.execp, seed=s)
        self._state = self._sim.reset()
        self._t = 0

        if options and "exog" in options:
            self._exog = options["exog"]
            # override initial mid from exogenous series
            self._state = MMState(
                t=0,
                mid=float(self._exog["mid"].iloc[0]),
                cash=0.0,
                inv=0,
            )
            self._sim._mid_hist = [self._state.mid]
        else:
            self._exog = None

        obs = self._get_obs()
        info = {"equity": self._state.equity, "inv": self._state.inv}
        return obs, info

    # ------------------------------------------------------------------
    def step(self, action):
        """Execute one tick: decode action, run sim, compute reward."""
        h_idx, m_idx = int(action[0]), int(action[1])
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

        # reward: PnL increment minus inventory penalty
        reward = (equity_after - equity_before) - self.eta * (inv_after ** 2)

        terminated = self._t >= self.n_steps
        truncated = False

        obs = self._get_obs()
        info["equity"] = equity_after
        info["inv"] = inv_after

        return obs, float(reward), terminated, truncated, info
