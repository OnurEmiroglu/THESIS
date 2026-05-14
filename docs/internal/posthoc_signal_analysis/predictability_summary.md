# Regime Predictability From sigma_hat

## Scope

This diagnostic asks whether the categorical regime labels present in frozen synthetic artifacts are predictable from `sigma_hat` alone. The primary target is `regime_hat`, because that is the explicit categorical label used by the main regime-aware policies. `regime_true` is reported as a secondary reference.

## Data

- Unique WP2-style synthetic CSVs used: 11
- Post-warmup rows for primary classifier: 72,610
- Split: chronological 70/30 within each source CSV.
- Features: `sigma_hat` only.

## Main Results

- Best within-source `regime_hat` classifier: random_forest with accuracy 1.000, balanced accuracy 1.000, macro F1 1.000, and NMI 0.999.
- Best pooled-global `regime_hat` classifier: random_forest with balanced accuracy 0.752. The lower pooled score reflects source-specific calibration of the thresholded regime detector.
- Secondary `regime_true` reference: best balanced accuracy 0.865. This indicates that `sigma_hat` also tracks the latent synthetic volatility state, although the thesis claim concerns the observed categorical channel used by the policies.

## Interpretation

The primary result is consistent with the redundancy interpretation: once each synthetic source is calibrated on its own training portion, the observed categorical `regime_hat` channel is almost entirely recoverable from `sigma_hat` alone. This should be read as mechanistic support for overlap between the two observed signals, not as evidence that all latent regime information is absent.
