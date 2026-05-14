# Project Full Notes - 13 May 2026

Purpose: one high-density project brain for ChatGPT project upload context under a 25-file limit. This file consolidates the final thesis position, canonical numerical evidence, statistical conclusions, pipeline design, audit-remediation state, and upload priorities.

Source precedence:

- Primary base: `docs/internal/project_full_notes_18april.md`.
- Merged current sources: `manuscript/thesis_28.pdf`, `manuscript/decisions_log_12.pdf`, `EVIDENCE_MANIFEST.md`, `docs/wp5/wp5_notes.md`, `docs/wp6/wp6_notes.md`, `docs/wp2/wp2_notes.md`, `README.md`, `CLAUDE.md`.
- Concise checks from protected CSV summaries and canonical metrics outputs were used only to preserve final numbers. No experiment was rerun and no raw CSV content is dumped here.

## 1. Executive Summary

| Topic | Final state |
|---|---|
| Thesis question | Does explicit volatility-regime information improve PPO market-making when `sigma_hat` is already observed? |
| Core answer | No robust advantage was found. The stronger final claim is signal redundancy: `sigma_hat` already carries the economically useful volatility information, so an explicit regime label adds little or can interfere. |
| Main WP5 OOS result | PPO-aware Sharpe 0.714826 vs PPO-blind 0.740370; paired t-test Sharpe p=0.261, final equity p=0.023 favoring blind. |
| Strongest equivalence evidence | Five-variant ablation: `ppo_sigma_only` Sharpe 0.752987 vs `ppo_oracle_full` 0.722443; classical p=0.115; TOST +/-0.10 p=0.00067, 90% CI [-0.001, +0.063]. |
| Detector robustness | Null result is stable under `rv_baseline`, `rv_dwell`, and HMM; ANOVA across detector-specific PPO-aware Sharpe: F=0.0034, p=0.9966. |
| Misspecification | Mild regime-dependent execution parameters still support equivalence: `sigma_only` 0.685509 vs `oracle_full` 0.681666; p=0.881; TOST +/-0.05 p=0.042. |
| WP6 extension | Progressive degradation of `sigma_hat` did not reveal a regime-label advantage. `combined` is below `sigma_only` in all informative conditions. |
| Audit-remediation | Lane A/B/C remediation completed through commit `045ee86`; protected CSV evidence remained 4/4 SHA256 MATCH after each Lane C commit. |

The thesis is not "PPO beats all baselines on every metric." It is: PPO learns much better risk-adjusted quoting than naive/AS in this synthetic setup, while explicit regime labels do not improve PPO beyond the continuous volatility signal already in the observation.

## 2. Final Thesis Claim

Final claim suitable for defense:

> In a synthetic high-frequency market-making environment with Markov volatility regimes, a PPO agent using a continuous realized-volatility signal learns strong risk-adjusted quoting behavior, but adding an explicit categorical regime label does not produce a reliable out-of-sample performance improvement. Across detector robustness checks, oracle labels, reward-shaping variants, misspecification, and a WP6 signal-informativeness sweep, the evidence supports a signal-redundancy interpretation: the regime label mostly repackages information already present in `sigma_hat`.

Important boundaries:

- This is a synthetic-market thesis, not a live-market trading claim.
- The result does not say regimes are irrelevant in finance; it says the explicit label adds little once the policy already sees a continuous volatility proxy.
- The strongest statistical support is not merely "p > 0.05"; it is TOST equivalence for the key `sigma_only` vs `oracle_full` comparison under preselected practical bounds.
- WP6 rejects the original informativeness-threshold hypothesis within the tested calibration band; it does not prove a universal result for every possible degradation of `sigma_hat`.

## 3. Final Numerical Results

### 3.1 Main WP5 OOS Run

Canonical source: `results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc/metrics_wp5_oos.csv`.

Setup: 20 seeds, 70/30 chronological train/test split, 1M PPO training timesteps per model, deterministic OOS evaluation on the test segment, `rv_baseline` detector.

| Strategy | Mean Sharpe-like | Mean final equity | Mean inv_p99 | Mean fill rate | Interpretation |
|---|---:|---:|---:|---:|---|
| `ppo_aware` | 0.714826 | 4.101425 | 2.000000 | 0.236229 | Regime label + sigma_hat |
| `ppo_blind` | 0.740370 | 4.420605 | 2.050000 | 0.232167 | sigma_hat, no regime one-hot |
| `AS` | 0.104879 | 5.050361 | 29.950000 | 0.444229 | Higher raw equity, much larger inventory risk |
| `naive` | 0.126457 | 4.489891 | 21.200000 | 0.119396 | Fixed half-spread baseline |

Statistical tests:

| Comparison | Metric | Result |
|---|---|---|
| `ppo_aware` vs `ppo_blind` | Sharpe-like | paired t-test p=0.261, inconclusive |
| `ppo_aware` vs `ppo_blind` | final equity | paired t-test p=0.023, favors `ppo_blind` |

Defense reading: PPO improves risk-adjusted behavior substantially over AS/naive, while AS can produce higher raw equity by carrying much larger inventory risk. The regime-aware PPO does not beat the blind PPO.

### 3.2 Five-Variant Ablation

Canonical source: `results/runs/20260327-171914_seed1_wp5-ablation_e1545a5/metrics_wp5_oos_combined.csv`.

| Variant | Observation meaning | Mean Sharpe-like | Mean final equity | Mean inv_p99 |
|---|---|---:|---:|---:|
| `ppo_sigma_only` | continuous `sigma_hat` only | 0.752987 | 4.547923 | 1.950000 |
| `ppo_oracle_full` | `sigma_hat` + true regime one-hot | 0.722443 | 4.067945 | 2.050000 |
| `ppo_regime_only` | estimated regime one-hot only | 0.697552 | 4.005379 | 2.150000 |
| `ppo_combined` | `sigma_hat` + estimated regime one-hot | 0.696182 | 3.905214 | 1.800000 |
| `ppo_oracle_pure` | true regime one-hot only | 0.683829 | 3.925499 | 1.950000 |
| `naive` | fixed spread | 0.126457 | 4.489891 | 21.200000 |
| `AS` | Avellaneda-Stoikov | 0.104879 | 5.050361 | 29.950000 |

Key tests:

| Comparison | Metric | Result |
|---|---|---|
| `ppo_sigma_only` vs `ppo_oracle_full` | Sharpe-like | classical paired t-test p=0.115 |
| `ppo_sigma_only` vs `ppo_oracle_full` | TOST, +/-0.10 | p=0.00067; 90% CI [-0.001, +0.063]; 95% CI [-0.008, +0.069] |
| `ppo_oracle_full` vs `ppo_combined` | Sharpe-like | p=0.301; this is not the main oracle-vs-sigma comparison |

Main interpretation: even perfect regime labels do not beat `sigma_hat` alone. This is the "oracle paradox" supporting signal redundancy.

### 3.3 Regime-Conditional Eta Run

Canonical source: `results/runs/20260330-155235_seed42_w5-eta-regime_af82a9f/metrics_wp5_oos.csv`.

Purpose: test whether regime labels become useful when the reward explicitly changes inventory penalty by regime (`eta_H = 5 x eta_L` design).

| Variant | Mean Sharpe-like | Mean final equity | Mean inv_p99 |
|---|---:|---:|---:|
| `ppo_sigma_only` | 0.714095 | 3.911864 | 1.800000 |
| `ppo_oracle_full` | 0.638290 | 3.383032 | 1.850000 |
| `ppo_combined` | 0.629076 | 3.499248 | 1.800000 |
| `ppo_oracle_pure` | 0.577552 | 3.446693 | 2.500000 |
| `ppo_regime_only` | 0.512642 | 3.070189 | 13.150000 |

Key tests:

- `ppo_sigma_only` beats `ppo_combined` on Sharpe-like: p=0.0016.
- Equity comparison also favors `sigma_only`: p=0.008.

Interpretation: making the reward regime-conditional still did not make the explicit regime channel useful; it strengthened the signal-redundancy argument.

### 3.4 Mild Model Misspecification

Canonical source: `results/runs/20260408-160248_seed1_w5-misspec-mild_5d9dc23/metrics_wp5_oos.csv`.

Misspecification: execution parameters vary by true regime:

| Regime | A | k |
|---|---:|---:|
| L | 4.0 | 1.8 |
| M | 5.0 | 1.5 |
| H | 6.0 | 1.2 |

Results:

| Variant | Mean Sharpe-like | Mean final equity | Mean inv_p99 |
|---|---:|---:|---:|
| `ppo_sigma_only` | 0.685509 | 4.306224 | 2.000000 |
| `ppo_oracle_full` | 0.681666 | 4.230066 | 2.150000 |
| `ppo_combined` | 0.651019 | 3.968368 | 1.800000 |
| `ppo_regime_only` | 0.634151 | 3.229698 | 8.400000 |
| `ppo_oracle_pure` | 0.602243 | 3.761956 | 2.200000 |

Key tests:

| Comparison | Result |
|---|---|
| `sigma_only` vs `oracle_full` classical t-test | p=0.881 |
| `sigma_only` vs `combined` classical t-test | p=0.217 |
| `sigma_only` vs `oracle_pure` classical t-test | p=0.098 |
| TOST +/-0.05, `sigma_only` vs `oracle_full` | p=0.042; 90% CI [-0.040, +0.048]; 95% CI [-0.049, +0.057]; Cohen's d=0.034 |
| TOST +/-0.10, same comparison | p=0.00067 |

Interpretation: under mild regime-dependent execution misspecification, `sigma_only` and `oracle_full` remain practically equivalent. Stronger misspecification was left as future work.

## 4. Statistical Conclusions

| Question | Evidence | Conclusion |
|---|---|---|
| Does adding estimated regime labels improve PPO over blind PPO? | Main OOS: Sharpe p=0.261; equity p=0.023 favors blind. | No supported improvement. |
| Is the null result due to poor detector quality? | Detector robustness: rv_baseline p=0.1142, rv_dwell p=0.1095, HMM p=0.0822; ANOVA F=0.0034, p=0.9966. | No; result is stable across detector choices, including HMM at 81.8% accuracy. |
| Does perfect true-regime information help? | `sigma_only` 0.752987 vs `oracle_full` 0.722443; p=0.115; TOST +/-0.10 p=0.00067. | Perfect regime labels do not beat `sigma_hat`; practical equivalence is supported. |
| Does reward shaping reveal regime value? | Regime-conditional eta: `sigma_only` beats `combined`, p=0.0016. | No; reward-channel test still favors `sigma_hat` alone. |
| Does mild model misspecification reveal regime value? | `sigma_only` 0.685509 vs `oracle_full` 0.681666; p=0.881; TOST +/-0.05 p=0.042. | No; practical equivalence holds under mild misspecification. |
| Does WP6 support the informativeness-threshold hypothesis? | `sigma_only` remains flat and above `combined` under full/noisy/lagged/coarsened. | No within the tested calibration band; evidence points toward categorical-channel degradation/interference. |

TOST convention:

- For equivalence claims, TOST at alpha=0.05 corresponds to the 90% CI lying inside the equivalence bounds.
- WP5 uses TOST to support practical equivalence.
- WP6 uses TOST in two ways: non-equivalence for `combined` vs `sigma_only`, and equivalence testing for `combined` vs `regime_only`.

## 5. WP-by-WP Architecture Summary

| WP | Role | Final status | Decision-relevant notes |
|---|---|---|---|
| WP0 | Project skeleton, run context, logging, dispatcher | Done | `run.py` dispatches by `cfg["job"]`; `RunContext` creates run dirs, snapshots config, logs metadata, and now enforces safer resume/config behavior. |
| WP1 | Market simulator and baselines | Done | Poisson fill intensity `lambda(delta)=A*exp(-k*delta)`, arithmetic Brownian mid, fees and latency, naive and Avellaneda-Stoikov baselines. |
| WP2 | Synthetic regimes and detectors | Done | Three-state Markov L/M/H volatility process; rolling RV detector, dwell-filter variant, HMM detector. Main pipelines use causal `rv_baseline`; dwell filter is auxiliary/offline. |
| WP3 | Gymnasium market-making environment | Done | Observation `[q_norm, sigma_hat, tau, regime_L, regime_M, regime_H]`; action half-spread/skew; reward `delta_equity - eta * inventory^2`; no fee double count. |
| WP4 | PPO pilot/infrastructure training | Done | Pilot/in-sample infrastructure only; not the source of reported OOS PPO numbers. |
| WP5 | Main OOS evaluation and robustness | Done | Main 4-strategy OOS, detector robustness, five-variant ablation, eta-regime, misspecification, TOST equivalence. |
| WP5.5 | Offline signal-degradation calibration audit | Done | Calibrated WP6 degradation choices and found monotonicity caveat; no PPO training in audit. |
| WP6 | Signal-informativeness sweep | Done | 480 trained cells; tests whether regime labels become useful as `sigma_hat` degrades. Result: original threshold hypothesis not supported. |

## 6. Canonical Configurations

### 6.1 Shared Market and Execution Parameters

| Block | Parameter | Value |
|---|---|---:|
| market | `mid0` | 100.0 |
| market | `tick_size` | 0.01 |
| market | `dt` | 0.2 |
| market | `sigma_mid_ticks` | 0.8 |
| execution | `A` | 5.0 |
| execution | `k` | 1.5 |
| execution | `fee_bps` | 0.2 |
| execution | `latency_steps` | 1 |
| episode | `n_steps` | 8000 |
| episode | `inv_max_clip` | 50 |

### 6.2 Regime Process

| Parameter | Value |
|---|---|
| `rv_window` | 50 |
| `warmup_steps` | 1000 |
| `sigma_mid_ticks_base` | 0.8 |
| `sigma_mult` | [0.6, 1.0, 1.8] |
| Transition row L | [0.9967, 0.0023, 0.0010] |
| Transition row M | [0.0042, 0.9917, 0.0041] |
| Transition row H | [0.0010, 0.0030, 0.9960] |

Expected regime durations are much longer than the RV window, avoiding the early timescale-mismatch failure mode.

### 6.3 PPO Hyperparameters

| Parameter | Value |
|---|---:|
| total timesteps | 1,000,000 |
| learning rate | 0.0003 |
| `n_steps` | 2048 |
| batch size | 256 |
| epochs | 10 |
| gamma | 0.999 |
| GAE lambda | 0.95 |
| clip range | 0.2 |
| entropy coefficient | 0.01 |
| device | CPU |

### 6.4 Canonical Config Files

| Config | Purpose | Key seed set |
|---|---|---|
| `config/w5_main.json` | Main OOS evaluation | seeds 1-20 |
| `config/w5_detector_full.json` | Detector robustness | seeds 1-20 |
| `config/w5_eta_regime.json` | Regime-conditional eta | seeds 1-20 |
| `config/w5_misspec_mild.json` | Mild model misspecification | seeds 1-20 |
| `config/w55_audit.json` | Offline degradation calibration audit | seed 123 |
| `config/w6_sweep_full.json` | WP6 signal-informativeness sweep | seeds 42-61 |

WP6 degradation parameters:

| Condition | Parameterization |
|---|---|
| `full` | unmodified informative `sigma_hat` |
| `noisy` | `noisy_alpha` = 0.40 |
| `lagged` | `lagged_k` = 20 |
| `coarsened` | `coarsened_n_bins` = 5 |
| `none` | `sigma_hat` removed/zeroed where applicable |

## 7. Detector Results

### 7.1 WP2 Detector Accuracy

| Detector | Method | Accuracy | Notes |
|---|---|---:|---|
| `rv_baseline` | rolling RV threshold at warmup percentiles | 60.7% | Main causal detector for WP4/WP5/WP6. |
| `rv_dwell` | rolling RV plus dwell filter | 60.4% | Auxiliary/offline detector comparison; dwell logic can use future segment structure. |
| `hmm` | GaussianHMM fit on warmup `sigma_hat`, states mapped by variance | 81.8% | Higher accuracy but still does not create regime-label PPO advantage. |

### 7.2 Detector Robustness Full Run

Canonical sources: `results/metrics_detector_compare.csv` and `results/stats_detector_robustness.txt`.

| Detector | Aware Sharpe | Blind Sharpe | Diff | Sharpe p | Final-equity p | Detector accuracy |
|---|---:|---:|---:|---:|---:|---:|
| `rv_baseline` | 0.7182 | 0.7530 | -0.0348 | 0.1142 | 0.0010 | 60.7% |
| `rv_dwell` | 0.7155 | 0.7530 | -0.0374 | 0.1095 | 0.0133 | 60.4% |
| `hmm` | 0.7186 | 0.7530 | -0.0344 | 0.0822 | 0.0213 | 81.8% |

ANOVA on `ppo_aware` Sharpe across detector choices: F=0.0034, p=0.9966.

Interpretation: detector choice does not explain the null result. Even HMM's higher classification accuracy does not translate into a material PPO advantage.

## 8. Ablation Results

| Ablation | Question | Final result |
|---|---|---|
| Eta sweep | What inventory penalty balances PnL and inventory risk? | `eta=0.001` selected; too low creates inventory blow-up; too high makes policy passive. |
| Action analysis | Do aware and blind policies behave very differently? | Only limited differences; both keep half-spread roughly in the same learned band in canonical analysis. |
| Five-variant ablation | Is `sigma_hat` or regime label carrying the signal? | `sigma_only` highest Sharpe; `oracle_full` does not beat it; practical equivalence supported by TOST. |
| Regime-conditional eta | Does regime-specific reward shaping make labels useful? | No; `sigma_only` beats `combined` on Sharpe, p=0.0016. |
| Oracle labels | Does perfect regime information help? | No reliable benefit over `sigma_hat`; this is the strongest signal-redundancy evidence. |

Most important ablation statement for thesis: explicit categorical regime information, even when true, does not improve the policy beyond the continuous volatility proxy already observed.

## 9. Misspecification Results

Mild misspecification changes execution parameters by true regime, so the environment is no longer execution-homogeneous. This directly tests whether regime labels become valuable when fill behavior itself is regime dependent.

| Evidence | Result |
|---|---|
| Mean Sharpe: `sigma_only` vs `oracle_full` | 0.685509 vs 0.681666 |
| Classical t-test | p=0.881 |
| TOST +/-0.05 | p=0.042; 90% CI [-0.040, +0.048] |
| Cohen's d | 0.034 |
| Thesis interpretation | Signal redundancy persists under mild misspecification. |

Important limitation: stronger misspecification was not run and should remain future work rather than being implied by the current evidence.

## 10. WP6 Signal Informativeness Sweep

Canonical run: `20260426-105115_seed42_wp6-sweep-full_ce849a0`.

Scale: 480 trained/evaluated cells, 5 degradation conditions x 5 variants x 20 seeds, except `sigma_only` is undefined under `condition=none`.

### 10.1 Mean Sharpe-like by Condition and Variant

Source: `docs/internal/wp6_sweep_full/summary_condition_variant.csv`.

| condition | `sigma_only` | `combined` | `regime_only` | `oracle_full` | `oracle_pure` |
|---|---:|---:|---:|---:|---:|
| full | 0.7626 | 0.6898 | 0.6991 | 0.6811 | 0.6632 |
| noisy | 0.7563 | 0.7125 | 0.6991 | 0.6736 | 0.6632 |
| lagged | 0.7822 | 0.6812 | 0.6991 | 0.7264 | 0.6632 |
| coarsened | 0.7827 | 0.6908 | 0.6991 | 0.7447 | 0.6632 |
| none | n/a | 0.6991 | 0.6991 | 0.6632 | 0.6632 |

Readings:

- `sigma_only` remains high and essentially flat across informative degradation conditions.
- `combined` sits below `sigma_only` in all four informative conditions by about 0.04 to 0.10 Sharpe-like.
- `combined` collapses to `regime_only` under `none`, as designed.
- `regime_only` and `oracle_pure` are condition-invariant anchors because they do not consume `sigma_hat`.

### 10.2 Paired Combined vs Sigma-Only

Source: `docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv`. Diff = `combined - sigma_only`.

| condition | n below | mean diff | paired t p | Cohen's dz | TOST p | non-equivalence at alpha=0.05? |
|---|---:|---:|---:|---:|---:|---|
| full | 15/20 | -0.072783 | 0.012032 | -0.620763 | 0.197844 | No |
| noisy | 15/20 | -0.043740 | 0.020040 | -0.567633 | 0.639807 | No |
| lagged | 18/20 | -0.100976 | 0.000639 | -0.912177 | 0.026713 | Yes |
| coarsened | 15/20 | -0.091880 | 0.008758 | -0.653228 | 0.099378 | No |

Interpretation:

- Direction is robust: `combined` is below `sigma_only` in 15-18 of 20 seeds for every informative condition.
- Paired t-tests are significant in all four conditions.
- Practical non-equivalence at delta=0.05 is formally established only for `lagged`.
- Recommended phrasing: "directionally shifted below sigma_only"; avoid overstating practical non-equivalence for all panels.

### 10.3 Paired Combined vs Regime-Only

Source: `docs/internal/wp6_sweep_full/summary_paired_combined_vs_regime.csv`. Diff = `combined - regime_only`.

| condition | n above | mean diff | paired t p | Cohen's dz | TOST p | equivalence at alpha=0.05? |
|---|---:|---:|---:|---:|---:|---|
| full | 9/20 | -0.009344 | 0.790586 | -0.060222 | 0.127872 | No |
| noisy | 7/20 | 0.013416 | 0.684535 | 0.092255 | 0.137278 | No |
| lagged | 11/20 | -0.017916 | 0.535007 | -0.141289 | 0.135952 | No |
| coarsened | 10/20 | -0.008319 | 0.813729 | -0.053423 | 0.123004 | No |

Interpretation:

- Mean differences are tiny (absolute mean diff <= 0.018), so "combined clearly improves on regime_only" is rejected.
- Formal equivalence at delta=0.05 is not established; the test is underpowered at n=20 with observed std_diff around 0.13-0.16.
- Conservative statement: `combined` is indistinguishable in mean from `regime_only` within roughly a +/-0.07 band, but not formally equivalent at +/-0.05.

### 10.4 WP6 Final Interpretation

Original hypothesis: as `sigma_hat` is degraded, the categorical regime label should become more useful and the `sigma_only` vs `combined` gap should narrow.

Observed: gap does not narrow in the expected direction. `sigma_only` remains strong; `combined` is often worse. This supports a refined descriptive interpretation: the categorical channel can degrade or interfere with the continuous volatility signal under the tested setup. Mechanism is not identified; plausible mechanisms include gradient interference, crowd-out, or PPO local-optimum differences.

## 11. Audit & Remediation Summary

Canonical audit-remediation record: `manuscript/decisions_log_12.pdf` and `EVIDENCE_MANIFEST.md`.

### 11.1 Lane A - Audit Interpretation and Scientific Clarification

| Item | Resolution |
|---|---|
| C1 dwell-filter look-ahead | Auxiliary detector comparison only. Main WP4/WP5/WP6 pipelines use causal `rv_baseline`. |
| C2 WP4 same-series train/eval | WP4 is pilot/infrastructure only. Reported PPO numbers come from WP5 70/30 OOS evaluation. |
| C3 WP6 noisy sigma calibration | Small noisy-only scale issue documented as caveat; no rerun performed. |

### 11.2 Lane B - Engineering Hardening

| Commit | Remediation |
|---|---|
| `26beecd` | `CSVMetricLogger` schema consistency fix. |
| `a63e640` | Resume config snapshot validation; mismatch requires explicit force/override. |
| `ffe8d90` | `.gitattributes` plus LF materialization for CSV/TXT audit stability. |
| `78df148` | `scripts/office/unpack.py` safe-root/path-validation guards, present before the final Lane C manifest chain. |

### 11.3 Lane C - Active-Code and Provenance Remediation

| Commit | Remediation |
|---|---|
| `0ed125e` | Clarified ANOVA framing in `stats_detector_robustness.py`. |
| `43ad288` | Clarified `figure_thesis.py` and `figure_thesis_23.py` ownership headers and WP6 boundary. |
| `5ac5bcb` | Moved historical thesis and decisions-log generators to `scripts/legacy/` with README. |
| `dca37b6` | Parameterized hardcoded run paths in `src/wp5/figure_thesis.py`, `src/wp5/figure_thesis_23.py`, and `scripts/eval_only_seed1to7.py` with byte-identical argparse defaults. |
| `e0c47c5` | Standardized WP2 per-run provenance artifact naming in `src/wp2/synth_regime.py`. |
| `1c259cd` | Added `decisions_log_12` audit-remediation record. |
| `045ee86` | Added `EVIDENCE_MANIFEST.md` for the audit-remediation chain. |

### 11.4 Protected Evidence Artifacts

| Artifact | SHA256 |
|---|---|
| `results/metrics_detector_compare.csv` | `28E7AD40BB47214F8576132846E9E1D4CD643F623CF1187743091FC367A206ED` |
| `docs/internal/wp6_sweep_full/summary_condition_variant.csv` | `6DD627E81637A49A60163F58AC1D3EF23B8D694E39AC55BA64FBF808E978C6EA` |
| `docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv` | `4BABCAAACE1DD5228C674E2CED9D977236F8D3ACB503C098FAEB06FF6C10B796` |
| `docs/internal/wp6_sweep_full/summary_paired_combined_vs_regime.csv` | `2087FEFBE5DC39AF23372EA2D8999AC0F1071D0FEE90BC1B3668F2158130E8F9` |

Audit invariants:

- All Lane C remediation commits preserved 4/4 SHA256 MATCH on the protected set.
- No experiments were rerun during audit remediation.
- No CSV/PNG result artifacts were regenerated.
- `thesis_28` numerical claims were not rerun or regenerated during remediation.
- `scripts/eval_only_seed1to7.py` was never executed during remediation.

## 12. Reproducibility Infrastructure

| Component | Reproducibility role |
|---|---|
| `run.py` | Single dispatcher for config-driven jobs. |
| `src/run_context.py` | Creates timestamped run directories, logs, config snapshots, metadata, status, and CSV metrics. |
| Run ID format | `YYYYMMDD-HHMMSS_seed<S>_<TAG>_<COMMIT>`. |
| Config snapshots | Each run captures the exact config used; resume now validates snapshot mismatch. |
| `CSVMetricLogger` | Stable schema behavior prevents silent CSV column drift. |
| `.gitattributes` | CSV/TXT line-ending policy supports stable hash-based audit. |
| WP2 artifacts | Global `data/processed/wp2_synth.csv` remains latest convenience snapshot; `ctx.run_dir/wp2_synth.csv` is the per-run provenance artifact. |
| Historical archive | `scripts/legacy/` preserves old generators for provenance/history, not active pipeline execution. |

No-arg behavior invariant: active path-parameterization fixes were designed so argparse defaults equal the previous hardcoded strings byte-for-byte.

## 13. Important Known Caveats

| Caveat | Status / defense handling |
|---|---|
| Synthetic environment | Thesis claims are about the constructed HFMM simulator, not live-market deployment. |
| Regime labels may matter elsewhere | The claim is conditional: explicit labels add little when `sigma_hat` is already available in this observation design. |
| WP4 in-sample evaluation | WP4 is infrastructure/pilot only; do not cite it for reported OOS PPO performance. |
| Dwell filter causality | `rv_dwell` is auxiliary/offline detector comparison; main reported pipelines use causal `rv_baseline`. |
| WP3 warmup observation | During warmup, unavailable `sigma_hat` maps to 0.0 and warmup regime handling can produce a medium one-hot signal; documented limitation. |
| WP6 noisy calibration | Small noisy-only scale issue documented; no rerun; does not change protected evidence. |
| WP6 mechanism | "Categorical-channel degradation" is descriptive, not a proven mechanism. Avoid claiming representation-level causality. |
| WP6 equivalence vs `regime_only` | Formal TOST equivalence at delta=0.05 is not established; use conservative mean-indistinguishability language. |
| Strong misspecification | Not run; leave as future work. |
| README/CLAUDE stale markers | Useful for architecture but still mention older manuscript names in places; prefer `thesis_28`, `decisions_log_12`, and this notes file for final state. |

## 14. Final Defense Narrative

Recommended defense spine:

1. Build credibility: start with a realistic market-making simulator, AS/naive baselines, fees, latency, inventory risk, and PPO policies evaluated OOS.
2. Establish performance: PPO delivers much higher risk-adjusted Sharpe-like performance than classical baselines, while AS's higher raw equity comes with much larger inventory exposure.
3. State the surprise: making PPO regime-aware does not improve OOS performance over a blind PPO that still sees `sigma_hat`.
4. Show it is not a weak null: detector robustness, HMM, oracle labels, TOST equivalence, eta-regime reward shaping, and misspecification all support signal redundancy.
5. Use WP6 to refine, not overextend: degradation tests did not reveal a threshold where categorical labels become useful; instead, the combined channel often underperforms `sigma_only`.
6. Close with scientific humility: the result is conditional on this simulator, signal design, PPO setup, and degradation calibration, but internally consistent and audit-stable.

One-sentence defense answer:

> The regime label did not fail because regimes were impossible to detect; it failed because the continuous volatility signal already gave the policy the information the discrete label was supposed to provide.

## 15. Final Repository State

| Area | State |
|---|---|
| Latest pushed remediation commit before this notes file | `045ee86 Lane-C: add evidence manifest for audit-remediation chain` |
| Audit status | Audit-ready and provenance-improved. |
| Numerical evidence | Protected CSV evidence frozen and hash-verified. |
| Thesis artifacts | `thesis_28` was not regenerated during remediation. |
| Decision record | `decisions_log_12` contains Decisions #48-#51 and summary-row expansion. |
| Evidence manifest | Present and committed at `045ee86`. |
| Current new artifact | This file, `docs/internal/project_full_notes_13may.md`, is a context-consolidation document and does not change experiment evidence. |

This consolidated notes file intentionally replaces many individual run-result files for ChatGPT upload context, while preserving the most important numerical and procedural facts needed for thesis decisions.

# Recommended ChatGPT Upload Set

Use this 25-file set for the ChatGPT project folder. The purpose is not to reproduce every run locally inside ChatGPT, but to provide enough current manuscript, evidence, code, config, and audit context for accurate final-thesis decisions.

| Rank | File path | Why this file is needed | Category |
|---:|---|---|---|
| 1 | `docs/internal/project_full_notes_13may.md` | Consolidated project brain with final results, p-values, caveats, audit state, and upload logic. | Master context |
| 2 | `manuscript/thesis_28.pdf` | Latest thesis manuscript as defended/read by humans. | Manuscript |
| 3 | `manuscript/decisions_log_12.pdf` | Latest decisions log including audit-remediation Decisions #48-#51. | Decision log |
| 4 | `EVIDENCE_MANIFEST.md` | Defense-grade manifest for protected artifacts, invariants, and remediation commits. | Audit manifest |
| 5 | `README.md` | Project overview, research question, command entry points, and key results; note stale manuscript markers. | Project guide |
| 6 | `CLAUDE.md` | Architecture, work-package, command, and coding guidance for AI/code context; note stale manuscript markers. | Project guide |
| 7 | `scripts/gen_thesis_28.py` | Active thesis generator corresponding to the latest manuscript. | Manuscript generation |
| 8 | `run.py` | Main config-driven dispatcher for all jobs. | Infrastructure |
| 9 | `src/run_context.py` | Run directories, config snapshots, metadata, CSVMetricLogger, resume guards. | Infrastructure |
| 10 | `src/wp1/sim.py` | Core simulator: mid dynamics, Poisson fills, fees, latency, inventory state. | Active code |
| 11 | `src/wp2/synth_regime.py` | Synthetic regimes, detectors, causal/offline notes, WP2 provenance artifact behavior. | Active code |
| 12 | `src/wp3/env.py` | Gym environment, observation/action/reward definitions, no fee double count. | Active code |
| 13 | `src/wp4/job_w4_ppo.py` | PPO training infrastructure and WP4 pilot boundary. | Active code |
| 14 | `src/wp5/job_w5_eval.py` | Main WP5 OOS evaluation and strategy comparison logic. | Active code |
| 15 | `src/wp6/job_w6_sweep_full.py` | WP6 signal-informativeness sweep implementation and calibration comments. | Active code |
| 16 | `src/wp5/figure_thesis.py` | Active figure generation for thesis figures 1-5 with current ownership header. | Figure code |
| 17 | `src/wp5/figure_thesis_23.py` | Active figure generation for thesis figures 6-9 with WP6 boundary notes. | Figure code |
| 18 | `config/w5_main.json` | Canonical main WP5 OOS configuration. | Config |
| 19 | `config/w6_sweep_full.json` | Canonical WP6 full sweep configuration. | Config |
| 20 | `config/w55_audit.json` | Offline signal-degradation calibration audit configuration. | Config |
| 21 | `results/metrics_detector_compare.csv` | Protected detector robustness evidence artifact. | Protected evidence |
| 22 | `docs/internal/wp6_sweep_full/summary_condition_variant.csv` | Protected WP6 condition-variant summary evidence. | Protected evidence |
| 23 | `docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv` | Protected WP6 paired combined-vs-sigma evidence. | Protected evidence |
| 24 | `docs/internal/wp6_sweep_full/summary_paired_combined_vs_regime.csv` | Protected WP6 paired combined-vs-regime evidence. | Protected evidence |
| 25 | `results/runs/20260422-170037_seed123_wp55-signal-audit_66fc17e/audit_summary.md` | Concise WP5.5 signal-degradation audit outcome supporting WP6 calibration caveats. | Audit evidence |

Rejected but not uploaded:

| File path | Reason |
|---|---|
| `manuscript/thesis_28.docx` | Redundant with PDF for ChatGPT reading; generator included for source provenance. |
| `manuscript/decisions_log_12.docx` | Redundant with PDF. |
| `docs/internal/project_full_notes_18april.md` | Superseded by this consolidated 13 May notes file. |
| `docs/wp5/wp5_notes.md` | Key content merged into this file. |
| `docs/wp6/wp6_notes.md` | Key content merged into this file. |
| `docs/wp2/wp2_notes.md` | Key content merged into this file. |
| `results/runs/*/metrics_wp5_oos*.csv` | Important numbers merged here; too many raw run files for 25-file budget. |
| `docs/internal/wp6_sweep_full/metrics_sweep_full.csv` | Large detailed CSV; protected summaries plus this file preserve final conclusions. |
| `scripts/legacy/*` | Historical provenance only; not active pipeline context. |
| `manuscript/thesis_25.*` and earlier drafts | Superseded by `thesis_28`. |
| `data/processed/wp2_synth.csv` | Convenience/latest snapshot, not needed when code, config, and notes explain provenance. |

Critical missing risk:

With only these 25 files, a future AI can verify the final thesis claim, protected evidence, pipeline design, canonical configs, and audit state. The main remaining difficulty is full raw rerun-level forensic reconstruction of every seed trajectory and plot artifact, because most raw run CSVs/PNGs are intentionally excluded. That is acceptable for the upload goal: final thesis decision-making and defense preparation, not complete local reproduction.
