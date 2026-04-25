"""Audit metrics for WP5.5 signal degradation ladder.

All functions operate on the post-warmup region and ignore NaNs / warmup labels.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

from src.wp2.synth_regime import assign_regime_hat


def _drop_invalid(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    keep = ~(np.isnan(a) | np.isnan(b))
    return a[keep], b[keep]


def spearman_correlation(
    clean: np.ndarray,
    degraded: np.ndarray,
    mask: np.ndarray,
) -> float:
    c = np.asarray(clean)[mask]
    d = np.asarray(degraded)[mask]
    c, d = _drop_invalid(c, d)
    if len(c) < 3:
        return 0.0
    if np.all(d == d[0]) or np.all(c == c[0]):
        return 0.0
    r, _ = stats.spearmanr(c, d)
    return 0.0 if np.isnan(r) else float(r)


def pearson_correlation(
    clean: np.ndarray,
    degraded: np.ndarray,
    mask: np.ndarray,
) -> float:
    c = np.asarray(clean)[mask]
    d = np.asarray(degraded)[mask]
    c, d = _drop_invalid(c, d)
    if len(c) < 3:
        return 0.0
    if np.all(d == d[0]) or np.all(c == c[0]):
        return 0.0
    r, _ = stats.pearsonr(c, d)
    return 0.0 if np.isnan(r) else float(r)


def regime_classification_accuracy(
    degraded_sigma: np.ndarray,
    regime_true: list,
    thresh_LM: float,
    thresh_MH: float,
    warmup_end: int,
) -> float:
    """Apply rv_baseline detector to degraded signal with clean thresholds."""
    # assign_regime_hat handles NaN via comparisons (NaN < x is False in numpy),
    # which would route NaNs into the "H" bucket. Replace NaN post-warmup with
    # a sentinel that lands in a deterministic bucket — 0.0 (forces "L"), but
    # the accuracy comparison still counts that as a misclassification when
    # regime_true differs, which is the desired behaviour.
    safe = np.asarray(degraded_sigma, dtype=np.float64).copy()
    nan_mask = np.isnan(safe)
    if nan_mask.any():
        safe[nan_mask] = 0.0
    pred = assign_regime_hat(safe, thresh_LM, thresh_MH, warmup_end)
    total = 0
    correct = 0
    for t in range(warmup_end, len(safe)):
        rt = str(regime_true[t]) if t < len(regime_true) else ""
        rh = pred[t]
        if rt not in ("L", "M", "H"):
            continue
        if rh == "warmup":
            continue
        total += 1
        if rh == rt:
            correct += 1
    return 0.0 if total == 0 else correct / total


def class_separability(
    degraded_sigma: np.ndarray,
    regime_true: list,
    warmup_end: int,
) -> float:
    """Kruskal-Wallis H statistic for degraded sigma grouped by true regime."""
    n = len(degraded_sigma)
    groups: dict[str, list[float]] = {"L": [], "M": [], "H": []}
    for t in range(warmup_end, n):
        val = float(degraded_sigma[t])
        if np.isnan(val):
            continue
        lab = str(regime_true[t]) if t < len(regime_true) else ""
        if lab in groups:
            groups[lab].append(val)

    arrays = [np.asarray(g) for g in groups.values() if len(g) > 0]
    if len(arrays) < 2:
        return 0.0
    flat = np.concatenate(arrays)
    if np.all(flat == flat[0]):
        return 0.0
    try:
        H, _ = stats.kruskal(*arrays)
    except ValueError:
        return 0.0
    return 0.0 if np.isnan(H) else float(H)


def threshold_overlap_rate(
    degraded_sigma: np.ndarray,
    thresh_LM: float,
    thresh_MH: float,
    warmup_end: int,
    band_pct: float = 0.05,
) -> float:
    """Fraction of post-warmup samples within ±band_pct of either threshold."""
    post = np.asarray(degraded_sigma, dtype=np.float64)[warmup_end:]
    post = post[~np.isnan(post)]
    if len(post) == 0:
        return 0.0
    lo_lm = thresh_LM * (1.0 - band_pct)
    hi_lm = thresh_LM * (1.0 + band_pct)
    lo_mh = thresh_MH * (1.0 - band_pct)
    hi_mh = thresh_MH * (1.0 + band_pct)
    in_lm = (post >= lo_lm) & (post <= hi_lm)
    in_mh = (post >= lo_mh) & (post <= hi_mh)
    return float((in_lm | in_mh).mean())


def nrmse(
    clean: np.ndarray,
    degraded: np.ndarray,
    mask: np.ndarray,
) -> float:
    """Normalised RMSE: sqrt(mean((c-d)^2)) / std(c), restricted to mask, NaN-safe."""
    c = np.asarray(clean)[mask]
    d = np.asarray(degraded)[mask]
    c, d = _drop_invalid(c, d)
    if len(c) < 2:
        return 0.0
    sd = float(np.std(c, ddof=0))
    if sd == 0.0:
        return 0.0
    rmse = float(np.sqrt(np.mean((c - d) ** 2)))
    return rmse / sd


def regime_crossing_rate(
    degraded_sigma: np.ndarray,
    thresh_LM: float,
    thresh_MH: float,
    warmup_end: int,
) -> float:
    """Fraction of consecutive post-warmup steps where rv_baseline regime label flips."""
    safe = np.asarray(degraded_sigma, dtype=np.float64).copy()
    nan_mask = np.isnan(safe)
    if nan_mask.any():
        safe[nan_mask] = 0.0
    pred = assign_regime_hat(safe, thresh_LM, thresh_MH, warmup_end)
    n = len(safe)
    transitions = 0
    counted = 0
    prev = None
    for t in range(warmup_end, n):
        cur = pred[t]
        if cur == "warmup":
            prev = None
            continue
        if prev is not None:
            counted += 1
            if cur != prev:
                transitions += 1
        prev = cur
    return 0.0 if counted == 0 else transitions / counted
