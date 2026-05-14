# PPO Action Explanation Test

## Scope

This analysis uses frozen WP5 curve CSVs and joins `sigma_hat` only when the run-level frozen WP2 snapshot matches the curve regime sequence. This avoids regenerating synthetic paths and limits the action explanation test to aligned curve/snapshot pairs.

## Data

- Accepted aligned curve files: 8
- Action rows after cleaning: 19,200
- Split: chronological 70/30 within each aligned run/seed/strategy curve.
- Estimator: small random forest regressor.

## Main Results

- Mean sigma-only R2 for `h`: 0.026; mean delta from adding regime: -0.002.
- Mean sigma-only R2 for `m`: -0.102; mean delta from adding regime: +0.003.
- Largest average Model B permutation features: sigma_hat (0.159), regime_M (0.086), regime_L (0.014).

## Interpretation

The action evidence is mixed. The simple sigma-only models explain some half-spread variation in selected aligned curves, but they do not explain skew reliably and they do not establish that PPO actions are largely determined by `sigma_hat` alone. The more stable finding is incremental: adding regime dummies after `sigma_hat` changes held-out action R2 only modestly in these aligned curve/snapshot pairs. Because this is a post-hoc approximation to trained PPO actions, it should not be described as a causal mechanism proof.

## Alignment Caveat

Only curves whose `regime_hat` sequence matched the frozen WP2 snapshot at >= 99.5% were used. Other curve files remain untouched but were excluded because their per-seed `sigma_hat` path is not present as a frozen curve-level column.
