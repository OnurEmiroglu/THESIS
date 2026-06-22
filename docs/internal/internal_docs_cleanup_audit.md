# Internal Documentation Cleanup Audit

Date: 2026-06-22

Scope: every Markdown file present under `docs/internal/` before this report was created. This is a read-only classification audit: no existing file was deleted, moved, renamed, or modified; no experiment, manuscript generator, figure generator, or evidence-producing script was run.

The audit was performed against the current working-tree contents, not only the last committed versions. The accepted final-candidate package used as the manuscript reference point is:

- `manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v3f.docx`
- `manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v3f.pdf`
- `manuscript/hector_template_migration_audit_v3f.md`

## 1. Executive summary

Twenty-nine pre-existing Markdown files were audited.

| Recommendation | Count | Summary |
| --- | ---: | --- |
| `KEEP_CRITICAL` | 15 | Freeze/evidence provenance, reproducibility snapshots, defense records, frozen post-hoc summaries, and WP6 run context. |
| `KEEP_USEFUL` | 2 | Useful source/freshness context that is not itself primary evidence. |
| `MOVE_TO_ARCHIVE` | 9 | Superseded project notes, migration history, and completed discovery/audit records worth retaining outside the active layer. |
| `DELETE_SAFE` | 3 | Generic restore instructions and two superseded thesis-transition notes with no live operational dependency. |
| `REVIEW_MANUALLY` | 0 | No file remained too ambiguous to classify after content and reference checks. |

The repository's active internal-document spine should remain compact but intact: `project_full_notes_13may.md`, the claim/provenance/freeze records, config snapshot, defense material, the post-hoc signal package, and the WP5.5/WP6 snapshot documentation.

Two integrity checks were performed read-only during this audit:

- All 21 hashes recorded in `docs/internal/config_snapshot_all.md` match the current `config/*.json` files.
- All four protected hashes in `EVIDENCE_MANIFEST.md` match: `results/metrics_detector_compare.csv` plus the three protected WP6 summary CSVs.

## 2. Reference-check findings

The search covered `README.md`, `AGENTS.md`, `EVIDENCE_MANIFEST.md`, `FREEZE_METADATA.md`, `scripts/`, `manuscript/`, and other documentation/code text.

- `README.md` actively names `project_full_notes_13may.md` and `doc_consistency_audit.md` as orientation files.
- `AGENTS.md` names `project_full_notes_13may.md` as the project brain and treats the entire `posthoc_signal_analysis/` directory as read-only/frozen supporting diagnostics.
- `FREEZE_METADATA.md` names `figure_provenance_audit.md` and `defense_claim_matrix.md` as parts of the frozen provenance chain.
- `EVIDENCE_MANIFEST.md` names the post-hoc package and protects three non-Markdown files under `docs/internal/wp6_sweep_full/` by SHA-256.
- `docs/internal/codebase_snapshot.py` points to `config_snapshot_all.md`, cites the post-hoc summaries, and contains frozen copies of script references. It is an upload-context snapshot, not an executable dependency.
- `docs/internal/posthoc_signal_analysis/run_posthoc_signal_analysis.py` writes the four post-hoc Markdown summaries. Their generated status is a reason to preserve the frozen package, not an invitation to rerun it.
- `scripts/gen_decisions_log_13.py` cites `final_signal_redundancy_assessment.md`.
- `docs/wp5/wp5_notes.md` still cites `project_full_notes_12april.md`. That is a stale historical pointer; update it before moving the 12 April file.
- `docs/wp6/wp6_notes.md` cites the WP6 directory's protected CSVs, metrics, and plots. The two Markdown files in that directory supply run-level context for those assets.
- Older `manuscript/hector_template_migration_audit*.md` files list many internal documents only as captured `git status` entries. Those are historical audit observations, not active runtime or content dependencies.
- No current manuscript generator or active runtime script was found to depend on the three files marked `DELETE_SAFE`. References to them are absent or merely historical status snapshots.

## 3. All audited files

| Path | Short purpose | Freshness | Recommendation | Reason / supersession / proposed destination |
| --- | --- | --- | --- | --- |
| `docs/internal/calibration_audit/README.md` | Identifies the WP5.5 calibration run and explains the two calibration CSV snapshots and selected alpha/k values. | Current frozen context | `KEEP_CRITICAL` | Preserves how WP6 degradation parameters were selected and ties the CSVs to run `20260425-184732_seed42_wp55-calibration_1e806ff`. Its decision-log pointer is historical, but the provenance remains important. |
| `docs/internal/config_snapshot_all.md` | Single-file inventory and full snapshot of all 21 experiment configs, with SHA-256 hashes. | Current | `KEEP_CRITICAL` | Reproducibility/upload-context record; all 21 recorded hashes matched during this audit. It is also referenced by `codebase_snapshot.py`. |
| `docs/internal/defense_claim_matrix.md` | Maps each thesis claim to evidence files, figures, scripts, configs, run IDs, statistical support, and defense caveats. | Current with historical thesis_28/29 anchors | `KEEP_CRITICAL` | Core claim-to-evidence traceability and explicitly part of the `FREEZE_METADATA.md` provenance chain. The HECTOR v3f manuscript supersedes its manuscript-version pointers, not its evidence mappings. |
| `docs/internal/defense_risk_register.md` | Lists likely defense challenges and bounded, evidence-aware answers. | Current | `KEEP_CRITICAL` | Direct defense preparation; cited by the freeze recommendation. Its scientific cautions remain aligned with v3f. |
| `docs/internal/doc_consistency_audit.md` | Records a pre-HECTOR freshness/consistency review across README, project notes, thesis_28, decision log, and manifest. | Historical | `KEEP_USEFUL` | Most action items are now historical, and v3f migration audits are newer for manuscript status. Keep because `README.md` still names it and because it documents the earlier audit chain. Reassess only after updating that README reference. |
| `docs/internal/figure_provenance_audit.md` | Maps thesis figures to source plots, scripts, CSVs, run IDs, and regeneration risks. | Current with historical thesis_28/29 anchors | `KEEP_CRITICAL` | Essential figure provenance and explicitly named by `FREEZE_METADATA.md`; v3f reused the scientific figures rather than superseding their evidence chain. |
| `docs/internal/final_audit_check/final_check_report.md` | Eleven-step defense-readiness verification, including protected hashes, numerical checks, wording checks, and deferred minor findings. | Historical freeze audit | `KEEP_CRITICAL` | Records the verified pre-migration evidence baseline and 4/4 protected-hash invariant. The v3f migration audit supersedes only manuscript packaging/format status. |
| `docs/internal/final_audit_check/manuscript_deletion_rationale.md` | Explains four old advisor-document deletions and gives git-history recovery commands. | Historical | `MOVE_TO_ARCHIVE` | The deletions are complete, but the rationale is useful repository history. Proposed: `docs/internal/archive/audits/manuscript_deletion_rationale.md`. |
| `docs/internal/literature_review_chapter_draft_2026-05-27.md` | Standalone literature-review chapter draft covering market making, RL, regimes, signal redundancy, and TOST. | Superseded | `MOVE_TO_ARCHIVE` | Its selected content was integrated through thesis_30/thesis_31 and ultimately into HECTOR v3f. Proposed: `docs/internal/archive/literature_review/literature_review_chapter_draft_2026-05-27.md`. |
| `docs/internal/literature_review_positioning_2026-05-27.md` | Defense-safe literature positioning, exact thesis gap, acceptable wording, and claims to avoid. | Current content, historical drafting artifact | `MOVE_TO_ARCHIVE` | Still useful for oral-defense wording, but it belongs with defense references rather than active migration files. Proposed: `docs/internal/defense_refs/literature_review_positioning_2026-05-27.md`. |
| `docs/internal/literature_review_sources_2026-05-27.md` | Source inventory with verification status, bibliographic identifiers, and notes on intended use. | Current | `KEEP_USEFUL` | Valuable bibliography provenance and defense support. It is explicitly not the final bibliography, so it is useful rather than critical primary evidence. |
| `docs/internal/posthoc_signal_analysis/action_explanation_summary.md` | Summarizes aligned frozen-curve regressions explaining PPO half-spread/skew actions. | Current frozen diagnostic | `KEEP_CRITICAL` | Part of the read-only post-hoc package named by `AGENTS.md`/`EVIDENCE_MANIFEST.md`; preserves an important limitation against mechanistic overclaiming. |
| `docs/internal/posthoc_signal_analysis/final_signal_redundancy_assessment.md` | Synthesizes predictability, incremental-value, action, WP5, and WP6 evidence into the bounded final interpretation. | Current frozen diagnostic | `KEEP_CRITICAL` | Central defense interpretation; cited by the decision-log generator and frozen audit records. It supports, but does not replace, primary WP5/WP6 evidence. |
| `docs/internal/posthoc_signal_analysis/incremental_value_summary.md` | Reports held-out predictive change from adding `regime_hat` after `sigma_hat`. | Current frozen diagnostic | `KEEP_CRITICAL` | Component evidence for the final signal-redundancy assessment and part of the frozen package. |
| `docs/internal/posthoc_signal_analysis/predictability_summary.md` | Reports how well `regime_hat` and `regime_true` can be predicted from `sigma_hat`. | Current frozen diagnostic | `KEEP_CRITICAL` | Component evidence for signal overlap/redundancy and part of the frozen package. |
| `docs/internal/project_full_notes_12april.md` | Comprehensive project brain through the pre-WP6 WP5 stage, including simulator, PPO, detector, ablation, and eta-regime details. | Superseded | `MOVE_TO_ARCHIVE` | Superseded by `project_full_notes_18april.md` and ultimately `project_full_notes_13may.md`. Proposed: `docs/internal/archive/project_notes/project_full_notes_12april.md`. First update the stale link in `docs/wp5/wp5_notes.md:52`. |
| `docs/internal/project_full_notes_13may.md` | Canonical consolidated project brain: final claims, numerical results, architecture, configs, WP5/WP6 results, audit state, caveats, and defense narrative. | Current | `KEEP_CRITICAL` | Named by both `README.md` and `AGENTS.md`; repeatedly cited by the claim/provenance/freeze records. Historical manuscript pointers do not reduce its scientific and repository-context value. |
| `docs/internal/project_full_notes_17march.md` | Early project brain before later detector, ablation, misspecification, TOST, and WP6 closure. | Superseded | `MOVE_TO_ARCHIVE` | Superseded by 30 March, 12 April, 18 April, and finally 13 May notes. Proposed: `docs/internal/archive/project_notes/project_full_notes_17march.md`. |
| `docs/internal/project_full_notes_18april.md` | Expanded pre-WP6 project brain including five-variant and eta-regime work. | Superseded | `MOVE_TO_ARCHIVE` | Explicitly superseded by `project_full_notes_13may.md`. Proposed: `docs/internal/archive/project_notes/project_full_notes_18april.md`; update the two historical source pointers in the 13 May notes if moved. |
| `docs/internal/project_full_notes_30march.md` | Intermediate project brain containing older statuses, paths, and statistical interpretation. | Superseded | `MOVE_TO_ARCHIVE` | Superseded by 12 April, 18 April, and 13 May notes; some statements are stale. Proposed: `docs/internal/archive/project_notes/project_full_notes_30march.md`. |
| `docs/internal/refactor_discovery_report.md` | Read-only dependency scan prepared before moving root job modules into `src/wp*/`. | Superseded | `MOVE_TO_ARCHIVE` | The described refactor is now reflected in the current source layout, so this is implementation history rather than active guidance. Proposed: `docs/internal/archive/refactors/refactor_discovery_report.md`. |
| `docs/internal/repo_freeze_recommendation.md` | Defines files/runs to freeze, no-regeneration rules, backup priorities, and advisor-facing evidence. | Current policy with historical manuscript pointers | `KEEP_CRITICAL` | Protects canonical evidence and is cited by the final verification report. HECTOR v3f supersedes its manuscript filename pointers, but not its run/evidence freeze policy. |
| `docs/internal/RESTORE.md` | Minimal generic instructions for cloning, recreating a venv, installing extensions, and using an old thesis build task. | Superseded | `DELETE_SAFE` | Generic content is covered more accurately by `README.md`, `AGENTS.md`, `requirements.txt`, and current workspace tasks; the old “Build thesis” workflow predates HECTOR v3f. Migration-audit mentions are status snapshots, not dependencies. |
| `docs/internal/thesis_30_literature_review_integration_note.md` | Records literature inputs and edits made while producing thesis_30. | Superseded | `DELETE_SAFE` | Superseded by `thesis_31_template_adaptation_note.md` and, for the final package, `manuscript/hector_template_migration_audit_v3f.md`. The underlying literature draft/source records are separately retained or archived. No active script depends on it. |
| `docs/internal/thesis_31_template_adaptation_note.md` | Records the first template-adaptation mapping, literature compression, figure reuse, and no-rerun policy. | Superseded | `MOVE_TO_ARCHIVE` | Useful migration provenance, but final HECTOR structure/export status is superseded by `manuscript/hector_template_migration_audit_v3f.md`. Proposed: `docs/internal/archive/thesis_migrations/thesis_31_template_adaptation_note.md`. |
| `docs/internal/thesis_34_defense_QA.md` | Detailed oral-defense Q&A on TOST power, regime separation, misspecification, OOS design, PPO choice, metrics, literature, and extensions. | Current content, historical title | `KEEP_CRITICAL` | Directly useful for defense. The v3f migration changed packaging/layout, not the scientific answers. |
| `docs/internal/thesis_35_format_compliance_audit.md` | Records a pre-HECTOR format-compliance pass, placeholder list, and guide-availability caveat. | Superseded | `DELETE_SAFE` | Final HECTOR formatting/export QA is documented by `manuscript/hector_template_migration_audit_v3f.md`; this file has no active inbound reference and no unique scientific evidence. |
| `docs/internal/wp6_sweep_full/full_summary.md` | Records the 480-cell WP6 run, timing distribution, and per-condition/per-variant means. | Current frozen result context | `KEEP_CRITICAL` | Compact run-level evidence context for Chapter 5/WP6. Its “next step” is stale, but its run ID and values remain useful and are linked from the directory README. |
| `docs/internal/wp6_sweep_full/README.md` | Describes the completed WP6 full-sweep snapshot, run ID, files, metadata, and completion status. | Current frozen result context | `KEEP_CRITICAL` | Essential provenance wrapper for the directory containing protected evidence and the canonical 480-cell metrics. The regeneration command must be treated as documentation only before defense. |

## 4. KEEP_CRITICAL

- `docs/internal/calibration_audit/README.md`
- `docs/internal/config_snapshot_all.md`
- `docs/internal/defense_claim_matrix.md`
- `docs/internal/defense_risk_register.md`
- `docs/internal/figure_provenance_audit.md`
- `docs/internal/final_audit_check/final_check_report.md`
- `docs/internal/posthoc_signal_analysis/action_explanation_summary.md`
- `docs/internal/posthoc_signal_analysis/final_signal_redundancy_assessment.md`
- `docs/internal/posthoc_signal_analysis/incremental_value_summary.md`
- `docs/internal/posthoc_signal_analysis/predictability_summary.md`
- `docs/internal/project_full_notes_13may.md`
- `docs/internal/repo_freeze_recommendation.md`
- `docs/internal/thesis_34_defense_QA.md`
- `docs/internal/wp6_sweep_full/full_summary.md`
- `docs/internal/wp6_sweep_full/README.md`

## 5. KEEP_USEFUL

- `docs/internal/doc_consistency_audit.md` — keep while `README.md` uses it as an orientation document; it also preserves the pre-HECTOR freshness-audit trail.
- `docs/internal/literature_review_sources_2026-05-27.md` — retain as bibliography/source-verification context and defense support.

## 6. MOVE_TO_ARCHIVE

| Current path | Proposed destination | Prerequisite / note |
| --- | --- | --- |
| `docs/internal/final_audit_check/manuscript_deletion_rationale.md` | `docs/internal/archive/audits/manuscript_deletion_rationale.md` | No active inbound dependency found. |
| `docs/internal/literature_review_chapter_draft_2026-05-27.md` | `docs/internal/archive/literature_review/literature_review_chapter_draft_2026-05-27.md` | `thesis_30_literature_review_integration_note.md` references it, but that note is separately marked `DELETE_SAFE`. |
| `docs/internal/literature_review_positioning_2026-05-27.md` | `docs/internal/defense_refs/literature_review_positioning_2026-05-27.md` | Preserve for defense-safe wording. |
| `docs/internal/project_full_notes_12april.md` | `docs/internal/archive/project_notes/project_full_notes_12april.md` | Update `docs/wp5/wp5_notes.md:52` first. |
| `docs/internal/project_full_notes_17march.md` | `docs/internal/archive/project_notes/project_full_notes_17march.md` | Historical status references need not be rewritten. |
| `docs/internal/project_full_notes_18april.md` | `docs/internal/archive/project_notes/project_full_notes_18april.md` | Update source/supersession pointers in `project_full_notes_13may.md`. |
| `docs/internal/project_full_notes_30march.md` | `docs/internal/archive/project_notes/project_full_notes_30march.md` | Historical status references need not be rewritten. |
| `docs/internal/refactor_discovery_report.md` | `docs/internal/archive/refactors/refactor_discovery_report.md` | Completed refactor history. |
| `docs/internal/thesis_31_template_adaptation_note.md` | `docs/internal/archive/thesis_migrations/thesis_31_template_adaptation_note.md` | Final migration status is in the v3f audit. |

## 7. DELETE_SAFE

- `docs/internal/RESTORE.md` — generic and stale restore/build instructions; current setup is documented elsewhere.
- `docs/internal/thesis_30_literature_review_integration_note.md` — transitional note superseded by thesis_31 and the final v3f migration audit.
- `docs/internal/thesis_35_format_compliance_audit.md` — pre-HECTOR format audit superseded by the final v3f migration/export audit.

`DELETE_SAFE` means no unique current defense/evidence function or active code dependency was found. It is still prudent to review the diff and rely on git history before removal.

## 8. REVIEW_MANUALLY

None. The conservative recommendations above keep or archive every file with meaningful defense, provenance, or historical value.

## 9. Do not delete warnings

- Do not delete or alter `EVIDENCE_MANIFEST.md` or its four protected artifacts. Their hashes were 4/4 MATCH during this audit.
- Do not delete or casually relocate `FREEZE_METADATA.md`, `docs/internal/defense_claim_matrix.md`, or `docs/internal/figure_provenance_audit.md`; together they form the documented provenance chain.
- Do not delete `docs/internal/project_full_notes_13may.md`; it is the named project brain in both `README.md` and `AGENTS.md`.
- Do not split or partially clean `docs/internal/posthoc_signal_analysis/` without treating it as a frozen package. Its Markdown summaries, CSVs, images, source manifest, and generating script explain one another.
- Do not delete or regenerate the protected WP6 summary CSVs under `docs/internal/wp6_sweep_full/`. The directory README and full summary should remain with that evidence package.
- Do not delete `docs/internal/config_snapshot_all.md` or `docs/internal/codebase_snapshot.py` casually. They are complementary upload-context/reproducibility snapshots; the former currently matches all 21 configs.
- Do not interpret this Markdown audit as approval to delete `docs/wp5/wp5_notes.md`, `docs/wp6/wp6_notes.md`, `EVIDENCE_MANIFEST.md`, `FREEZE_METADATA.md`, `codebase_snapshot.py`, decision logs, experiment outputs, manuscript artifacts, or any non-Markdown sibling.
- Decisions logs are not submission artifacts, but they remain valuable defense chronology. If any are cleaned later, archive/move them or preserve an explicit recovery path rather than deleting casually.
- Preserve the accepted v3f DOCX/PDF and `manuscript/hector_template_migration_audit_v3f.md` as the current final-candidate package.

## 10. Suggested next-step cleanup commands — do not run yet

These commands are proposals only. Update the two live historical links noted below before moving their targets, review the working tree, and then run the commands manually in a dedicated cleanup pass.

```powershell
# Review current working-tree edits to every proposed target before cleanup.
git diff -- docs/internal/RESTORE.md docs/internal/thesis_30_literature_review_integration_note.md docs/internal/thesis_35_format_compliance_audit.md
git diff -- docs/internal/final_audit_check/manuscript_deletion_rationale.md docs/internal/literature_review_chapter_draft_2026-05-27.md docs/internal/literature_review_positioning_2026-05-27.md docs/internal/project_full_notes_12april.md docs/internal/project_full_notes_17march.md docs/internal/project_full_notes_18april.md docs/internal/project_full_notes_30march.md docs/internal/refactor_discovery_report.md docs/internal/thesis_31_template_adaptation_note.md

# Create archive destinations.
New-Item -ItemType Directory -Force -Path docs/internal/archive/audits
New-Item -ItemType Directory -Force -Path docs/internal/archive/literature_review
New-Item -ItemType Directory -Force -Path docs/internal/archive/project_notes
New-Item -ItemType Directory -Force -Path docs/internal/archive/refactors
New-Item -ItemType Directory -Force -Path docs/internal/archive/thesis_migrations
New-Item -ItemType Directory -Force -Path docs/internal/defense_refs

# Before moving: update docs/wp5/wp5_notes.md:52 to the 13 May notes or the new archive path.
# Before moving: update the two project_full_notes_18april.md pointers in project_full_notes_13may.md.

git mv docs/internal/final_audit_check/manuscript_deletion_rationale.md docs/internal/archive/audits/
git mv docs/internal/literature_review_chapter_draft_2026-05-27.md docs/internal/archive/literature_review/
git mv docs/internal/literature_review_positioning_2026-05-27.md docs/internal/defense_refs/
git mv docs/internal/project_full_notes_12april.md docs/internal/archive/project_notes/
git mv docs/internal/project_full_notes_17march.md docs/internal/archive/project_notes/
git mv docs/internal/project_full_notes_18april.md docs/internal/archive/project_notes/
git mv docs/internal/project_full_notes_30march.md docs/internal/archive/project_notes/
git mv docs/internal/refactor_discovery_report.md docs/internal/archive/refactors/
git mv docs/internal/thesis_31_template_adaptation_note.md docs/internal/archive/thesis_migrations/

git rm docs/internal/RESTORE.md
git rm docs/internal/thesis_30_literature_review_integration_note.md
git rm docs/internal/thesis_35_format_compliance_audit.md

# Validate references and inspect; do not commit automatically.
rg -n "project_full_notes_12april|project_full_notes_18april|thesis_30_literature_review_integration_note|thesis_35_format_compliance_audit|docs/internal/RESTORE.md" README.md AGENTS.md docs scripts manuscript
git diff --stat
git status --short
```

Historical `git status` snapshots inside old HECTOR migration audits do not need path rewriting. They record the repository state at the time of those audits and should remain historically accurate.
