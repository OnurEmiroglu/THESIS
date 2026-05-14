# Repository Freeze Recommendation

Purpose: define what should be frozen for defense, what may safely change, and what must not be regenerated. This file also records the final repo sanity scan requested for the defense-readiness audit.

## Freeze Recommendation

| Scope | Freeze status | Rationale |
|---|---|---|
| `manuscript/thesis_28.pdf` and `manuscript/thesis_28.docx` | Freeze | Final thesis artifact. Do not regenerate unless explicitly creating a new thesis version. |
| `manuscript/decisions_log_12.pdf` and `manuscript/decisions_log_12.docx` | Freeze | Final decision record including audit-remediation Decisions #48-#51. |
| `EVIDENCE_MANIFEST.md` | Freeze | Canonical audit-remediation manifest committed at `045ee86`. |
| `docs/internal/project_full_notes_13may.md` | Freeze after review/commit | Consolidated project brain for defense/upload context. |
| `docs/internal/codebase_snapshot.py` | Freeze after review/commit | Single-file code context snapshot; update only if active code changes. |
| `docs/internal/doc_consistency_audit.md` | Freeze after review/commit | Freshness audit record. |
| `docs/internal/defense_claim_matrix.md` | Freeze after review/commit | Claim-to-evidence traceability. |
| `docs/internal/figure_provenance_audit.md` | Freeze after review/commit | Figure provenance record. |
| `docs/internal/defense_risk_register.md` | Freeze after review/commit | Defense preparation record. |
| `docs/internal/repo_freeze_recommendation.md` | Freeze after review/commit | This freeze policy. |
| `results/metrics_detector_compare.csv` | Hard freeze / protected | Lane C protected evidence artifact. |
| `docs/internal/wp6_sweep_full/summary_condition_variant.csv` | Hard freeze / protected | Lane C protected evidence artifact. |
| `docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv` | Hard freeze / protected | Lane C protected evidence artifact. |
| `docs/internal/wp6_sweep_full/summary_paired_combined_vs_regime.csv` | Hard freeze / protected | Lane C protected evidence artifact. |
| `docs/internal/wp6_sweep_full/metrics_sweep_full.csv` | Hard freeze | Full WP6 evidence base behind protected summaries. |
| `docs/internal/wp6_sweep_full/plots/*` | Hard freeze | Thesis Figures 10-12 and companion PDFs. |
| `results/plots/thesis/*` | Hard freeze | Thesis Figures 1, 2, 5, 6, 7 as embedded. |
| `results/plots/thesis_23/*` | Hard freeze | Thesis Figures 3, 4, 8, 9 as embedded. |
| Canonical run directories listed below | Hard freeze | Source evidence, model files, curves, configs, and metrics. |

## Canonical Run Directories to Freeze

| Run directory | Evidence role |
|---|---|
| `results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc` | Main WP5 OOS aware/blind/AS/naive evidence and Figures 1, 2, 5, 6. |
| `results/runs/20260316-223842_seed1_wp5-detector-full_a67e381` | Detector robustness full-run source. |
| `results/runs/20260327-171914_seed1_wp5-ablation_e1545a5` | Five-variant ablation and oracle paradox evidence. |
| `results/runs/20260330-155235_seed42_w5-eta-regime_af82a9f` | Regime-conditional eta evidence. |
| `results/runs/20260408-160248_seed1_w5-misspec-mild_5d9dc23` | Mild model misspecification evidence. |
| `results/runs/20260422-170037_seed123_wp55-signal-audit_66fc17e` | WP5.5 signal audit evidence used for WP6 calibration caveats. |
| `docs/internal/wp6_sweep_full` | WP6 full sweep mirror/summary directory for Chapter 5 evidence. |

## Files That May Still Safely Change

| File class | Safe changes | Conditions |
|---|---|---|
| Defense-only markdown notes under `docs/internal/` | Typos, clarifications, additional cross-references | Do not alter numerical claims unless copied from canonical sources and reviewed. |
| `README.md`, `CLAUDE.md` | Documentation freshness and path corrections | No new experimental claims without source references. |
| New upload manifests/checklists | Additive documentation only | Avoid touching results/manuscripts. |
| `.gitignore` / housekeeping docs | Non-scientific repo hygiene | Do not affect tracked protected evidence. |

## Outputs That Must Never Be Regenerated Before Defense

| Output | Reason |
|---|---|
| `manuscript/thesis_28.*` | Final thesis artifact. |
| `manuscript/decisions_log_12.*` | Final decision artifact. |
| Protected CSV set in `EVIDENCE_MANIFEST.md` | Hash-protected audit evidence. |
| `docs/internal/wp6_sweep_full/summary_*.csv` | Protected summaries; WP6 plot scripts overwrite them. |
| `docs/internal/wp6_sweep_full/plots/*` | Current thesis Chapter 5 figures. |
| `results/plots/thesis/*` and `results/plots/thesis_23/*` | Current thesis figure artifacts. |
| Any `results/runs/**/models/*.zip` | PPO trained model artifacts. |
| Any canonical run metrics/curves CSVs | Source evidence for thesis claims. |

## External Backup Recommendation

Back up the following outside the repo before defense:

| Item | Why |
|---|---|
| `manuscript/thesis_28.pdf` and `.docx` | Final deliverable. |
| `manuscript/decisions_log_12.pdf` and `.docx` | Audit/decision provenance. |
| `EVIDENCE_MANIFEST.md` | Protected evidence map. |
| `docs/internal/project_full_notes_13may.md` | High-density defense/project memory. |
| `docs/internal/codebase_snapshot.py` | Single-file code context. |
| The four protected CSV files | Hash-frozen evidence base. |
| `docs/internal/wp6_sweep_full/` | Full WP6 evidence, summaries, plots, config/meta. |
| `results/plots/thesis/` and `results/plots/thesis_23/` | Thesis embedded figure images. |
| Canonical run directories listed above | Metrics, curves, model artifacts, config snapshots. |

## Advisor-Facing Critical Evidence

| Evidence | Use in advisor/committee discussion |
|---|---|
| `manuscript/thesis_28.pdf` | Primary thesis text. |
| `docs/internal/project_full_notes_13may.md` | Compact map of all final results and caveats. |
| `EVIDENCE_MANIFEST.md` | Audit/remediation and protected artifact guarantees. |
| `docs/internal/defense_claim_matrix.md` | Claim-by-claim evidence trace. |
| `docs/internal/figure_provenance_audit.md` | Figure provenance and regeneration risk. |
| `docs/internal/defense_risk_register.md` | Prepared answers to likely questions. |
| `results/metrics_detector_compare.csv` | Detector robustness protected artifact. |
| `docs/internal/wp6_sweep_full/summary_*.csv` | WP6 protected summary evidence. |

## Final Repo Sanity Scan Findings

This scan is read-only and report-only. It reviewed `README.md`, `CLAUDE.md`, `project_full_notes_13may.md`, `EVIDENCE_MANIFEST.md`, `scripts/gen_thesis_28.py`, active source/config paths, and current git status.

| Check | Finding | Risk | Recommendation |
|---|---|---|---|
| Stale manuscript references | `README.md` and `CLAUDE.md` now point to `thesis_28` / `decisions_log_12`; no remaining `thesis_25`, `decisions_log_8`, `scripts/gen_thesis_docx`, `src/w1_`, or `src/w3_sanity` references were found in those two docs after refresh. | Low | Keep current docs frozen after review. |
| Obsolete thesis version pointers elsewhere | Historical references remain under `scripts/legacy/*` and archived files by design. | Low | Do not edit legacy archive; it is provenance/history only. |
| Orphan configs | All active `config/*.json` files are included in `docs/internal/codebase_snapshot.py`; WP5.5/WP6 configs exist. | Low | No action unless active dispatcher changes. |
| Dead active imports | No import execution was performed in this audit. Static read shows active dispatcher imports current package paths and lazy-loads WP5.5/WP6 jobs. | Low/medium | Avoid claiming full import test was run; code snapshot coverage is current. |
| Duplicated active jobs | `run.py` has one branch per active job. Historical generators are archived. | Low | No action. |
| Active scripts pointing to legacy outputs | `figure_thesis_23.py` writes to `results/plots/thesis_23/` by intentional historical filename convention; not a legacy script dependency. | Low | Documented in figure provenance audit. |
| Accidental overwrite risk | Highest risk is WP6 plot scripts, which write protected summary CSVs and plot files. Figure scripts also overwrite thesis PNGs. | Medium | Do not run plotting/generation scripts before defense unless a new version is explicitly approved. |
| Ambiguous "current" labels | README/CLAUDE were refreshed. `project_full_notes_13may.md` states latest pushed remediation commit before that notes file was `045ee86`; additional uncommitted docs may now exist. | Low | When committing new audit docs, update any future manifest if needed. |
| Dirty/untracked repo state | Working tree contains intended documentation changes and pre-existing housekeeping/archive changes. | Medium for final push hygiene | Before final defense push, stage only intended docs or clean/archive housekeeping deliberately. |

## Freeze Verdict

The repository is defense-ready if the new defense audit docs are reviewed and staged intentionally. The main freeze rule is simple: do not regenerate thesis artifacts, figures, protected summaries, or experiment outputs before defense.
