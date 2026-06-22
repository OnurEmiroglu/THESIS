# Internal Documentation Cleanup Execution Report

Date: 2026-06-22

Source plan: `docs/internal/internal_docs_cleanup_audit.md`

Scope: implementation of the documentation-only archive/delete plan. No experiment, PPO/WP5/WP6 job, manuscript generator, figure generator, or evidence-producing script was run. No source code, config, experiment output, CSV, figure, PDF, or DOCX was changed by this cleanup.

## Archive folders

The following folders were created or confirmed present:

- `docs/internal/archive/audits/`
- `docs/internal/archive/literature_review/`
- `docs/internal/archive/project_notes/`
- `docs/internal/archive/refactors/`
- `docs/internal/archive/thesis_migrations/`
- `docs/internal/defense_refs/`

## Files moved

All nine `MOVE_TO_ARCHIVE` recommendations were applied with `git mv`.

| Previous path | New path |
| --- | --- |
| `docs/internal/final_audit_check/manuscript_deletion_rationale.md` | `docs/internal/archive/audits/manuscript_deletion_rationale.md` |
| `docs/internal/literature_review_chapter_draft_2026-05-27.md` | `docs/internal/archive/literature_review/literature_review_chapter_draft_2026-05-27.md` |
| `docs/internal/literature_review_positioning_2026-05-27.md` | `docs/internal/defense_refs/literature_review_positioning_2026-05-27.md` |
| `docs/internal/project_full_notes_12april.md` | `docs/internal/archive/project_notes/project_full_notes_12april.md` |
| `docs/internal/project_full_notes_17march.md` | `docs/internal/archive/project_notes/project_full_notes_17march.md` |
| `docs/internal/project_full_notes_18april.md` | `docs/internal/archive/project_notes/project_full_notes_18april.md` |
| `docs/internal/project_full_notes_30march.md` | `docs/internal/archive/project_notes/project_full_notes_30march.md` |
| `docs/internal/refactor_discovery_report.md` | `docs/internal/archive/refactors/refactor_discovery_report.md` |
| `docs/internal/thesis_31_template_adaptation_note.md` | `docs/internal/archive/thesis_migrations/thesis_31_template_adaptation_note.md` |

## Files deleted

Only the three files classified `DELETE_SAFE` were deleted:

- `docs/internal/RESTORE.md`
- `docs/internal/thesis_30_literature_review_integration_note.md`
- `docs/internal/thesis_35_format_compliance_audit.md`

## References updated

- `docs/wp5/wp5_notes.md`: the detector-robustness cross-reference now points to `docs/internal/project_full_notes_13may.md` Section 7.2 instead of the 12 April notes.
- `docs/internal/project_full_notes_13may.md`: the primary-base pointer now identifies `docs/internal/archive/project_notes/project_full_notes_18april.md` as the historical base.
- `docs/internal/project_full_notes_13may.md`: the supersession table now uses the archived 18 April path and explicitly labels it historical.

Reference checking found no remaining live reference to the removed current locations. Remaining matches are intentional:

- `docs/internal/internal_docs_cleanup_audit.md` contains the cleanup decision record and suggested commands.
- `manuscript/hector_template_migration_audit.md`, `_v2.md`, `_v3.md`, and `_v3b.md` contain historical `git status` snapshots. They were left unchanged as instructed.
- The two updated 13 May references correctly point to the new archived 18 April path.

## Protected evidence verification

The four SHA-256 values recorded in `EVIDENCE_MANIFEST.md` remain unchanged:

| Protected artifact | SHA-256 status |
| --- | --- |
| `results/metrics_detector_compare.csv` | MATCH — `28E7AD40BB47214F8576132846E9E1D4CD643F623CF1187743091FC367A206ED` |
| `docs/internal/wp6_sweep_full/summary_condition_variant.csv` | MATCH — `6DD627E81637A49A60163F58AC1D3EF23B8D694E39AC55BA64FBF808E978C6EA` |
| `docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv` | MATCH — `4BABCAAACE1DD5228C674E2CED9D977236F8D3ACB503C098FAEB06FF6C10B796` |
| `docs/internal/wp6_sweep_full/summary_paired_combined_vs_regime.csv` | MATCH — `2087FEFBE5DC39AF23372EA2D8999AC0F1071D0FEE90BC1B3668F2158130E8F9` |

Result: **4/4 MATCH**. `git status --short` reports no change to any protected path.

## Remaining warnings

- The repository already had a large dirty working tree before this cleanup. This execution did not attempt to normalize or resolve unrelated changes.
- Several moved documents carried pre-existing working-tree modifications. `git mv` preserved their current contents; until the cleanup set is staged, Git may show a staged rename plus an unstaged destination modification (`RM`).
- The original cleanup audit intentionally retains old path names as an audit trail. It should not be interpreted as a live link inventory after execution.

No commit was created.
