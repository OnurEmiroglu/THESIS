# Manuscript Cleanup — Deletion Rationale

Follow-up record for commit `5d85c63` ("Defense artifact freeze: thesis_29 + decisions_log_13 + audit chain"), which included four outright file deletions in `manuscript/` that were not renamed to `manuscript/archive/`.

## Deleted files

- `manuscript/thesis_progress_report_updated.pdf`
- `manuscript/thesis_progress_report_updated.docx`
- `manuscript/signal_sweep_proposal.pdf`
- `manuscript/signal_sweep_proposal.docx`

## Rationale

These were one-off advisor-meeting documents whose content has been subsumed by `thesis_29` (current canonical manuscript). No archive copy is kept because:

- They are not predecessor thesis versions (which are preserved under `manuscript/archive/`).
- Their content is fully reflected in the current thesis and decision log.
- They are recoverable from git history if ever needed.

## Recovery

The last commit where all four files still existed is `045ee86` (parent of `5d85c63`). To recover any of them:

```
git show 045ee86:manuscript/thesis_progress_report_updated.pdf  > recovered_progress_report.pdf
git show 045ee86:manuscript/thesis_progress_report_updated.docx > recovered_progress_report.docx
git show 045ee86:manuscript/signal_sweep_proposal.pdf           > recovered_signal_sweep.pdf
git show 045ee86:manuscript/signal_sweep_proposal.docx          > recovered_signal_sweep.docx
```

## Audit invariants preserved

- No protected CSV was modified by these deletions.
- Lane C 4/4 SHA256 MATCH preserved (verified post-commit on `5d85c63`).
- No experiment was rerun; no manuscript was regenerated.

## Related references

- Final defense-readiness verification report: `docs/internal/final_audit_check/final_check_report.md`.
- Evidence manifest: `EVIDENCE_MANIFEST.md` (unchanged).

### Defense-readiness audit commit chain

| Commit | Role |
|---|---|
| `c697b6a` | Lane C remediation: add protected-output warning to WP6 plot scripts |
| `33d35e0` | Defense-readiness final verification report (11-step audit) |
| `5d85c63` | Defense artifact freeze: thesis_29 + decisions_log_13 + audit chain (this commit included the four manuscript deletions) |
| `4cfa911` | Housekeeping: remove GEMINI.md, update local claude settings |

Pre-chain anchor: `045ee86` (Lane-C evidence manifest commit) — last commit before this audit chain, and the recovery point for the four deleted manuscript files.
