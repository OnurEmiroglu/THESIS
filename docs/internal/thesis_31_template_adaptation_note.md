# Thesis 31 Template Adaptation Note

Date: 2026-06-01

Scope: thesis writing and technical-report template adaptation only. No experiments were run, no PPO models were trained, no figures were regenerated, and no protected evidence CSVs, PNGs, or canonical run outputs were modified.

## Template Adaptation Principle

`thesis_31` is a template-adapted English technical-report draft derived from the existing thesis evidence base. It is not a replacement for the frozen baseline `manuscript/thesis_29.pdf` and does not alter the literature-review integrated `manuscript/thesis_30.pdf`.

The central bounded interpretation is preserved throughout:

> In the tested controlled synthetic HFMM environment, explicit categorical volatility-regime labels do not provide robust incremental value once sigma_hat is already observed by the PPO policy. The results are consistent with signal redundancy.

The adaptation avoids claims that volatility regimes are irrelevant, labels contain zero information, PPO internal mechanisms are proven, categorical-channel interference is conclusively proven, results generalize to all market-making environments, or live trading/deployment viability is shown.

## Final Section Mapping

| Template Section | Source Material | Adaptation Decision |
| --- | --- | --- |
| Title Page | `thesis_30`, README project title | Rewritten in English as a technical-report title page. |
| Abstract | `thesis_30` abstract, README final finding | Rewritten in English with bounded synthetic-market framing. |
| Symbols, Abbreviations, and Glossary | `thesis_30` front matter | Condensed and translated into English. |
| 1 Introduction | `thesis_30` Introduction and Literature Review | Literature review compressed into Section 1.3. |
| 2 Mathematical Formulation | `thesis_30` methodology and AGENTS architecture notes | Reorganized around equations required by the template. |
| 3 Use-Case Scenario | Existing synthetic HFMM framing | New bridge section clarifying the controlled synthetic use case. |
| 4 System Architecture | README, AGENTS, `project_full_notes_13may.md` | Reframed as layered report architecture, not software-product marketing. |
| 5 Layered Experimental Model | WP0-WP6 structure | New template-facing layered model equivalent. |
| 6 Algorithm Specification and Pseudocode | `src/wp2`, `src/wp3`, `src/wp5`, `src/wp6` summaries | Concise pseudocode only; full code remains in appendix/file map. |
| 7 Experimental Setup | WP5/WP6 notes, config snapshot, evidence manifest | Canonical setup, seeds, variants, detector caveats, and no-rerun policy. |
| 8 Results and Visualisation | `thesis_30` Chapters 5-6 and frozen figures | Reuses existing figures only; no plot scripts are run. |
| 9 Evaluation Metrics | `thesis_30`, WP5/WP6 notes | Metrics and statistical tests collected into one template section. |
| 10 Discussion | `project_full_notes_13may.md`, defense claim/risk docs | Signal redundancy interpretation with caveats and future work. |
| 11 Reproducibility Checklist | `EVIDENCE_MANIFEST.md`, `FREEZE_METADATA.md`, run lifecycle notes | Defense-safe checklist with protected hashes. |
| 12 Conclusion | `thesis_30` conclusion | Condensed English conclusion. |
| Appendix A | `docs/internal/codebase_snapshot.py`, README | Code map and executable commands. |
| Appendix B | tests and WP3 sanity checks | Unit-test and sanity-check summary. |
| Appendix C | Longer supporting result tables | Extended evidence tables and diagnostic summaries. |

Appendix D Assessment Criteria is intentionally omitted because it is not part of the thesis unless explicitly required later.

## Literature Review Compression Decision

`thesis_30` introduced a standalone literature-review chapter. For `thesis_31`, that material is compressed into `1.3 Background and Related Work` because the target template places related work inside the Introduction.

The compressed section preserves four strands:

- Classical market making and inventory risk.
- Reinforcement learning and deep reinforcement learning for market making.
- Volatility regimes, non-stationarity, and state representation.
- Equivalence testing and null-result interpretation.

This keeps the draft template-compatible while preserving the defense-safe intellectual positioning.

## Figure and Table Reuse Plan

Only existing figure files are embedded. Figure scripts are not executed.

| Figure | Existing Path | Thesis 31 Location | Decision |
| --- | --- | --- | --- |
| Main OOS performance and inventory risk | `results/plots/thesis/fig1_sharpe_inv.png` | Section 8.1 | Keep. |
| Seed-paired PPO-aware vs PPO-blind | `results/plots/thesis/fig2_paired_seed.png` | Section 8.1 | Keep. |
| Five-variant ablation summary | `results/plots/thesis_23/fig6_ablation_summary.png` | Section 8.2 | Keep. |
| Oracle paired-seed visual | `results/plots/thesis_23/fig7_oracle_paired_seed.png` | Section 8.2 | Keep. |
| Detector robustness | `results/plots/thesis/fig4_detector_robustness.png` | Section 8.3 | Keep. |
| Regime-conditional eta | `results/plots/thesis_23/fig8_eta_regime_summary.png` | Section 8.4 | Keep. |
| Mild misspecification | `results/plots/thesis_23/fig9_misspec_summary.png` | Section 8.4 | Keep. |
| WP6 monotonic gap | `docs/internal/wp6_sweep_full/plots/monotonic_gap.png` | Section 8.5 | Keep. |
| WP6 combined vs sigma_only | `docs/internal/wp6_sweep_full/plots/paired_seed_combined_vs_sigma.png` | Section 8.5 | Keep. |
| WP6 combined vs regime_only | `docs/internal/wp6_sweep_full/plots/paired_seed_combined_vs_regime.png` | Section 8.5 | Keep if space allows. |
| Action analysis | `results/plots/thesis/fig5_action_analysis.png` | Appendix C | Demote. |
| Regime-wise Sharpe | `results/plots/thesis/fig3_regime_sharpe.png` | Appendix C | Demote. |

Main tables retained in the body:

- Main WP5 OOS table.
- Five-variant ablation table.
- Key statistical tests table.
- WP6 condition-variant table.
- Reproducibility checklist table.

Long diagnostic or provenance-heavy tables are moved to the appendices.

## No-Rerun Policy

The following remain untouched:

- `manuscript/thesis_29.pdf`
- `manuscript/thesis_29.docx`
- `manuscript/thesis_30.pdf`
- `manuscript/thesis_30.docx`
- `manuscript/decisions_log_13.pdf`
- `manuscript/decisions_log_13.docx`
- Protected CSVs listed in `EVIDENCE_MANIFEST.md`
- Existing WP5/WP6 figures and summaries
- Canonical run outputs under `results/runs/`
- Frozen diagnostic packages unless explicitly unfrozen

## Files Touched By Thesis 31 Implementation

Allowed files created or updated:

- `docs/internal/thesis_31_template_adaptation_note.md`
- `scripts/gen_thesis_31_template.py`
- `manuscript/thesis_31.docx`
- `manuscript/thesis_31.pdf`

No other file should be modified by this adaptation.
