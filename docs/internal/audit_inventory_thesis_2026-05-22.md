# Audit Inventory — Thesis (`main` branch)

**Audit date:** 2026-05-22
**Branch audited:** `main` (HEAD = `27c11bd`)
**Mode:** read-only

---

## 1. Git state

### 1.1 Working tree
- Branch: `main`, up-to-date with `origin/main`
- Tracked files: **clean** (no modifications, no staged)
- Untracked: `HFMM_REALDATA/` (entire directory) — ✓ expected; this directory is only tracked on the `realdata-v1` branch (see Step 3 cross-branch summary)

### 1.2 Last 15 commits
```
27c11bd docs: add FREEZE_METADATA.md anchor for thesis-v29-frozen baseline
9681faa docs: Lane C final polish — provenance index + legacy + ownership refs   ← thesis-v29-frozen
ecac138 scripts: extend protected-output overwrite warnings to 3 eval/figure scripts
41e5455 docs: B5/B6 freshness patches + AGENTS.md tracking + lockfile ignore
cbf44ed Audit follow-up: record rationale for 4 manuscript deletions in 5d85c63
4cfa911 Housekeeping: remove GEMINI.md, update local claude settings
5d85c63 Defense artifact freeze: thesis_29 + decisions_log_13 + audit chain
33d35e0 Defense-readiness final verification report (11-step audit)
c697b6a Lane C remediation: add protected-output warning to WP6 plot scripts
045ee86 Lane-C: add evidence manifest for audit-remediation chain
1c259cd Lane-C: add decisions_log_12 audit remediation record
e0c47c5 Lane-C: standardize WP2 per-run provenance artifact naming
dca37b6 Lane-C: parameterize hardcoded run paths in 3 active scripts (argparse with byte-identical defaults)
5ac5bcb Lane-C: move historical thesis and decisions-log generators to scripts/legacy/ (23 files); add README
43ad288 Lane-C: clarify figure_thesis*.py ownership scope in headers (Fig 1-5 / Fig 6-9); declare WP6 boundary
```

### 1.3 Frozen tag verification — `thesis-v29-frozen`
- ✓ Commit: `9681faab6ca3509f9721b03c4e7c6d37f01d3b6d` (matches expected `9681faa`)
- Author: Onur <onureemiroglu@gmail.com>
- Date: 2026-05-17 03:55:14 +0300
- Subject: `docs: Lane C final polish — provenance index + legacy + ownership refs`
- 5 files changed, 31 insertions, 10 deletions (figure_provenance_audit.md, scripts/legacy/README.md, scripts/legacy/gen_thesis_28.py [moved], src/wp5/figure_thesis*.py)
- ⚠ Note: 1 commit (`27c11bd`) sits **on top of** the frozen tag on `main`. This is a docs-only commit adding `FREEZE_METADATA.md` as an anchor. Acceptable as post-freeze housekeeping; flagged for awareness only.

### 1.4 Unpushed commits
- ✓ `git log origin/main..HEAD` → empty. Local `main` is in sync with remote.

---

## 2. Files & integrity (Section 1.5)

| Status | Path | Last modified | SHA256 |
|---|---|---|---|
| ✓ | `manuscript/thesis_29.pdf` | 2026-05-13 23:07:44 | `5540ba8cd85497b46188e615a1bf40c2b711f50d5db857bb59f1bbc10aa996f3` |
| ✓ | `manuscript/decisions_log_13.pdf` | 2026-05-13 23:07:52 | `0a66cabd751bb5b86e86a38029848718887e81922ffa1b83d03d7dc54726a294` |
| ⚠ | `docs/internal/EVIDENCE_MANIFEST.md` | — | **NOT at this path**; located at repo root: `EVIDENCE_MANIFEST.md` (sha `4b55d3454f7762becd9ff8a3b923906b445c9e15056ca4dca5b04a6b955bec04`, mtime 2026-05-16 18:59:04). CLAUDE.md confirms root location. |
| ✓ | `docs/internal/figure_provenance_audit.md` | 2026-05-17 03:51:19 | `3ff19e82960e55f22288e42cb5aee31959fee1e1eda0fd22071a52648f3f6f25` |
| ✓ | `docs/internal/defense_claim_matrix.md` | 2026-05-16 19:23:14 | `fdae35f45dd15b8aa9c98739c1bf11977e459df7b1df45c621f0312bc6120ff7` |
| ✓ | `docs/internal/defense_risk_register.md` | 2026-05-16 19:23:15 | `b145aad7556bb23c909990612245a39050779d8c711b43c363124ac8d28776d3` |
| ✓ | `docs/internal/repo_freeze_recommendation.md` | 2026-05-16 19:23:15 | `8daa87e05f620a10a97bd96814b23adc4903429cefe1649111a95d396110d6ce` |
| ⚠ | `docs/internal/FREEZE_METADATA.md` | — | **NOT at this path**; located at repo root: `FREEZE_METADATA.md` (sha `f492f0ad26acbb53f198e672336e58bf60be1d76a7937d7983411ccc60ee1e56`). Added in commit `27c11bd` (the post-freeze docs commit). |
| ⚠ | `docs/wp6_notes.md` | — | **NOT at this path**; located at `docs/wp6/wp6_notes.md` (sha `958bf36ffe1469ce86e39f76205df38698480aa6dea0f42d6059f24c7806fc5b`, mtime 2026-05-10 21:40:12). |
| ✓ | `README.md` | 2026-05-16 18:59:04 | `43bef21f0ec2c2b3ba9373d17637be088e1aef4127ca2f8af8013f99bf61720b` |
| ✓ | `CLAUDE.md` | 2026-05-16 18:59:04 | `d59dfac96c278cade02b434c6e17a1de56c68797f26439acd27ecaeec374f7c7` |
| ✓ | `AGENTS.md` | 2026-05-16 22:42:11 | `e8a5907e4b4fd140b99d583e5d2ad2a38681e6f2e5973d1d9eabef4d0928718d` |
| ✓ | `results/metrics_detector_compare.csv` | 2026-05-12 14:30:50 | `28e7ad40bb47214f8576132846e9e1d4cd643f623cf1187743091fc367a206ed` |
| ✓ | `results/stats_detector_robustness.txt` | 2026-05-12 14:30:50 | `52776247f005fa70713aecc933d5a23ab9e8863f33a3e3516b656fd0f06cec4d` |

### project_full_notes_*.md (glob expansion)

| Tag | Path | Last modified | SHA256 |
|---|---|---|---|
| **CURRENT** | `docs/internal/project_full_notes_13may.md` | 2026-05-16 19:23:14 | `9d693da912dfd1cc39dfd858cb3da29473c9b5e5fb1ffd8486acba5b6a28c38d` |
| PRIOR | `docs/internal/project_full_notes_18april.md` | 2026-04-17 15:50:06 | `a9bb8c4f1550893f6ce7013b2ddec768a8e4a5a8d74f2f003dd9893cf935b27a` |
| PRIOR | `docs/internal/project_full_notes_12april.md` | 2026-04-14 01:45:10 | `c164f659c0c693a663ff0a928fa7429a7deb4af03dd0a8191a025018adaf5684` |
| PRIOR | `docs/internal/project_full_notes_30march.md` | 2026-04-14 01:44:12 | `6e529199729ef179848b2cf580d3d6a0d8627a35fc2da7695a00c964a5bc2d10` |
| PRIOR | `docs/internal/project_full_notes_17march.md` | 2026-04-14 01:44:12 | `5c19b2fbdd1fbf2863f8d4a3d6fe8e85e241b4fb7e682651156dc1bdcb6d842b` |

Total: 1 CURRENT + 4 PRIOR. Housekeeping decision deferred to user.

### 1.6 `src/` + `scripts/` top-level (1 level deep)

**`src/`** (subdirs only): `wp0/`, `wp1/`, `wp2/`, `wp3/`, `wp4/`, `wp5/`, `wp5_5/`, `wp6/`
Top-level files: `__init__.py`, `run_context.py`

**`scripts/`** (subdirs + files):
- Subdirs: `legacy/`, `office/`
- Files: `eval_only_seed1to7.py`, `gen_decisions_log_13.py`, `gen_project_summary.py`, `gen_thesis_29.py`, `wp6_plot1_monotonic_gap.py`, `wp6_plot2_paired_seed.py`, `wp6_plot3_paired_seed_vs_regime.py`

### 1.7 `config/*.json` (21 files)
`base.json`, `w1_as_baseline.json`, `w1_compare.json`, `w1_naive_sweep.json`, `w2_synth.json`, `w3_sanity.json`, `w3_sanity_both.json`, `w4_ppo.json`, `w55_audit.json`, `w55_calibration.json`, `w55_runtime.json`, `w5_ablation_eta.json`, `w5_ablation_skew.json`, `w5_detector_full.json`, `w5_detector_pilot.json`, `w5_eta_regime.json`, `w5_eval.json`, `w5_main.json`, `w5_misspec_mild.json`, `w6_sweep_full.json`, `w6_sweep_pilot.json`

All 21 configs match the table in CLAUDE.md ✓.

---

## Open questions

1. **Path mismatch — EVIDENCE_MANIFEST.md.** Plan listed `docs/internal/EVIDENCE_MANIFEST.md`; actual location is repo root. CLAUDE.md confirms root. Just a plan-path typo? Or did the file used to live in `docs/internal/` and get moved?
2. **Path mismatch — FREEZE_METADATA.md.** Same situation: listed as `docs/internal/FREEZE_METADATA.md`, actually at repo root.
3. **Path mismatch — wp6_notes.md.** Listed as `docs/wp6_notes.md`, actually at `docs/wp6/wp6_notes.md`.
4. **Extra local branch `thesis-25-tost-recompute`.** Visible in `git branch -a`; no remote counterpart. Stale work branch? Safe to delete or keep around?
5. **4 PRIOR `project_full_notes_*.md` versions.** Housekeeping opportunity: archive/delete or keep as historical record?
6. **1 commit on top of `thesis-v29-frozen`.** `27c11bd` (FREEZE_METADATA.md anchor) is post-freeze. Intentional (docs anchor describing the freeze) but means `main` HEAD ≠ frozen tag. Worth a written note in the manifest?

---

## Step 3 — Branch comparison summary

- `git branch -a`: local = `main`, `realdata-v1`, `thesis-25-tost-recompute`; remotes = `origin/main`, `origin/realdata-v1`. No `origin/thesis-25-tost-recompute`.
- `git tag -l`: `thesis-v29-frozen`, `realdata-v1-phase1a-frozen` (2 tags total).
- `git merge-base main realdata-v1` = `9681faab6ca3509f9721b03c4e7c6d37f01d3b6d` — exactly the `thesis-v29-frozen` commit. ✓ `realdata-v1` was forked cleanly from the frozen baseline.
- `git diff main realdata-v1 --stat` (first 30 lines): differences are (a) `.claude/settings.local.json` + `.gitignore` deltas, (b) entire `HFMM_REALDATA/` tree added on `realdata-v1`, (c) `FREEZE_METADATA.md` present on `main`, absent on `realdata-v1` (because `27c11bd` was committed only after fork). No thesis-side code/data was modified on `realdata-v1`. ✓ Thesis chain integrity preserved.
