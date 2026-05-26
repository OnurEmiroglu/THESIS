# Decisions Log 14 — Post-Freeze Documentation Hygiene Addendum

## 1. Context and Baseline

Frozen thesis baseline: `thesis-v29-frozen`

Baseline commit: `9681faa`

Frozen artifacts:
- `manuscript/thesis_29.pdf`
- `manuscript/thesis_29.docx`
- `manuscript/decisions_log_13.pdf`
- `manuscript/decisions_log_13.docx`

This addendum is documentation-only. It records post-freeze documentation hygiene and does not supersede `decisions_log_13` unless it is later reviewed and promoted to a manuscript artifact.

## 2. Branch Purpose

Branch: `docs-hygiene-wave1`

Purpose: post-freeze documentation hygiene, provenance clarification, and defense-readiness notes.

No experiments were run, no artifacts were regenerated, and no numerical thesis claims were changed.

## 3. Commit Sequence on docs-hygiene-wave1

| Step | Commit | Summary | Files/Scope | Evidence Impact |
|---|---|---|---|---|
| Freeze anchor context | `9681faa` | Lane C final polish / `thesis-v29-frozen` baseline | Frozen baseline context | Documentation/provenance only |
| Freeze metadata anchor | `27c11bd` | Add `FREEZE_METADATA.md` anchor | Freeze metadata documentation | No protected evidence modified |
| C1 | `4cb7996` | Document deliberate zero one-hot for warmup; align `regime_source` terminology | WP3 regime-channel comments/docs | No numerical claim change; no experiment rerun |
| C2 | `29e63bb` | Upgrade freshness anchors to audit-traceable form | Documentation freshness anchors | Documentation/provenance only |
| C3 | `f2bb0ea` | Update figure provenance to current generator | Figure provenance documentation | No protected evidence modified |
| C5 | `eecf51c` | Tighten two WP6 wording cases; 19 of 21 already defense-safe | WP6 documentation wording | No numerical claim change |
| C6 | `965d929` | Document `wp2_synth.csv` as convenience alias, not frozen evidence | WP2 comment/docs provenance note | No protected evidence modified; no experiment rerun |
| C7 | `a6c6a6f` | Add canonical-rerun warning to WP5 evaluation scripts | WP5 top comments and notes | Documentation/provenance only; no code logic change |
| C8 | `11b3a24` | Add thesis and real-data audit inventory reports | Audit inventory Markdown reports | No protected evidence modified; no numerical claim change |

## 4. C4 Branch Split

C4 lives separately on branch `realdata-v1` at commit `9cd5542`.

C4 summary: correct frozen tag references in real-data docs.

C4 is intentionally not part of `docs-hygiene-wave1`. The `docs-hygiene-wave1` branch continued from `main` after `27c11bd`, while `realdata-v1` forked from the frozen baseline `9681faa`.

This separation prevents real-data exploration from contaminating the documentation-hygiene branch.

## 5. Protected Evidence Invariant

Protected SHA256 verification remained `4/4 MATCH` after relevant steps.

Protected artifacts:
- `docs/internal/wp6_sweep_full/summary_condition_variant.csv`
- `docs/internal/wp6_sweep_full/summary_paired_combined_vs_regime.csv`
- `docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv`
- `results/metrics_detector_compare.csv`

No protected CSV, canonical run directory, plot, model, metrics file, or manuscript artifact was modified.

## 6. WP2 Output Provenance Clarification

C6 clarified that `data/processed/wp2_synth.csv` is a convenience/latest snapshot alias.

That file is overwritten by WP2 runs. It is not frozen evidence and is not audit-traceable.

The run-specific frozen provenance copy is under `ctx.run_dir/wp2_synth.csv`, i.e. under `results/runs/<run_id>/`.

## 7. WP5 Canonical Rerun Warning

C7 clarified that WP5 evaluation and figure scripts can produce fresh outputs if rerun from `HEAD`.

Such outputs must not be treated as canonical `thesis_29` evidence.

Canonical claims must reference frozen run directories and evidence manifest/provenance records.

Reruns are allowed only for pilot/exploration work or explicit reproducibility verification against frozen hashes.

## 8. Real-Data Directory Handling

`HFMM_REALDATA/` remains intentionally untracked on `docs-hygiene-wave1`.

The real-data audit inventory was added as documentation only.

Real-data files themselves were not added to the thesis branch.

## 9. Current End State

HEAD after C8: `11b3a24`

Branch: `docs-hygiene-wave1`

Tracked tree clean.

Only untracked item: `HFMM_REALDATA/`.

No merge to `main` yet.

No push to `origin` yet.

`decisions_log_14` manuscript artifact has not been generated yet.

## 10. Recommended Next Step

Review and commit this Markdown addendum first.

Only after review, decide whether to promote it into `manuscript/decisions_log_14.docx` / `manuscript/decisions_log_14.pdf`.

Merge and push should happen only after the documentation record is approved.
