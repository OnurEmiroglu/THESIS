# Incremental Predictive Value After sigma_hat

## Scope

The predictive target is next-step absolute mid return in ticks, `abs(ret[t+1]) / tick_size`. Features are measured at time `t`, so the target is forward-looking while the regressors remain contemporaneously observed.

## Design

- Model A: `future_abs_return_ticks ~ sigma_hat`.
- Model B: `future_abs_return_ticks ~ sigma_hat + regime_hat`.
- Split: chronological 70/30 within each source CSV.
- Estimator: OLS on the training split, evaluated out of sample on the held-out tail.

## Main Results

- OOS R2 changes by +0.000159 when `regime_hat` is added after `sigma_hat`.
- MAE changes by +0.000103; RMSE changes by -0.000031.
- Nested training-set F-test p-value for the regime terms: 0.0003455.

## Interpretation

The relevant evidence is the held-out predictive change, not only the training significance of extra step-function terms. Small OOS deltas support the view that, for this synthetic setting and target, the explicit label adds limited incremental predictive content once `sigma_hat` is observed.
