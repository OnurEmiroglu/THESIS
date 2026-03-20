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
