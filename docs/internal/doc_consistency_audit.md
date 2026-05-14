# Freshness Audit

Scope: documentation consistency and freshness audit across `README.md`, `CLAUDE.md`, `docs/internal/project_full_notes_13may.md`, `manuscript/thesis_28.pdf`, `manuscript/decisions_log_12.pdf`, and `EVIDENCE_MANIFEST.md`.

Canonical current state used for this audit:

- Latest manuscript: `manuscript/thesis_28.pdf` / Sürüm 28.
- Latest decision log: `manuscript/decisions_log_12.pdf` / Sürüm 28.
- Current consolidated notes: `docs/internal/project_full_notes_13may.md`.
- Audit manifest: `EVIDENCE_MANIFEST.md`.
- Audit-remediation completed through `045ee86 Lane-C: add evidence manifest for audit-remediation chain`.
- Protected Lane C artifacts remained 4/4 SHA256 MATCH during remediation.

No experiment outputs, CSVs, PNGs, model files, protected evidence artifacts, or thesis artifacts were modified by this audit.

## README.md

### Stale items

| Item | Evidence | Canonical current state | Risk |
|---|---|---|---|
| Old manuscript pointer | README says current manuscript is `manuscript/thesis_25.pdf`. | Current manuscript is `manuscript/thesis_28.pdf`. | SAFE |
| Old decision-log pointer | README says decision log is `manuscript/decisions_log_8.pdf`. | Current decision log is `manuscript/decisions_log_12.pdf`. | SAFE |
| Structure stops before WP5.5/WP6 | Structure lists `wp1`-`wp5`; no `wp5_5`, `wp6`, `docs/internal/wp6_sweep_full`, or audit manifest. | WP5.5 and WP6 are complete and decision-relevant. | SAFE |
| No audit-remediation status | README does not mention Lane A/B/C remediation, protected SHA checks, or evidence manifest. | Audit-remediation is completed and documented in `EVIDENCE_MANIFEST.md` and `decisions_log_12`. | SAFE |
| No explicit WP6 completion status | README key results stop at WP5 detector/misspecification; WP6 signal-informativeness sweep is absent. | WP6 full sweep is complete; original informativeness-threshold hypothesis was not supported. | SAFE |
| Detector framing lacks C1 caveat | README lists `rv_dwell` as one of three detector variants but does not state it is auxiliary/offline for the audit caveat. | Main WP4/WP5/WP6 pipelines use causal `rv_baseline`; `rv_dwell` is auxiliary detector comparison only. | NEEDS REVIEW |
| Synthetic-market boundary is implicit | README title and setup imply simulation, but defense-safe wording should explicitly say claims are synthetic-market claims, not live-market trading claims. | Thesis_28 and project notes frame results as synthetic controlled-environment evidence. | SAFE |
| Final thesis claim is compressed as "null result" | README accurately reports the null/equivalence result but does not foreground the final signal-redundancy thesis. | Canonical claim: explicit regime labels add little once `sigma_hat` is observed; evidence supports signal redundancy. | SAFE |

### Suggested updates

| Suggested edit | Classification | Notes |
|---|---|---|
| Replace current manuscript/log line with `thesis_28.pdf` and `decisions_log_12.pdf`. | SAFE | Documentation-only, non-numerical, no evidence impact. |
| Add a short "Current Final State" paragraph: thesis_28, decisions_log_12, evidence manifest, audit-ready, no numerical claim drift. | SAFE | Mirrors canonical manifest. |
| Extend structure list with `wp5_5/` and `wp6/`; optionally mention `docs/internal/project_full_notes_13may.md` and `EVIDENCE_MANIFEST.md`. | SAFE | Documentation-only path freshness. |
| Add WP6 key result: full sweep complete; `combined` below `sigma_only` in informative conditions; threshold hypothesis not supported within tested calibration band. | NEEDS REVIEW | It is canonical, but it adds numerical/interpretive thesis result content to README. |
| Add detector caveat: `rv_baseline` is the causal main-pipeline detector; `rv_dwell` is auxiliary/offline comparison; HMM is robustness comparison. | NEEDS REVIEW | Important for audit defense; wording should match thesis_28/manifest. |
| Add explicit synthetic-boundary line: "Claims are about the controlled synthetic HFMM simulator, not live-market deployment." | SAFE | Non-numerical defense clarity. |
| Reframe "Current finding" into "Final thesis claim" using signal-redundancy wording. | SAFE | Non-numerical if p-values are left unchanged. |

## CLAUDE.md

### Stale items

| Item | Evidence | Canonical current state | Risk |
|---|---|---|---|
| Project overview implies regime-aware adaptation without final null result | Overview says agent observes regime state and adapts; does not mention the final no-advantage/signal-redundancy result. | Final thesis claim is signal redundancy, not regime-aware improvement. | SAFE |
| Work package table stops at WP5 | WP0-WP5 only; no WP5.5 or WP6. | WP5.5 and WP6 are complete and central to final thesis. | SAFE |
| WP3 status says "ablation ready" | WP3 is no longer an intermediate ablation-ready state. | WP3 is done; WP5/WP6 completed downstream. | SAFE |
| Commands omit WP5.5 and WP6 jobs | No `w55_audit`, `w55_runtime`, `w55_calibration`, `w6_sweep_pilot`, `w6_sweep_full`, or `--resume` examples. | Dispatcher supports these jobs and resume. | SAFE |
| Run lifecycle omits resume validation | Describes basic `setup_run()` but not `--resume` or config snapshot mismatch guard. | Resume config validation is a Lane B guardrail. | SAFE |
| Key module paths are obsolete | Lists `src/w1_naive_sweep.py`, `src/w1_as_baseline.py`, `src/w1_compare.py`, and `src/w3_sanity.py`. | Current paths are `src/wp1/...` and `src/wp3/w3_sanity.py`. | SAFE |
| Config table omits current configs | Table stops around `w5_detector_full`; no `w5_eta_regime`, `w5_misspec_mild`, WP5.5, or WP6 configs. | Canonical configs include `w5_eta_regime`, `w5_misspec_mild`, `w55_*`, and `w6_sweep_*`. | SAFE |
| Thesis manuscript section is old | Says source is `scripts/gen_thesis_docx.py`, current version `thesis_25`, decisions log `decisions_log_8`. | Current source is `scripts/gen_thesis_28.py`; current docs are `thesis_28` and `decisions_log_12`. | SAFE |
| Detector causality wording is overbroad | "Non-negotiable: no look-ahead" is stated before all detector variants, while `rv_dwell` has an audit caveat. | Main pipelines use causal `rv_baseline`; `rv_dwell` is auxiliary/offline comparison only. | NEEDS REVIEW |
| No audit-remediation / evidence-manifest section | CLAUDE lacks Lane A/B/C remediation status, protected SHA invariants, and historical `scripts/legacy/` note. | These are canonical in decisions_log_12 and `EVIDENCE_MANIFEST.md`. | SAFE |
| No WP6 interpretation guidance | CLAUDE lacks the full-sweep result and caution around "categorical-channel degradation" being descriptive, not mechanism proof. | Canonical notes and thesis_28 include this nuance. | NEEDS REVIEW |

### Suggested updates

| Suggested edit | Classification | Notes |
|---|---|---|
| Add a "Current Final Finding" block with signal redundancy, synthetic-market boundary, and no regime-label advantage. | SAFE | Non-numerical if it does not alter p-values. |
| Extend Work Package Status through WP5.5 and WP6. | SAFE | Documentation-only status freshness. |
| Update command list with WP5.5/WP6 jobs and `--resume <run_id>` for WP6. | SAFE | Matches dispatcher; no scientific claim change. |
| Replace obsolete module paths with current package paths. | SAFE | Path freshness only. |
| Add WP5.5/WP6 modules to "Key modules". | SAFE | Architecture documentation only. |
| Update config table/schema with `w5_eta_regime`, `w5_misspec_mild`, `w55_audit`, `w55_runtime`, `w55_calibration`, `w6_sweep_pilot`, and `w6_sweep_full`. | SAFE | Documentation-only config coverage. |
| Replace thesis manuscript section with `scripts/gen_thesis_28.py`, `thesis_28`, `decisions_log_12`, and `EVIDENCE_MANIFEST.md`. | SAFE | Documentation-only, non-numerical. |
| Clarify detector causality: causal `rv_baseline` is main; `rv_dwell` is auxiliary/offline; HMM is robustness comparison. | NEEDS REVIEW | Important audit wording; should be copied closely from canonical notes/manifest. |
| Add audit-remediation section with Lane A/B/C, protected SHA 4/4 MATCH, no reruns, no CSV/PNG regeneration. | SAFE | Mirrors evidence manifest. |
| Add WP6 result/caveat summary. | NEEDS REVIEW | It is canonical, but it adds final result interpretation to guidance docs. |

## Cross-document consistency

### Contradictions

| Topic | Contradiction | Risk |
|---|---|---|
| Current manuscript/log | README and CLAUDE point to `thesis_25` / `decisions_log_8`; canonical docs point to `thesis_28` / `decisions_log_12`. | SAFE to fix, potentially dangerous if left stale during defense logistics. |
| Thesis generator | CLAUDE points to `scripts/gen_thesis_docx.py`; canonical current generator is `scripts/gen_thesis_28.py`, while historical generators are in `scripts/legacy/`. | SAFE to fix, potentially confusing during audit. |
| Code paths | CLAUDE lists old root-style WP1/WP3 paths; active repo uses package subfolders. | SAFE to fix, likely confusing for future AI/tool use. |
| Work package completion | CLAUDE stops at WP5; project notes and thesis_28 include WP5.5/WP6 completion. | SAFE to fix. |
| Detector causality | CLAUDE/README do not fully reflect Lane A C1: `rv_dwell` is auxiliary/offline and main pipelines use causal `rv_baseline`. | NEEDS REVIEW; audit-sensitive if phrased carelessly. |

### Missing references

| Missing in README/CLAUDE | Canonical source | Suggested action |
|---|---|---|
| `EVIDENCE_MANIFEST.md` | Evidence manifest | Add short pointer in README and CLAUDE. |
| `docs/internal/project_full_notes_13may.md` | Consolidated notes | Add as canonical project-brain context. |
| WP5.5 audit/calibration/runtime jobs | Project notes, code snapshot, configs | Add module/config/command references. |
| WP6 full sweep and protected summaries | Thesis_28, project notes, protected CSVs | Add final status and cautious interpretation. |
| Audit-remediation Decisions #48-#51 | `decisions_log_12.pdf` | Add short audit status section. |
| Protected SHA invariant | `EVIDENCE_MANIFEST.md` | Add one-line statement, no hashes necessary unless desired. |
| Resume/config validation guardrail | `src/run_context.py`, Lane B | Add to reproducibility section. |

### Ambiguous wording

| Wording | Issue | Safer wording |
|---|---|---|
| "Current finding: null result" | Accurate but undersells positive TOST/equivalence and signal-redundancy framing. | "Final finding: explicit regime labels do not improve PPO beyond `sigma_hat`; TOST and robustness checks support signal redundancy." |
| "The agent observes regime state ... and adapts" | Could imply regime-aware policy success. | "Some variants observe regime labels; final evidence shows the label does not improve performance once `sigma_hat` is present." |
| "No look-ahead -- regime label uses only past data" near all detectors | Does not reflect `rv_dwell` audit caveat. | "Main pipelines use causal `rv_baseline`; `rv_dwell` is retained as auxiliary/offline detector comparison." |
| "Detector robustness full run COMPLETE" | Correct but lacks ANOVA/design caveat and C1 distinction. | Keep result but add causal-main/auxiliary-detector clarification. |

### Obsolete statements

- `README.md`: `thesis_25`, `decisions_log_8`.
- `CLAUDE.md`: `thesis_25`, `decisions_log_8`, `scripts/gen_thesis_docx.py`, old `src/w1_*` / `src/w3_sanity.py` paths, WP table stopping at WP5, config table stopping before WP5.5/WP6.
- `README.md` and `CLAUDE.md`: no mention of the completed audit-remediation sequence, `EVIDENCE_MANIFEST.md`, protected SHA invariant, or `scripts/legacy/` archive status.

## Safe-to-update items

The following are documentation-only, non-numerical, non-destructive, and safe for audit integrity:

| File | Change | Classification |
|---|---|---|
| README.md | Replace `thesis_25` / `decisions_log_8` pointers with `thesis_28` / `decisions_log_12`. | SAFE |
| README.md | Add `EVIDENCE_MANIFEST.md` and `docs/internal/project_full_notes_13may.md` as current orientation docs. | SAFE |
| README.md | Add WP5.5 and WP6 to repository structure. | SAFE |
| README.md | Add synthetic-market boundary wording. | SAFE |
| README.md | Reframe final claim in non-numerical signal-redundancy wording while preserving existing p-values. | SAFE |
| CLAUDE.md | Update old module paths to `src/wp1/...` and `src/wp3/w3_sanity.py`. | SAFE |
| CLAUDE.md | Extend WP status table through WP5.5 and WP6. | SAFE |
| CLAUDE.md | Add WP5.5/WP6 command examples and `--resume` note. | SAFE |
| CLAUDE.md | Update manuscript source/current-version section to `scripts/gen_thesis_28.py`, `thesis_28`, `decisions_log_12`, and `EVIDENCE_MANIFEST.md`. | SAFE |
| CLAUDE.md | Add reproducibility guardrail note for CSVMetricLogger schema consistency and resume config validation. | SAFE |
| CLAUDE.md | Add historical archive note: `scripts/legacy/` is provenance/history, not active execution. | SAFE |

Suggested edits that mention final numerical results or audit-sensitive causality are still documentation-only, but should be reviewed before applying:

| File | Change | Classification |
|---|---|---|
| README.md | Add WP6 numerical summary or paired-test values. | NEEDS REVIEW |
| README.md | Add `rv_dwell` offline/auxiliary caveat. | NEEDS REVIEW |
| CLAUDE.md | Add WP6 numerical summary and interpretation. | NEEDS REVIEW |
| CLAUDE.md | Rewrite detector causality section around Lane A C1 caveat. | NEEDS REVIEW |

No suggested documentation update should touch:

| Target | Classification | Reason |
|---|---|---|
| CSV/PNG/model/result artifacts | DO NOT TOUCH | Protected/scientific evidence artifacts. |
| `thesis_28.*` | DO NOT TOUCH | Current thesis artifact should not be regenerated or altered in this audit. |
| Protected WP6 summary CSVs and `results/metrics_detector_compare.csv` | DO NOT TOUCH | Lane C protected evidence set. |
| Legacy generators under `scripts/legacy/` | DO NOT TOUCH | Historical provenance archive; update references only. |

## Risk assessment

| Suggested edit | Classification | Rationale |
|---|---|---|
| Update old thesis/log filenames in README and CLAUDE | SAFE | Pure freshness fix. |
| Update obsolete code paths in CLAUDE | SAFE | Pure path correction. |
| Add WP5.5/WP6 status rows | SAFE | Matches canonical notes and current code/configs. |
| Add evidence manifest and audit-remediation pointers | SAFE | Matches committed manifest; no numerical change. |
| Add synthetic-market boundary wording | SAFE | Defense-safe clarification; no numerical change. |
| Add signal-redundancy final claim wording | SAFE | Canonical thesis framing; no new numbers. |
| Add exact WP6 numerical results to README/CLAUDE | NEEDS REVIEW | Correct but numerical; review to avoid accidental drift from protected summaries. |
| Rewrite detector section for `rv_dwell` auxiliary/offline caveat | NEEDS REVIEW | Correct and important, but audit-sensitive wording should be precise. |
| Modify thesis_28, PDFs, CSVs, PNGs, models, protected result files | DO NOT TOUCH | Outside documentation audit scope and audit integrity constraints. |

## Final summary

Is the repository documentation internally consistent?

- Partially. `project_full_notes_13may.md`, `thesis_28.pdf`, `decisions_log_12.pdf`, and `EVIDENCE_MANIFEST.md` are mutually aligned on the final thesis claim, WP6 completion, audit-remediation completion, protected evidence invariants, TOST framing, detector robustness, synthetic-market boundary, and signal-redundancy interpretation.
- `README.md` is mostly numerically consistent with WP5/WP5.5 claims but stale on current manuscript/log, missing WP6, and missing audit-remediation context.
- `CLAUDE.md` is significantly stale as a codebase guidance document: it predates WP5.5/WP6, old path moves, resume/config validation, current thesis artifacts, and audit-remediation notes.

Which files are outdated?

- `README.md`: moderately outdated.
- `CLAUDE.md`: strongly outdated.
- `docs/internal/project_full_notes_13may.md`: current and should be treated as canonical for future updates.
- `thesis_28.pdf`, `decisions_log_12.pdf`, `EVIDENCE_MANIFEST.md`: current canonical references for this audit.

Are any stale statements potentially dangerous during thesis defense/audit?

- Yes. The old `thesis_25` / `decisions_log_8` references could confuse final-version provenance.
- Yes. CLAUDE's old generator reference (`scripts/gen_thesis_docx.py`) and old root-style source paths could mislead future tooling or AI context.
- Yes. Detector-causality wording that does not distinguish causal `rv_baseline` from auxiliary/offline `rv_dwell` is audit-sensitive because it touches Lane A C1.
- README's missing WP6/audit-remediation context is less dangerous but makes the public project overview incomplete relative to the final thesis state.
