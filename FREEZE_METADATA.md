# Thesis-v29 Freeze Metadata

This file records the canonical baseline state of the synthetic-market
thesis repository after full audit closure. Post-thesis work — including
the real-data extension and any paper-direction follow-up — branches from
this baseline.

## Freeze coordinates

- **Tag:** `thesis-v29-frozen`
- **Commit (HEAD at freeze):** `9681faab6ca3509f9721b03c4e7c6d37f01d3b6d`
- **Short hash:** `9681faa`
- **Tag date:** `2026-05-17 03:58:09 +0300`

## Canonical artifacts

- Manuscript: `manuscript/thesis_29.pdf`
- Decision log: `manuscript/decisions_log_13.pdf`

## Audit closure summary

- Statistical recompute checks: PASS (5 spot-checks, ~56 cells reconciled
  against primary CSVs)
- Terminology discipline: PASS (forbidden mechanism-laden terms appear
  only inside Section 5.2 avoidance disclaimer)
- Provenance chain: SHA-protected artifacts registry
  (`EVIDENCE_MANIFEST.md`) + per-figure mapping
  (`docs/internal/figure_provenance_audit.md`) + claim ↔ run-id
  traceability (`docs/internal/defense_claim_matrix.md`)
- Working tree: clean
- Reproducibility chain: documented in `docs/internal/`

## How to use this anchor

When starting post-thesis work, branch from this tag:

    git checkout -b <branch-name> thesis-v29-frozen

When citing the frozen baseline in a paper or follow-up document, refer
to the tag name rather than a commit hash — the tag is the immutable
handle.
