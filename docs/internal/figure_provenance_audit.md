# Figure Provenance Audit

Purpose: trace every major figure embedded in `manuscript/thesis_28.pdf` to its generating script, source data, run IDs, and regeneration status. This is a documentation-only audit; figures were not regenerated.

Primary thesis insertion map: `scripts/gen_thesis_28.py`.

## Summary

| Figure | Thesis section / caption summary | Image path embedded by `gen_thesis_28.py` | Generating script | Source CSV(s) | Source run ID(s) | Reproducible now? | Protected artifact dependency? | Legacy dependency? | Provenance assessment |
|---|---|---|---|---|---|---|---|---|---|
| Figure 1 | OOS performance summary: Sharpe and inventory risk | `results/plots/thesis/fig1_sharpe_inv.png` | `src/wp5/figure_thesis.py` | `results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc/metrics_wp5_oos.csv` | `20260228-093733_seed1_wp5-eval-main_3e8eacc` | Yes, from frozen CSV using active script; do not regenerate unless explicitly approved | No | No | Clear. Script header declares ownership of Fig 1-5. |
| Figure 2 | Seed-paired PPO-aware vs PPO-blind comparison | `results/plots/thesis/fig2_paired_seed.png` | `src/wp5/figure_thesis.py` | `results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc/metrics_wp5_oos.csv` | `20260228-093733_seed1_wp5-eval-main_3e8eacc` | Yes, from frozen CSV using active script; do not regenerate unless explicitly approved | No | No | Clear. P-values are hardcoded visual annotations matching thesis values. |
| Figure 3 | Five-variant pure ablation summary | `results/plots/thesis_23/fig6_ablation_summary.png` | `src/wp5/figure_thesis_23.py` | `results/runs/20260327-171914_seed1_wp5-ablation_e1545a5/metrics_wp5_oos_combined.csv` | `20260327-171914_seed1_wp5-ablation_e1545a5` | Yes, from frozen CSV using active script; do not regenerate unless explicitly approved | No | No | Clear, but filename numbering (`fig6`) differs from thesis figure number because the script preserves thesis_23-era filenames. Documented in script header. |
| Figure 4 | Oracle paradox paired-seed visual | `results/plots/thesis_23/fig7_oracle_paired_seed.png` | `src/wp5/figure_thesis_23.py` | `results/runs/20260327-171914_seed1_wp5-ablation_e1545a5/metrics_wp5_oos_combined.csv` | `20260327-171914_seed1_wp5-ablation_e1545a5` | Yes, from frozen CSV using active script; do not regenerate unless explicitly approved | No | No | Clear. Uses active supplementary figure script. |
| Figure 5 | Regime-wise action distribution | `results/plots/thesis/fig5_action_analysis.png` | `src/wp5/figure_thesis.py` | Main WP5 run curves under `results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc/curves/*_test.csv` | `20260228-093733_seed1_wp5-eval-main_3e8eacc` | Likely yes from frozen curves using active script; exact visual depends on existing curve files and script behavior | No | No | Mostly clear. More granular provenance resides in curve CSVs rather than a single summary CSV. |
| Figure 6 | Regime-wise Sharpe by strategy | `results/plots/thesis/fig3_regime_sharpe.png` | `src/wp5/figure_thesis.py` | `results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc/metrics_wp5_oos_by_regime.csv` | `20260228-093733_seed1_wp5-eval-main_3e8eacc` | Yes, from frozen CSV using active script; do not regenerate unless explicitly approved | No | No | Clear. Embedded file name `fig3_regime_sharpe` differs from thesis figure number. |
| Figure 7 | Detector robustness by detector | `results/plots/thesis/fig4_detector_robustness.png` | `src/wp5/figure_thesis.py` | Default script source: `results/runs/20260316-223842_seed1_wp5-detector-full_a67e381/metrics_detector_pilot.csv`; protected summary: `results/metrics_detector_compare.csv`; stats: `results/stats_detector_robustness.txt` | `20260316-223842_seed1_wp5-detector-full_a67e381` | Reproducible from frozen detector CSV using active script; protected summary should remain frozen | Yes: `results/metrics_detector_compare.csv` protected for audit | No | Clear but nomenclature is confusing: default file is named `metrics_detector_pilot.csv` inside the full-run directory. Protected summary is canonical for audit. |
| Figure 8 | Regime-conditional eta summary | `results/plots/thesis_23/fig8_eta_regime_summary.png` | `src/wp5/figure_thesis_23.py` | `results/runs/20260330-155235_seed42_w5-eta-regime_af82a9f/metrics_wp5_oos.csv` | `20260330-155235_seed42_w5-eta-regime_af82a9f` | Yes, from frozen CSV using active script; do not regenerate unless explicitly approved | No | No | Clear. |
| Figure 9 | Mild misspecification summary | `results/plots/thesis_23/fig9_misspec_summary.png` | `src/wp5/figure_thesis_23.py` | `results/runs/20260408-160248_seed1_w5-misspec-mild_5d9dc23/metrics_wp5_oos.csv` | `20260408-160248_seed1_w5-misspec-mild_5d9dc23` | Yes, from frozen CSV using active script; do not regenerate unless explicitly approved | No | No | Clear. |
| Figure 10 | WP6 monotonic-gap plot | `docs/internal/wp6_sweep_full/plots/monotonic_gap.png` | `scripts/wp6_plot1_monotonic_gap.py` | `docs/internal/wp6_sweep_full/metrics_sweep_full.csv`; protected summary `summary_condition_variant.csv` | `20260426-105115_seed42_wp6-sweep-full_ce849a0` | Reproducible from frozen WP6 metrics CSV; do not regenerate for defense | Yes: `summary_condition_variant.csv` protected | No | Clear. The script writes the protected summary CSV, so running it would touch protected evidence. Do not run without explicit approval. |
| Figure 11 | WP6 paired combined vs sigma_only | `docs/internal/wp6_sweep_full/plots/paired_seed_combined_vs_sigma.png` | `scripts/wp6_plot2_paired_seed.py` | `docs/internal/wp6_sweep_full/metrics_sweep_full.csv`; protected summary `summary_paired_combined_vs_sigma.csv` | `20260426-105115_seed42_wp6-sweep-full_ce849a0` | Reproducible from frozen WP6 metrics CSV; do not regenerate for defense | Yes: `summary_paired_combined_vs_sigma.csv` protected | No | Clear. Script regenerates protected summary; freeze recommended. |
| Figure 12 | WP6 paired combined vs regime_only | `docs/internal/wp6_sweep_full/plots/paired_seed_combined_vs_regime.png` | `scripts/wp6_plot3_paired_seed_vs_regime.py` | `docs/internal/wp6_sweep_full/metrics_sweep_full.csv`; protected summary `summary_paired_combined_vs_regime.csv` | `20260426-105115_seed42_wp6-sweep-full_ce849a0` | Reproducible from frozen WP6 metrics CSV; do not regenerate for defense | Yes: `summary_paired_combined_vs_regime.csv` protected | No | Clear. Script regenerates protected summary; freeze recommended. |

## Generator Status

| Generator | Status | Notes |
|---|---|---|
| `scripts/gen_thesis_28.py` | Active current thesis generator | Embeds current figure files and saves `manuscript/thesis_28.docx`. Do not run for this audit. |
| `src/wp5/figure_thesis.py` | Active figure script for thesis Figures 1, 2, 5, 6, 7 as embedded file paths | Header explicitly states ownership of `fig1`-`fig5` output filenames and WP6 exclusion. |
| `src/wp5/figure_thesis_23.py` | Active figure script for thesis Figures 3, 4, 8, 9 via preserved `thesis_23` filenames | The `_23` suffix is historical but intentionally retained for appendix/file-index stability. |
| `scripts/wp6_plot1_monotonic_gap.py` | Active WP6 plot/stat script | Regenerates both plot and protected summary CSV. Treat as frozen unless explicitly approved. |
| `scripts/wp6_plot2_paired_seed.py` | Active WP6 plot/stat script | Regenerates both plot and protected summary CSV. Treat as frozen unless explicitly approved. |
| `scripts/wp6_plot3_paired_seed_vs_regime.py` | Active WP6 plot/stat script | Regenerates both plot and protected summary CSV. Treat as frozen unless explicitly approved. |
| `scripts/legacy/*` | Historical only | No current thesis figure should depend on these directly. Acceptable as provenance/history archive. |

## Flags

| Flag | Severity | Detail | Defense handling |
|---|---|---|---|
| Preserved `thesis_23` output directory for Figures 3/4/8/9 | Low | Current thesis embeds files under `results/plots/thesis_23/` because figure script filenames were preserved. | Explain as stable historical filename convention, not old evidence. Active script header documents this. |
| Detector CSV name `metrics_detector_pilot.csv` in full-run directory | Low/medium | `figure_thesis.py` default points to `results/runs/20260316-223842_seed1_wp5-detector-full_a67e381/metrics_detector_pilot.csv`. | Use protected `results/metrics_detector_compare.csv` and `stats_detector_robustness.txt` as canonical detector evidence in defense. |
| WP6 plot scripts write protected summaries | Medium | Running plot scripts would overwrite protected CSVs even if numerically identical. | Do not run WP6 plot scripts before defense; use frozen figures/summaries. |
| Exact regeneration of PNG rendering | Low | Matplotlib/font/backend differences can cause pixel-level differences. | Defend numerical evidence from CSVs and use current PNG/PDF figures as frozen presentation artifacts. |

## Conclusion

The figure provenance is defense-ready. All major figures trace to active scripts and named frozen data artifacts. The only sensitive point is not scientific but procedural: avoid regenerating WP6 plots or summaries because those scripts write protected evidence files.
