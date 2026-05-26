# Audit Inventory — Real-Data Extension (`realdata-v1` branch)

**Audit date:** 2026-05-22
**Branch audited:** `realdata-v1` (HEAD = `f95d4bd`)
**Mode:** read-only

---

## 1. Git state

### 2.1 Working tree
- Branch: `realdata-v1`, up-to-date with `origin/realdata-v1`
- ✓ Working tree clean (no modifications, no untracked).

### 2.2 Last 15 commits
```
f95d4bd Housekeeping: harness auto-update to claude settings
2fa2b41 phase1a closure: BTCUSDT-perp cross-venue cadence symmetry + finding   ← realdata-v1-phase1a-frozen
ce50884 phase1a_perp: probe + download binance-futures BTCUSDT
f787d64 [realdata] step 05.5: clock-time resampled spread sanity check (raw/100ms/500ms/1000ms cadences)
07b2284 [realdata] step 05: sample inspection report + spread degeneracy histograms (ETHUSDT spot, 3 days, P(spread=1tick) ≈ 99.4-99.84%)
c0b6908 [realdata] step 04.5: book_snapshot_5 probe + download for ETHUSDT spot (free-tier confirmed, manifest now 9 entries)
0b27a2a [realdata] step 04: download ETHUSDT spot Group C (3 days × 2 datatypes, 323 MB), manifest tracked
bc6ff18 [realdata] step 03: GET-stream URL probe, 10/10 OK across binance spot + binance-futures, ETHUSDT free-tier confirmed
b7cd4b4 [realdata] step 01-02: branch already at thesis-v29-frozen (a632d2d), bootstrap directory structure
9681faa docs: Lane C final polish — provenance index + legacy + ownership refs   ← thesis-v29-frozen (= fork point)
ecac138 scripts: extend protected-output overwrite warnings to 3 eval/figure scripts
41e5455 docs: B5/B6 freshness patches + AGENTS.md tracking + lockfile ignore
cbf44ed Audit follow-up: record rationale for 4 manuscript deletions in 5d85c63
4cfa911 Housekeeping: remove GEMINI.md, update local claude settings
5d85c63 Defense artifact freeze: thesis_29 + decisions_log_13 + audit chain
```

### 2.3 Frozen tag verification — `realdata-v1-phase1a-frozen`
- ✓ Commit: `2fa2b4190f1e62e218b05a0a9a4a55e08d379ba9` (matches expected `2fa2b41`)
- Author: Onur <onureemiroglu@gmail.com>
- Date: 2026-05-21 00:55:01 +0300
- Subject: `phase1a closure: BTCUSDT-perp cross-venue cadence symmetry + finding`
- 9 files changed, 771 insertions, 56 deletions. Includes BTCUSDT-perp processed/, REAL_DATA_FINDING.md, and 02_sample_inspect.py + 03_clocktime_resample.py PROFILES refactor.
- ⚠ Note: 1 commit (`f95d4bd Housekeeping: harness auto-update to claude settings`) sits **on top of** the frozen tag. Non-substantive (claude harness settings). Flagged for awareness; consider whether the freeze line should be re-tagged or kept anchored to `2fa2b41`.

### 2.4 Unpushed commits
- ✓ `git log origin/realdata-v1..HEAD` → empty. Local branch is in sync with remote.

---

## 2. HFMM_REALDATA structure (Section 2.5, depth 3)

```
HFMM_REALDATA
├── data
│   ├── phase1a_btcusdt_perp
│   │   ├── processed
│   │   └── raw
│   ├── processed                     ← ETHUSDT spot output (asymmetric: no phase1a_ethusdt_spot/ wrapper)
│   └── raw                           ← ETHUSDT spot raw
├── docs
├── notebooks
│   └── __pycache__
├── specs
└── src
    └── realdata
```

⚠ Asymmetric layout: BTCUSDT-perp is namespaced under `phase1a_btcusdt_perp/`, but ETHUSDT spot data sits directly under `data/raw/` and `data/processed/`. Most likely historical (ETHUSDT was the original Phase 1A subject, BTCUSDT-perp added later as separate dir). Flagged in open questions.

---

## 3. Deliverable integrity (Section 2.6-2.7)

| Status | Path | Last modified | SHA256 |
|---|---|---|---|
| ✓ | `HFMM_REALDATA/docs/REAL_DATA_FINDING.md` | 2026-05-22 21:08:29 | `dfecb72bdbb5cab7b4f3cf5ef2e9375314705af6b6e5c62994a3da62127bf0d8` |
| ✓ | `HFMM_REALDATA/data/raw/_manifest.json` | 2026-05-22 21:08:29 | `01f055af299f7eea16115fa0b92d28694ed717c36815dd497838003149852123` |
| ✓ | `HFMM_REALDATA/data/phase1a_btcusdt_perp/raw/_manifest.json` | 2026-05-22 21:08:29 | `9ce525ad3a001108b1c6a20d42e82882370f4afce68fa4c4fe03fdb1b9768152` |
| ✓ | `HFMM_REALDATA/data/phase1a_btcusdt_perp/processed/STEP5_SUMMARY.md` | 2026-05-22 21:08:28 | `20a2836d54ce05ed0d8a8431d6dfdd5b565cf5c935475ecd9208e692844c4559` |
| ✓ | `HFMM_REALDATA/data/phase1a_btcusdt_perp/processed/step5_inspection_report.txt` | 2026-05-22 21:08:29 | `52f7d48226f9f8ab35ddae1fa1dca45acca775a9fb150988ea2cc79876e78f9d` |
| ✓ | `HFMM_REALDATA/data/phase1a_btcusdt_perp/processed/step5_5_clocktime_sanity_report.txt` | 2026-05-22 21:08:29 | `8ed44667435e973bdbe0c8093c47568e2b2df4dfadfc56c1f7ec293f6f73f675` |

(Note: mtimes are 2026-05-22 because the files were re-materialized by `git checkout realdata-v1` during this audit. Hashes are the authoritative integrity check.)

### Manifest entry counts (Section 2.7)
- ✓ ETHUSDT manifest `HFMM_REALDATA/data/raw/_manifest.json`: **9 entries** (`files[]`), matching expected
  - Datatypes: incremental_book_L2 × 3 dates, trades × 3 dates, book_snapshot_5 × 3 dates (2024-03-01, 2024-06-01, 2024-09-01)
- ✓ BTCUSDT-perp manifest `HFMM_REALDATA/data/phase1a_btcusdt_perp/raw/_manifest.json`: **9 entries** (`files[]`), matching expected

(Plan listed "entry count"; actual JSON key is `files`. No data discrepancy, only terminology — calling it out so the next audit uses the right key.)

---

## 4. Pipeline scripts (Section 2.8)

| Path | Last modified |
|---|---|
| `HFMM_REALDATA/notebooks/00_tardis_url_check.py` | 2026-05-22 21:08:28 |
| `HFMM_REALDATA/notebooks/01_tardis_download.py` | 2026-05-22 21:08:28 |
| `HFMM_REALDATA/notebooks/02_sample_inspect.py` | 2026-05-22 21:08:28 |
| `HFMM_REALDATA/notebooks/03_clocktime_resample.py` | 2026-05-22 21:08:28 |

All 4 expected scripts present. (mtimes reflect checkout time; for last-content-change date, see git log.)

---

## Open questions

1. **Asymmetric data layout.** ETHUSDT spot lives at `data/raw/` + `data/processed/` (no venue-prefixed wrapper), while BTCUSDT-perp uses `data/phase1a_btcusdt_perp/raw/` etc. Likely historical; do we want to rename ETHUSDT side to `data/phase1a_ethusdt_spot/` for symmetry before Phase 1B, or keep as-is?
2. **`f95d4bd` on top of frozen tag.** The post-freeze commit is non-substantive (harness settings auto-update). Worth noting in a frozen-anchor doc, or just leave it? Should we re-tag, or is `2fa2b41` permanently the freeze line?
3. **`__pycache__/` under `notebooks/`.** Not a problem, but check `.gitignore` coverage if it ever gets staged.

---

## Step 3 — Branch comparison summary

- `git branch -a`: local = `main`, `realdata-v1`, `thesis-25-tost-recompute`; remotes = `origin/main`, `origin/realdata-v1`. No `origin/thesis-25-tost-recompute`.
- `git tag -l`: `thesis-v29-frozen`, `realdata-v1-phase1a-frozen` (2 tags total).
- `git merge-base main realdata-v1` = `9681faab6ca3509f9721b03c4e7c6d37f01d3b6d` — exactly the `thesis-v29-frozen` commit. ✓ `realdata-v1` was forked cleanly from the frozen baseline; no thesis code was modified on the real-data branch.
- `git diff main realdata-v1 --stat` (first 30 lines): differences are confined to (a) `.claude/settings.local.json` + `.gitignore` deltas, (b) entire `HFMM_REALDATA/` tree added on `realdata-v1`, (c) `FREEZE_METADATA.md` absent on `realdata-v1` (because `main`'s `27c11bd` was committed only after the fork). ✓ Thesis chain integrity preserved.
