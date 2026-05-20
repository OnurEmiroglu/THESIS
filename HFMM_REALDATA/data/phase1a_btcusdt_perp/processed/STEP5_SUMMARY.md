# Phase 1A Step 5 summary — BTCUSDT perpetual futures

## Dataset
- Venue: Binance Futures
- Symbol: BTCUSDT (perpetual)
- Dates: 2024-03-01, 2024-06-01, 2024-09-01
- Datatypes: incremental_book_L2, trades, book_snapshot_5
- Manifest: ../raw/_manifest.json (9 entries, schema v1)
- Source script: HFMM_REALDATA/notebooks/02_sample_inspect.py
              + HFMM_REALDATA/notebooks/03_clocktime_resample.py
- Canonical tick: 0.10 USDT (documented Binance Futures BTCUSDT-perp
  tick; per-date inference reported as diagnostic only)

## Probe (Step 1, commit ce50884)

9/9 URLs returned HTTP 200. Total payload: 1,651,422,208 bytes
(~1.54 GiB compressed). Per-file detail in ../raw/_manifest.json.

## Spread analysis — event time (Step 3)

Source: step5_inspection_report.txt

| Date       | Rows used  | P(spread=1 tick) | Median ticks |
|------------|------------|------------------|--------------|
| 2024-03-01 | 1,408,663  | 99.43%           | 1.0          |
| 2024-06-01 | 1,134,184  | 99.90%           | 1.0          |
| 2024-09-01 | 1,303,118  | 99.43%           | 1.0          |

Tick agreement (gcd vs min-diff vs documented):

| Date       | gcd     | min-diff | inferred == documented |
|------------|---------|----------|------------------------|
| 2024-03-01 | 0.10    | 0.03     | False (off-grid contamination) |
| 2024-06-01 | 0.10    | 0.10     | True                   |
| 2024-09-01 | 0.10    | 0.10     | True                   |

2024-03-01 LOUD WARN fired (inferred != documented); proceeded with
documented tick = 0.10 USDT per the canonical-tick policy.

## Spread analysis — clock time (Step 4)

Source: step5_5_clocktime_sanity_report.txt

P(spread = 1 tick) at each (cadence, date) cell:

| Cadence | 2024-03-01 | 2024-06-01 | 2024-09-01 |
|---------|-----------:|-----------:|-----------:|
| raw     | 99.43%     | 99.90%     | 99.43%     |
| 100ms   | 99.55%     | 99.93%     | 99.56%     |
| 500ms   | 99.58%     | 99.94%     | 99.58%     |
| 1000ms  | 99.56%     | 99.94%     | 99.61%     |

Round→0 (sub-tick spread) counts: 0 in every (cadence, date) cell.
Off-grid contamination on 2024-03-01 did not propagate to clock-time
rounding artifacts.

## Volume / activity context

Source: step5_inspection_report.txt (trades section)

| Date       | Trades rows | Trades/sec (avg) | L2 rows     |
|------------|------------:|-----------------:|------------:|
| 2024-03-01 | 4,242,506   | 49.10            | 127,800,787 |
| 2024-06-01 | 851,468     | 9.85             | 43,804,103  |
| 2024-09-01 | 2,973,388   | 34.41            | 99,540,679  |

Time coverage: 23.999 hours per date (within ~1 second of full day).

## Cross-reference

See ../../../docs/REAL_DATA_FINDING.md for the methodological
interpretation and the cross-venue (ETHUSDT spot + BTCUSDT-perp)
synthesis.
