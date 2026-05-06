# WP6: Signal Informativeness Sweep Notes

## 1. Setup

- 20 seeds, 5 conditions × 5 variants = 25 cells (= 480 cells total, since `sigma_only` is structurally undefined under `condition = none`)
- Conditions (signal degradation axis): `full` → `noisy` → `lagged` → `coarsened` → `none`
- Variants: `sigma_only`, `combined`, `regime_only`, `oracle_full`, `oracle_pure`
- Train/test split: WP5 convention (70/30 on exogenous series, n_train=5600 / n_test=2400)
- Each cell: one PPO model trained on train split, deterministic OOS evaluation on test split
- Calibration parameters: noisy α=0.40, lagged k=20 (Decision #46, offline calibration audit), coarsened binning per same audit
- Results CSV: `docs/internal/wp6_sweep_full/metrics_sweep_full.csv` (480 rows)

By-design constraints:
- `regime_only` and `oracle_pure` do not consume `sigma_hat` → condition-invariant (verified seed-by-seed in Plot 3 sanity check, max |diff| = 0)
- `sigma_only` requires sigma → undefined when `condition = none` (sigma_hat is zeroed out)
- `combined` under `condition = none` collapses to `regime_only` (use_sigma=False, regime_source=hat) — verified: identical mean (0.6991), identical seed-paired values

## 2. Main Sweep Results (Plot 1: monotonic-gap)

Aggregated CSV: `docs/internal/wp6_sweep_full/summary_condition_variant.csv` (mean ± 95% CI, t-critical, df=19).

| condition | sigma_only | combined | regime_only | oracle_full | oracle_pure |
|---|---|---|---|---|---|
| full      | 0.7626 ± 0.0596 | 0.6898 ± 0.0607 | 0.6991 ± 0.0668 | 0.6811 ± 0.0697 | 0.6632 ± 0.0769 |
| noisy     | 0.7563 ± 0.0616 | 0.7125 ± 0.0628 | 0.6991 ± 0.0668 | 0.6736 ± 0.1013 | 0.6632 ± 0.0769 |
| lagged    | 0.7822 ± 0.0454 | 0.6812 ± 0.0536 | 0.6991 ± 0.0668 | 0.7264 ± 0.0686 | 0.6632 ± 0.0769 |
| coarsened | 0.7827 ± 0.0533 | 0.6908 ± 0.0827 | 0.6991 ± 0.0668 | 0.7447 ± 0.0549 | 0.6632 ± 0.0769 |
| none      | NaN (n=0)       | 0.6991 ± 0.0668 | 0.6991 ± 0.0668 | 0.6632 ± 0.0769 | 0.6632 ± 0.0769 |

Observations:
- `sigma_only` is essentially flat across the four informative conditions (0.756–0.783), not monotonically declining as the original hypothesis would predict.
- `combined` sits below `sigma_only` everywhere by 0.04–0.10 Sharpe-like.
- `regime_only` and `oracle_pure` are flat by construction and serve as anchor baselines.
- In `none`, `combined` and `regime_only` collapse together; `oracle_full` and `oracle_pure` collapse together.

Plot: `docs/internal/wp6_sweep_full/plots/monotonic_gap.{png,pdf}`. Script: `scripts/wp6_plot1_monotonic_gap.py`.

## 3. Paired-Seed Analysis: combined vs sigma_only (Plot 2)

Question: is `combined < sigma_only` robust seed-by-seed, or driven by outlier seeds?

CSV: `docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv`. TOST direction: **non-equivalence** (H1: |mean_diff| > δ), δ=0.05, two one-sided tests, reject H0 iff min(p_lower, p_upper) < 0.05.

| condition | n_below | mean_diff | paired t p | Cohen's dz | TOST p | reject H0 (non-equiv) |
|---|---|---|---|---|---|---|
| full      | 15/20 | −0.073 | 0.012   | −0.621 | 0.198 | No |
| noisy     | 15/20 | −0.044 | 0.020   | −0.568 | 0.640 | No |
| lagged    | 18/20 | −0.101 | 0.00064 | −0.912 | 0.027 | **Yes** |
| coarsened | 15/20 | −0.092 | 0.0088  | −0.653 | 0.099 | No |

Reading:
- Direction is robust seed-by-seed in all four panels (15–18 of 20 below identity, paired t-test p < 0.05 everywhere, Cohen's dz medium-to-large between −0.57 and −0.91).
- Magnitude exceeds the practical-relevance threshold (δ=0.05) only in `lagged` (mean_diff = −0.101, dz = −0.91). The other conditions show consistent direction but the 90% CI of the diff still touches the equivalence band.

Plot: `docs/internal/wp6_sweep_full/plots/paired_seed_combined_vs_sigma.{png,pdf}`. Script: `scripts/wp6_plot2_paired_seed.py`.

## 4. Paired-Seed Analysis: combined vs regime_only (Plot 3)

Question: in the combined variant, does the policy still extract value from `sigma_hat` beyond what `regime_only` provides?

CSV: `docs/internal/wp6_sweep_full/summary_paired_combined_vs_regime.csv`. TOST direction: **equivalence** (H1: |mean_diff| ≤ δ), δ=0.05, two one-sided tests, reject H0 iff max(p_lower, p_upper) < 0.05.

| condition | n_above | mean_diff | paired t p | Cohen's dz | TOST p | reject H0 (equiv) |
|---|---|---|---|---|---|---|
| full      |  9/20 | −0.009 | 0.791 | −0.060 | 0.128 | No |
| noisy     |  7/20 | +0.013 | 0.685 | +0.092 | 0.137 | No |
| lagged    | 11/20 | −0.018 | 0.535 | −0.141 | 0.136 | No |
| coarsened | 10/20 | −0.008 | 0.814 | −0.053 | 0.123 | No |

Variance side-output:

| condition | std_combined | std_regime_only | std_diff | iqr_combined | iqr_regime_only | iqr_diff |
|---|---|---|---|---|---|---|
| full      | 0.130 | 0.143 | 0.155 | 0.114 | 0.125 | 0.140 |
| noisy     | 0.134 | 0.143 | 0.145 | 0.091 | 0.125 | 0.126 |
| lagged    | 0.114 | 0.143 | 0.127 | 0.120 | 0.125 | 0.112 |
| coarsened | 0.177 | 0.143 | 0.156 | 0.207 | 0.125 | 0.127 |

Reading:
- Mean diffs are tiny (|mean_diff| ≤ 0.018) and three of four are negative. Outcome (a) ("combined > regime_only") is firmly rejected.
- TOST equivalence cannot be formally claimed: tost_p ≈ 0.12–0.14 in all four panels, does not clear α=0.05. With observed std_diff ≈ 0.13–0.16 and n=20, the minimum detectable equivalence band is roughly ±0.07–0.08, not ±0.05 — i.e. underpowered, not absence of effect.
- `std_diff > std_regime_only` in `full`, `noisy`, `coarsened` (3 of 4), indicating combined and regime_only are not seed-paired-deterministic — the policies are not learning the same per-seed function.
- `coarsened` has highest std_combined (0.177 vs 0.143 baseline), driven by a few high-Sharpe seeds visible in the panel.

Auto-classified outcome per condition: all four are **(c) inconclusive** under the strict (a)/(b)/(c) decision rule, but qualitatively closer to (b) than (a).

Plot: `docs/internal/wp6_sweep_full/plots/paired_seed_combined_vs_regime.{png,pdf}`. Script: `scripts/wp6_plot3_paired_seed_vs_regime.py`.

## 5. Discussion / Refined Interpretation

### 5.1 Original hypothesis: rejected

- Pre-registered expectation: as `sigma_hat` was progressively degraded (full → noisy → lagged → coarsened → none), the gap between `sigma_only` and `combined` should narrow monotonically — once sigma was sufficiently noisy, the categorical regime label would start to add meaningful information.
- Observed: the gap stays in the 0.06–0.10 Sharpe-like range across all four informative conditions; `sigma_only` is essentially condition-invariant (0.756–0.783) within the tested calibration range (α=0.40 noisy, k=20 lagged, coarsened binning per Decision #46).
- Caveat: more aggressive degradations (e.g. α=0.20 conservative or α=0.80 / k=50 aggressive) were not tested in the main sweep. The flatness of `sigma_only` is a statement about the calibration band selected for the sweep, not a universal claim about all sigma degradations.

### 5.2 Stronger empirical pattern

- `combined` is directionally shifted below `sigma_only` in all 4 informative conditions: paired t-test p < 0.05 everywhere, Cohen's dz between −0.57 (medium) and −0.91 (large).
- Magnitude exceeds the practical-relevance threshold (δ = 0.05 Sharpe-like) only in the `lagged` condition (mean_diff = −0.101, dz = −0.91). Use **"directionally shifted"** in chapter prose, not "consistently shifted" — the magnitude is condition-dependent and only one of four panels clears the practical threshold.
- This is the reverse of the pre-registered direction: not "regime labels become useful as sigma degrades" but "regime labels appear to *interfere* with sigma when both are presented together."

### 5.3 Refined interpretation

- `combined` did not deterministically collapse to `regime_only` behavior. Mean diffs are null (Plot 3) but variance is heterogeneous: `std_diff > std_regime_only` in 3 of 4 conditions (full, noisy, coarsened). The policies are not learning the same per-seed function, so the effect is statistical-mean equivalence rather than policy-level equivalence.
- TOST equivalence at δ=0.05 is **not formally rejected at n=20** (tost_p ≈ 0.12–0.14). With observed std_diff ≈ 0.13–0.16, the minimum detectable equivalence band is roughly ±0.07–0.08. This is **underpowered, not absence of effect**. A conservative claim is therefore "indistinguishable in mean within a ±0.07 band" rather than "equivalent at δ=0.05".
- **Methodological symmetry with WP5.** WP5 used TOST to *prove equivalence* (`ppo_aware ≈ ppo_blind`, see WP5 notes Section 10). WP6 uses TOST in the opposite direction in Plot 2: to *prove non-equivalence* (`combined ≠ sigma_only`) by showing the 90% CI of the paired diff lies outside [−δ, +δ]. Plot 3 returns to the WP5 direction (equivalence). This symmetry — and its implementation difference (max-p vs min-p of the two one-sided tests) — should be made explicit in the chapter intro to prevent reader confusion.
- **Mechanism is not identified.** The data are consistent with several mechanisms — (i) representational interference (the regime one-hot disrupts sigma-conditional value estimation), (ii) crowd-out (the policy puts weight on the categorical channel and underuses sigma), (iii) optimization noise (PPO finds a slightly different local optimum when given the larger observation). This experiment cannot distinguish among them. Use **"encoding-interference"** as a descriptive label in the chapter, not "representation-level effect" (avoid undefined term that implies a mechanism we have not identified).

## 6. Status (6 May 2026)

WP6 main sweep complete:
- 480-cell sweep run (5d 12h wall clock): ✓ — `docs/internal/wp6_sweep_full/metrics_sweep_full.csv`
- Plot 1 monotonic-gap: ✓
- Plot 2 paired-seed combined vs sigma_only: ✓
- Plot 3 paired-seed combined vs regime_only + variance side-output: ✓
- Section 5 interpretation: ✓ (this document)
- Decision #47 logged (chapter reframing, Plot 4 not pursued)

Plot 4 (per-regime breakdown / action analysis) not pursued — the three plots above establish the chapter spine; further analysis would open new fronts orthogonal to the core sweep question. See Decision #47.

Current manuscript: thesis_25 / decisions_log_10 → decisions_log_11 (this update).
