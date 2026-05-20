# Real-data finding: structural one-tick spread dominance in liquid crypto majors

## Status
Phase 1A closure of the real-data extension to thesis_29 (frozen at tag
`thesis-v29-frozen`).

## Finding

Across both ETHUSDT spot and BTCUSDT perpetual futures on Binance, the
probability that the top-of-book spread equals one tick exceeded 99.4%
in every measurement cell tested — 24 cells in total, covering 4 sampling
cadences (event-time, 100ms, 500ms, 1s) and 3 first-of-month dates
(2024-03-01, 2024-06-01, 2024-09-01).

| Cadence | ETHUSDT spot | BTCUSDT-perp |
|---------|--------------|--------------|
| raw     | 99.40 – 99.84% | 99.43 – 99.90% |
| 100ms   | 99.53 – 99.91% | 99.55 – 99.93% |
| 500ms   | 99.52 – 99.92% | 99.58 – 99.94% |
| 1000ms  | 99.55 – 99.92% | 99.56 – 99.94% |

The two venues have different documented tick sizes (0.01 USDT for
ETHUSDT spot, 0.10 USDT for BTCUSDT-perp), different product types
(spot vs perpetual futures), and different liquidity profiles. Despite
these differences, one-tick spread dominance was consistent in both
direction (always > 99.4%) and magnitude (within ~0.5pp of each other
in every cell).

## Methodological implications

The synthetic environment in thesis_29 assumes a meaningful
spread-placement action space: the agent chooses among five half-spread
values (h ∈ {1,2,3,4,5} ticks), and the fill model rewards tighter
spreads with higher arrival intensity (λ(δ) = A·exp(-k·δ)). This
assumption is internally well-defined and the thesis results follow
correctly from it.

The Phase 1A finding suggests that in liquid crypto majors during the
2024 sample period, this action space may be structurally collapsed:
the top-of-book is at the minimum allowed tick the overwhelming majority
of the time, so a spread-placement decision is rarely a decision at all.
An RL agent that learns half-spread policy under these conditions would
spend most of its training updates in a degenerate regime where all
non-minimum half-spreads receive zero fills.

This does NOT contradict thesis_29's central claim. The thesis result —
that explicit regime labels are redundant when the regime signal is
implicit in the observation space (via σ̂) — holds within the synthetic
environment as a conditional statement. The Phase 1A finding instead
constrains the empirical applicability of the spread-placement
formulation itself, independent of the regime-label question.

A more direct real-data extension of thesis_29 would require either:
- A venue with a meaningfully wider average spread in tick units
  (likely lower-liquidity instruments, traditional FX, or equity small-
  caps — none of which were tested in this work), or
- A different action space formulation where the agent's decision is
  not spread placement but, e.g., queue priority, cancellation timing,
  or aggressive vs passive order type selection (a microstructure
  reformulation, outside this thesis scope).

## Notes on robustness

- The 2024-03-01 BTCUSDT-perp data showed off-grid contamination at the
  price-grid level (21,266 distinct prices vs ~4-17k on the other
  dates; min-diff = 0.03 USDT vs the documented tick of 0.10 USDT).
  This was diagnosed as a data-quality artifact (likely upstream
  reconstructor or float-precision rounding), not a venue-level tick-size
  change. Under banker's rounding, no rows in any cell collapsed to a
  sub-tick spread, so the contamination did not bias the P(spread = 1
  tick) measurement.

- ETHUSDT spot artifacts from the previous run were verified
  byte-immutable across the BTCUSDT-perp re-runs (sha256 + mtime
  checks).

- Both event-time and clock-time sampling were tested. Clock-time
  resampling did not relax the degeneracy; in most cells it slightly
  intensified it (a last-tick semantics effect — the agent sees the
  most recent observed top-of-book, which is typically at 1 tick).

## Position in the broader research program

This finding is an empirical scope-boundary observation for the
synthetic-environment thesis. It does not invalidate any prior result;
it constrains the conditions under which the synthetic action space
maps to real markets. Two post-thesis directions remain open:

1. **Microstructure reformulation**: replace the spread-placement
   action space with a queue-priority / cancellation / aggression
   action space, on the same venues. This would be a substantive
   research project, not a thesis extension.

2. **Spread-meaningful venue search**: locate a venue where the
   spread-placement action space remains non-degenerate at relevant
   trading cadences (likely outside the major-crypto universe). This
   would extend the thesis claim to real-data conditions.

The author has not committed to either direction at the time of this
write-up.

## Reproducibility

- Branch: `realdata-v1`
- Tag (Phase 1A closure): `phase1a-frozen` (TBD on closure commit)
- Data manifests: `HFMM_REALDATA/data/raw/_manifest.json` (ETHUSDT spot)
  and `HFMM_REALDATA/data/phase1a_btcusdt_perp/raw/_manifest.json`
  (BTCUSDT-perp)
- Analysis scripts: `HFMM_REALDATA/notebooks/02_sample_inspect.py` and
  `HFMM_REALDATA/notebooks/03_clocktime_resample.py`
- Reports: `data/processed/step5_inspection_report.txt`,
  `data/processed/step5_5_clocktime_sanity_report.txt` (ETHUSDT spot);
  `data/phase1a_btcusdt_perp/processed/step5_inspection_report.txt` and
  `data/phase1a_btcusdt_perp/processed/step5_5_clocktime_sanity_report.txt`
  (BTCUSDT-perp).
