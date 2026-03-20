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
