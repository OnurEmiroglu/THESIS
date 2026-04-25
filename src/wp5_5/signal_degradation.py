"""Signal degradation transformations for WP5.5 audit (pure numpy).

Each transform takes a clean sigma_hat array (1-D, may contain NaN during
warmup) and returns a degraded array of identical shape and dtype.
"""

from __future__ import annotations

import numpy as np


def apply_noise(
    sigma_hat: np.ndarray,
    noise_std: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Add i.i.d. Gaussian noise (std=noise_std) to non-NaN positions."""
    out = sigma_hat.astype(np.float64, copy=True)
    mask = ~np.isnan(out)
    out[mask] = out[mask] + rng.normal(0.0, noise_std, size=int(mask.sum()))
    return out.astype(sigma_hat.dtype, copy=False)


def apply_lag(sigma_hat: np.ndarray, k_steps: int) -> np.ndarray:
    """Shift array right by k_steps; leading k_steps become NaN."""
    n = len(sigma_hat)
    out = np.empty(n, dtype=np.float64)
    k = max(0, int(k_steps))
    k = min(k, n)
    out[:k] = np.nan
    if n - k > 0:
        out[k:] = sigma_hat[: n - k].astype(np.float64, copy=False)
    return out.astype(sigma_hat.dtype, copy=False)


def apply_coarsen(sigma_hat: np.ndarray, cutpoints: np.ndarray) -> np.ndarray:
    """Discretize sigma_hat into bins defined by cutpoints; return bin midpoints.

    cutpoints: 1-D array of length (n_bins - 1) with interior boundaries.
    Bin midpoints are inferred assuming uniform cutpoint spacing (as produced
    by compute_clean_cutpoints).
    """
    cuts = np.asarray(cutpoints, dtype=np.float64).ravel()
    n_cuts = len(cuts)
    n_bins = n_cuts + 1

    if n_cuts >= 2:
        spacing = float(cuts[1] - cuts[0])
    else:
        # degenerate case — fall back to unit spacing
        spacing = 1.0

    mids = np.empty(n_bins, dtype=np.float64)
    if n_bins == 1:
        mids[0] = float(cuts[0]) if n_cuts else 0.0
    else:
        mids[0] = cuts[0] - spacing / 2.0
        for i in range(1, n_bins - 1):
            mids[i] = cuts[i - 1] + spacing / 2.0
        mids[-1] = cuts[-1] + spacing / 2.0

    out = np.full(sigma_hat.shape, np.nan, dtype=np.float64)
    valid = ~np.isnan(sigma_hat)
    if valid.any():
        idx = np.searchsorted(cuts, sigma_hat[valid].astype(np.float64), side="right")
        idx = np.clip(idx, 0, n_bins - 1)
        out[valid] = mids[idx]
    return out.astype(sigma_hat.dtype, copy=False)


def apply_remove(sigma_hat: np.ndarray, fill_value: float = 0.0) -> np.ndarray:
    """Replace all values (including warmup NaNs) with fill_value."""
    return np.full(sigma_hat.shape, fill_value, dtype=sigma_hat.dtype)


def compute_clean_cutpoints(
    sigma_hat_clean: np.ndarray,
    warmup_end: int,
    n_bins: int = 5,
) -> np.ndarray:
    """Fixed bin cutpoints from the clean warmup distribution.

    Uses np.linspace between min and max of warmup-region non-NaN values to
    build (n_bins + 1) edges, and returns the (n_bins - 1) interior
    boundaries. These cutpoints are reused identically across all conditions.
    """
    warm = sigma_hat_clean[:warmup_end]
    warm = warm[~np.isnan(warm)]
    if len(warm) == 0:
        raise ValueError("compute_clean_cutpoints: no finite warmup values")
    lo = float(np.min(warm))
    hi = float(np.max(warm))
    edges = np.linspace(lo, hi, int(n_bins) + 1)
    return edges[1:-1].astype(np.float64, copy=False)
