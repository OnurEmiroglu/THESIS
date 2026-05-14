# Final Signal Redundancy Assessment

## Bottom Line

The post-hoc diagnostics strengthen the cautious signal-redundancy interpretation, mainly through the classifier and incremental-prediction tests. In the tested synthetic setting, the observed categorical regime channel is highly predictable from source-calibrated `sigma_hat` and adds limited held-out predictive value for next-step absolute returns after `sigma_hat`. The action explanation test is more mixed: it does not show that `sigma_hat` alone explains PPO actions broadly, but it does show little additional explanatory gain from adding regime labels in the aligned frozen curves.

## Evidence Added Here

- Classifier evidence: best within-source `regime_hat` from `sigma_hat` alone achieved accuracy 1.000, balanced accuracy 1.000, macro F1 1.000, and NMI 0.999. In the pooled-global setting, the best balanced accuracy was 0.752.
- Incremental predictive value: adding `regime_hat` after `sigma_hat` changed OOS R2 by +0.000159, MAE by +0.000103, and RMSE by -0.000031 for next-step absolute mid return.
- Action explanation: across aligned frozen PPO curves, mean sigma-only R2 was 0.026 for `h` and -0.102 for `m`; adding regime changed mean R2 by -0.002 for `h` and +0.003 for `m`. This is weak evidence for sigma-only action explanation, but supportive evidence that the explicit label has limited incremental action-explanatory value in the aligned subset.

## Connection To Existing WP5/WP6 Evidence

- WP5 main OOS means: ppo_aware 0.715, ppo_blind 0.740.
- WP5 ablation means: sigma_only 0.753, combined 0.696, regime_only 0.698, oracle_full 0.722.
- WP5 misspec mild means: sigma_only 0.686, combined 0.651, regime_only 0.634, oracle_full 0.682.
- WP6 full-condition means are sigma_only 0.763 and combined 0.690; the mean paired combined-minus-sigma difference across informative conditions is -0.077.

## Contradictory Or Limiting Evidence

The main contradictory note is the action test: sigma-only models do not explain PPO actions broadly, especially skew. This tempers any action-level mechanistic claim. The aligned action analysis is also limited to curve/snapshot pairs with exact frozen alignment, so it is best treated as supportive rather than exhaustive.

## Defense-Safe Interpretation

These results are consistent with the view that most policy-relevant and predictive structure conveyed by the observed categorical regime channel may already be embedded in `sigma_hat`. The action evidence should be framed more narrowly: explicit labels appear to add little after `sigma_hat` in the aligned post-hoc action regressions, but sigma-only action determination is not established. These diagnostics do not show that regime labels contain zero information, and they do not identify a causal PPO learning mechanism.

## Suggested Thesis Wording

In the tested synthetic setting, post-hoc diagnostics indicate that the observed categorical regime labels are highly recoverable from source-calibrated `sigma_hat` and add only limited held-out predictive value once `sigma_hat` is observed. In aligned post-hoc action regressions, explicit labels also provide little additional explanatory gain beyond `sigma_hat`, although the simple sigma-only action models do not fully explain PPO action variation. Together with the WP5/WP6 policy results, this supports the interpretation that most economically relevant regime structure available to the policies may already be embedded in the continuous volatility signal, while leaving open the possibility that explicit labels could matter in settings where `sigma_hat` is weaker, differently calibrated, or unavailable.

## Audit Notes

- Unique WP2 synthetic CSVs read: 11.
- Accepted aligned action curves: 8.
- No PPO model was retrained.
- No WP5/WP6 experiment was rerun.
- No protected CSV or protected figure artifact was modified.
