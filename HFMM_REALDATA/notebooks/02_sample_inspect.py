"""Phase 1A Step 5: sample inspection + spread-degeneracy decision gate.

For each of the 3 dates (2024-03-01, 2024-06-01, 2024-09-01) consume the
3 corresponding gzipped CSVs already on disk (per the Step 4 + 4.5 manifest)
and emit a consolidated report covering:

  (a) L2 file inspection      - row counts, time span, inter-update intervals
  (b) Trades file inspection  - row counts, volume, trades-per-second
  (c) Tick size verification  - data-driven, from book_snapshot_5 only
  (d) Top-of-book spread      - P(spread=1 tick), distribution, histogram PNG

Plus a final summary table and an interpretation guide for the human reader.
This script does NOT make a pair-switch decision; the human reads the gate.

Schema notes (confirmed from header inspection, all 3 datatypes for 2024-03-01):
  - incremental_book_L2 columns:
      exchange,symbol,timestamp,local_timestamp,is_snapshot,side,price,amount
      is_snapshot is the lowercase string "true"/"false".
  - trades columns:
      exchange,symbol,timestamp,local_timestamp,id,side,price,amount
  - book_snapshot_5 columns (24 total): the 4 common ones plus
      asks[0..4].price, asks[0..4].amount, bids[0..4].price, bids[0..4].amount
  - timestamp and local_timestamp are microseconds since Unix epoch.
    local_timestamp = exchange message receive time on the Tardis collector;
    timestamp       = exchange-provided ts (may be lower-resolution / aligned).
    We use local_timestamp for ordering and interval calculations because it is
    monotonic per Tardis collector and reflects real arrival order; we note
    when timestamp would have produced a different answer (it would, slightly).

Hard rules respected:
  - Files under data/raw/ are read-only (no writes back).
  - All emitted timestamps are timezone-aware UTC.
  - Outputs (PNGs + text report) live under data/processed/.
  - All column lookups validate the header before use; no silent guessing.
"""

from __future__ import annotations

import gzip
import io
import json
import math
import sys
from datetime import datetime, timezone
from functools import reduce
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


SCRIPT_DIR = Path(__file__).resolve().parent
HFMM_ROOT = SCRIPT_DIR.parent

# === Dataset profiles (shape matches 01_tardis_download.py) ===
# NUMERIC-LEVEL byte-for-byte preservation under the "ethusdt_spot" profile:
# flipping ACTIVE_PROFILE back yields the same canonical tick (0.01), the same
# rounding policy (np.round / banker's, half-to-even), and the same percentile
# values at the previously-emitted breakpoints (p25/p50/p75/p95/max), so any
# downstream consumer keying off those numeric fields sees identical input.
# The REPORT TEXT now also emits p90/p99 percentile lines, the per-date
# rounding-policy + rounded-to-{0,1,>1} counts, the spread-table preamble line,
# and (when triggered) the LOUD WARN block from infer_tick_size(); these are
# textual additions and do not alter pre-existing numeric output.
# proc_dir + report_basename + fname_prefix are bundled for cross-script
# consistency with notebook 03. documented_tick is the venue spec and is now
# the source of truth for the spread math (NOT the per-date inferred value);
# infer_tick_size() runs as a diagnostic that warns loudly when it disagrees.
PROFILES = {
    "ethusdt_spot": {
        "raw_dir":         HFMM_ROOT / "data" / "raw",
        "manifest_path":   HFMM_ROOT / "data" / "raw" / "_manifest.json",
        "proc_dir":        HFMM_ROOT / "data" / "processed",
        "report_basename": "step5_inspection_report.txt",
        "fname_prefix":    "binance",
        "documented_tick": 0.01,
        "venue_label":     "Binance Spot ETHUSDT",
        "targets": [
            {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2024-03-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2024-06-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2024-09-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "trades",              "date": "2024-03-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "trades",              "date": "2024-06-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "trades",              "date": "2024-09-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "book_snapshot_5",     "date": "2024-03-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "book_snapshot_5",     "date": "2024-06-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "book_snapshot_5",     "date": "2024-09-01", "symbol": "ETHUSDT"},
        ],
    },
    "btcusdt_perp": {
        "raw_dir":         HFMM_ROOT / "data" / "phase1a_btcusdt_perp" / "raw",
        "manifest_path":   HFMM_ROOT / "data" / "phase1a_btcusdt_perp" / "raw" / "_manifest.json",
        "proc_dir":        HFMM_ROOT / "data" / "phase1a_btcusdt_perp" / "processed",
        "report_basename": "step5_inspection_report.txt",
        "fname_prefix":    "binance-futures",
        "documented_tick": 0.10,
        "venue_label":     "Binance Futures BTCUSDT (perp)",
        "targets": [
            {"exchange": "binance-futures", "datatype": "incremental_book_L2", "date": "2024-03-01", "symbol": "BTCUSDT"},
            {"exchange": "binance-futures", "datatype": "incremental_book_L2", "date": "2024-06-01", "symbol": "BTCUSDT"},
            {"exchange": "binance-futures", "datatype": "incremental_book_L2", "date": "2024-09-01", "symbol": "BTCUSDT"},
            {"exchange": "binance-futures", "datatype": "trades",              "date": "2024-03-01", "symbol": "BTCUSDT"},
            {"exchange": "binance-futures", "datatype": "trades",              "date": "2024-06-01", "symbol": "BTCUSDT"},
            {"exchange": "binance-futures", "datatype": "trades",              "date": "2024-09-01", "symbol": "BTCUSDT"},
            {"exchange": "binance-futures", "datatype": "book_snapshot_5",     "date": "2024-03-01", "symbol": "BTCUSDT"},
            {"exchange": "binance-futures", "datatype": "book_snapshot_5",     "date": "2024-06-01", "symbol": "BTCUSDT"},
            {"exchange": "binance-futures", "datatype": "book_snapshot_5",     "date": "2024-09-01", "symbol": "BTCUSDT"},
        ],
    },
}

ACTIVE_PROFILE = "btcusdt_perp"

_active = PROFILES[ACTIVE_PROFILE]
RAW_DIR = _active["raw_dir"].resolve()
PROC_DIR = _active["proc_dir"].resolve()
MANIFEST_PATH = _active["manifest_path"].resolve()
REPORT_PATH = PROC_DIR / _active["report_basename"]
DATES = sorted({t["date"] for t in _active["targets"]})
_TARGETS_BY_KEY = {(t["datatype"], t["date"]): t for t in _active["targets"]}
DOCUMENTED_TICK = _active["documented_tick"]
VENUE_LABEL = _active["venue_label"]

# 1e8 scale is lossless for Binance USDT-pair prices (max 8 decimals on any
# major USDT pair) and keeps GCD / min-diff in integer arithmetic so we avoid
# float-precision drift that would otherwise contaminate the inferred grid.
TICK_INT_SCALE = 100_000_000
TICK_SAMPLE_SIZE = 10_000

SPREAD_HIST_MAX_TICK = 20
SPREAD_HIST_OVERFLOW_LABEL = "20+"


class Tee:
    """Print-and-capture so a single pass writes stdout + report file."""

    def __init__(self) -> None:
        self._buf = io.StringIO()

    def __call__(self, *parts: object) -> None:
        line = " ".join(str(p) for p in parts) if parts else ""
        print(line)
        self._buf.write(line + "\n")

    def text(self) -> str:
        return self._buf.getvalue()


def filename_for(datatype: str, date: str) -> Path:
    # Resolve exchange + symbol from the active profile's target list so the
    # filename matches exactly what 01_tardis_download.py wrote. No hardcoded
    # venue/symbol here.
    t = _TARGETS_BY_KEY[(datatype, date)]
    return RAW_DIR / f"{t['exchange']}_{datatype}_{t['symbol']}_{date.replace('-', '')}.csv.gz"


def us_to_utc(us: int) -> datetime:
    return datetime.fromtimestamp(us / 1_000_000, tz=timezone.utc)


def require_columns(actual: list[str], required: list[str], where: str) -> None:
    missing = [c for c in required if c not in actual]
    if missing:
        raise SystemExit(
            f"FAIL: {where} missing expected columns: {missing}. "
            f"Got header: {actual}"
        )


def read_header(path: Path) -> list[str]:
    with gzip.open(path, "rt") as f:
        line = f.readline().rstrip("\n").rstrip("\r")
    return line.split(",")


# --------------------------- (a) L2 file -------------------------------------


def inspect_l2(log: Tee, date: str) -> dict:
    log()
    log(f"--- (a) L2 file inspection [{date}] ---")
    path = filename_for("incremental_book_L2", date)
    log(f"  file       : {path.name}")
    header = read_header(path)
    require_columns(header, ["local_timestamp", "is_snapshot"], "incremental_book_L2")
    log(f"  cols used  : local_timestamp, is_snapshot  (ordering = local_timestamp)")

    df = pd.read_csv(
        path,
        compression="gzip",
        usecols=["local_timestamp", "is_snapshot"],
        dtype={"local_timestamp": "int64", "is_snapshot": "string"},
    )
    total = len(df)
    is_snap = df["is_snapshot"].str.lower() == "true"
    n_snap = int(is_snap.sum())
    n_nonsnap = total - n_snap

    ts = df["local_timestamp"].to_numpy()
    ts_sorted = np.sort(ts)
    first_us, last_us = int(ts_sorted[0]), int(ts_sorted[-1])
    span_s = (last_us - first_us) / 1_000_000

    diffs_us = np.diff(ts_sorted)
    diffs_ms = diffs_us / 1000.0
    p25, p50, p75, p95, p99 = np.percentile(diffs_ms, [25, 50, 75, 95, 99])

    log(f"  total rows                       : {total:,}")
    log(f"  snapshot rows (is_snapshot=True) : {n_snap:,}")
    log(f"  non-snapshot rows                : {n_nonsnap:,}")
    log(f"  first local_timestamp (UTC)      : {us_to_utc(first_us).isoformat()}")
    log(f"  last  local_timestamp (UTC)      : {us_to_utc(last_us).isoformat()}")
    log(f"  span (s)                         : {span_s:.1f}")
    log(f"  inter-update interval (ms)       :")
    log(f"    p25 = {p25:.3f}  p50 = {p50:.3f}  p75 = {p75:.3f}")
    log(f"    p95 = {p95:.3f}  p99 = {p99:.3f}")

    return {
        "l2_total": total,
        "l2_snap": n_snap,
        "l2_nonsnap": n_nonsnap,
        "l2_span_s": span_s,
        "l2_interval_p25_ms": float(p25),
        "l2_interval_p50_ms": float(p50),
        "l2_interval_p75_ms": float(p75),
        "l2_interval_p95_ms": float(p95),
        "l2_interval_p99_ms": float(p99),
    }


# --------------------------- (b) trades --------------------------------------


def inspect_trades(log: Tee, date: str) -> dict:
    log()
    log(f"--- (b) Trades file inspection [{date}] ---")
    path = filename_for("trades", date)
    log(f"  file       : {path.name}")
    header = read_header(path)
    require_columns(header, ["local_timestamp", "amount"], "trades")

    df = pd.read_csv(
        path,
        compression="gzip",
        usecols=["local_timestamp", "amount"],
        dtype={"local_timestamp": "int64", "amount": "float64"},
    )
    total = len(df)
    total_vol = float(df["amount"].sum())
    mean_size = float(df["amount"].mean())

    ts_sorted = np.sort(df["local_timestamp"].to_numpy())
    first_us, last_us = int(ts_sorted[0]), int(ts_sorted[-1])
    span_s = (last_us - first_us) / 1_000_000
    tps_overall = total / span_s if span_s > 0 else float("nan")

    # Trades-per-second over 1-second buckets keyed on floor(local_timestamp/1e6).
    sec_bucket = ts_sorted // 1_000_000
    _, counts_per_sec = np.unique(sec_bucket, return_counts=True)
    p50_tps, p95_tps = np.percentile(counts_per_sec, [50, 95])

    gaps_s = np.diff(ts_sorted) / 1_000_000
    over_1s = gaps_s > 1.0
    n_over_1s = int(over_1s.sum())
    largest_gap_s = float(gaps_s.max()) if len(gaps_s) else 0.0

    sym = _TARGETS_BY_KEY[("trades", date)]["symbol"]
    base = sym[:-4] if sym.endswith("USDT") else sym
    log(f"  total trades        : {total:,}")
    log(f"  total volume ({base})  : {total_vol:,.4f}")
    log(f"  mean trade size     : {mean_size:.6f} {base}")
    log(f"  first ts (UTC)      : {us_to_utc(first_us).isoformat()}")
    log(f"  last  ts (UTC)      : {us_to_utc(last_us).isoformat()}")
    log(f"  span (s)            : {span_s:.1f}")
    log(f"  trades/sec overall  : {tps_overall:.2f}")
    log(f"  trades/sec p50      : {p50_tps:.2f}  (1s buckets)")
    log(f"  trades/sec p95      : {p95_tps:.2f}  (1s buckets)")
    log(f"  gaps > 1 s          : count = {n_over_1s}")
    log(f"  largest gap (s)     : {largest_gap_s:.3f}")

    return {
        "trades_total": total,
        "trades_total_vol": total_vol,
        "trades_mean_size": mean_size,
        "trades_span_s": span_s,
        "trades_tps_overall": float(tps_overall),
        "trades_tps_p50": float(p50_tps),
        "trades_tps_p95": float(p95_tps),
        "trades_gap_over_1s": n_over_1s,
        "trades_largest_gap_s": largest_gap_s,
    }


# --------------------------- (c) tick size -----------------------------------


def infer_tick_size(log: Tee, date: str) -> dict:
    log()
    log(f"--- (c) Tick size verification [{date}] ---")
    path = filename_for("book_snapshot_5", date)
    log(f"  source        : {path.name}")
    log(f"  rationale     : tick size is enforced at the quote (book) level;")
    log(f"                  trade prints can VWAP/aggregate and mask the grid.")
    header = read_header(path)
    ask_col, bid_col = "asks[0].price", "bids[0].price"
    require_columns(header, [ask_col, bid_col], "book_snapshot_5")
    log(f"  resolved cols : {ask_col}, {bid_col}")

    df = pd.read_csv(
        path,
        compression="gzip",
        usecols=[ask_col, bid_col],
        dtype={ask_col: "float64", bid_col: "float64"},
    )
    prices = pd.concat([df[ask_col], df[bid_col]], ignore_index=True).dropna()
    int_prices = np.round(prices.to_numpy() * TICK_INT_SCALE).astype(np.int64)
    int_prices = np.unique(int_prices)
    int_prices = int_prices[int_prices > 0]
    log(f"  scale         : x1e8 integer (Binance prices have <= 8 decimals,")
    log(f"                  so this is lossless and avoids float-GCD drift)")
    log(f"  distinct >0 prices: {len(int_prices):,}")

    if len(int_prices) < 2:
        raise SystemExit("FAIL: not enough distinct prices to infer a tick.")

    # GCD estimate over a sample
    if len(int_prices) > TICK_SAMPLE_SIZE:
        rng = np.random.default_rng(42)
        sample = rng.choice(int_prices, size=TICK_SAMPLE_SIZE, replace=False)
    else:
        sample = int_prices
    sample_sorted = np.sort(sample)
    sample_diffs = np.diff(sample_sorted)
    sample_diffs = sample_diffs[sample_diffs > 0]
    if len(sample_diffs) == 0:
        raise SystemExit("FAIL: no positive diffs in sampled prices.")
    gcd_int = reduce(math.gcd, sample_diffs.tolist())
    gcd_estimate = gcd_int / TICK_INT_SCALE

    # Min-diff over the full distinct grid
    full_diffs = np.diff(int_prices)
    full_diffs = full_diffs[full_diffs > 0]
    min_diff_int = int(full_diffs.min())
    min_diff_estimate = min_diff_int / TICK_INT_SCALE

    agree = gcd_int == min_diff_int
    documented_int = int(round(DOCUMENTED_TICK * TICK_INT_SCALE))
    agree_with_documented = (gcd_int == documented_int) and (min_diff_int == documented_int)
    log(f"  gcd estimate (USDT)      : {gcd_estimate}")
    log(f"  min-diff estimate (USDT) : {min_diff_estimate}")
    log(f"  estimates agree          : {agree}")
    log(f"  documented {VENUE_LABEL} tick: {DOCUMENTED_TICK} USDT")
    log(f"  inferred vs documented   : {agree_with_documented}")
    if not agree:
        log("  WARN: gcd != min-diff -- inspect distinct price grid manually.")
    if not agree_with_documented:
        log("  ============================================================")
        log("  LOUD WARN: inferred tick disagrees with documented venue tick")
        log("  ------------------------------------------------------------")
        log(f"    documented : {DOCUMENTED_TICK} USDT  ({VENUE_LABEL})")
        log(f"    gcd        : {gcd_estimate} USDT")
        log(f"    min-diff   : {min_diff_estimate} USDT")
        log("    interpretation : off-grid prices in this date's data")
        log("                     (likely Tardis reconstructor or fp64")
        log("                     artifact); not a venue tick-regime change.")
        log(f"    PROCEEDING with documented tick = {DOCUMENTED_TICK} USDT.")
        log("  ============================================================")

    return {
        "tick_gcd": gcd_estimate,
        "tick_min_diff": min_diff_estimate,
        "tick_agree": agree,
        "tick_agree_with_documented": agree_with_documented,
    }


# --------------------------- (d) spread + histogram --------------------------


def analyse_spread(log: Tee, date: str, tick_size: float) -> dict:
    log()
    log(f"--- (d) Top-of-book spread analysis [{date}] ---")
    path = filename_for("book_snapshot_5", date)
    log(f"  source         : {path.name}")
    log(f"  tick size used : {tick_size}  USDT  (documented venue tick; see (c) for diagnostic)")
    ask_col, bid_col = "asks[0].price", "bids[0].price"

    df = pd.read_csv(
        path,
        compression="gzip",
        usecols=[ask_col, bid_col],
        dtype={ask_col: "float64", bid_col: "float64"},
    )
    n_raw = len(df)
    df = df.dropna(subset=[ask_col, bid_col])
    n_after_nan = len(df)
    n_nan_dropped = n_raw - n_after_nan

    ask = df[ask_col].to_numpy()
    bid = df[bid_col].to_numpy()
    valid = (ask > bid) & (bid > 0)
    n_valid = int(valid.sum())
    n_crossed_or_zero = int((~valid).sum())

    spread_price = ask[valid] - bid[valid]
    # Rounding policy = np.round (banker's, half-to-even). Held fixed; do
    # not change without an explicit decision. Sub-tick spreads (round-to-0)
    # are impossible per venue spec and indicate off-grid data-quality
    # artifacts in the source file -- counts reported for the record.
    spread_ticks = np.round(spread_price / tick_size).astype(int)
    n_round_0   = int((spread_ticks == 0).sum())
    n_round_1   = int((spread_ticks == 1).sum())
    n_round_gt1 = int((spread_ticks > 1).sum())

    p_eq_1 = float((spread_ticks == 1).mean())
    p_le_2 = float((spread_ticks <= 2).mean())
    p25, p50, p75, p90, p95, p99 = np.percentile(spread_ticks, [25, 50, 75, 90, 95, 99])
    max_t = int(spread_ticks.max())

    log(f"  raw rows                    : {n_raw:,}")
    log(f"  dropped (NaN top-of-book)   : {n_nan_dropped:,}")
    log(f"  dropped (crossed/zero/etc)  : {n_crossed_or_zero:,}")
    log(f"  valid rows used             : {n_valid:,}")
    log(f"  rounding policy             : np.round (banker's, half-to-even) on spread / tick")
    log(f"  rounded to 0 ticks          : {n_round_0:,}  (sub-tick: impossible spread, off-grid artifact)")
    log(f"  rounded to 1 tick           : {n_round_1:,}")
    log(f"  rounded to > 1 tick         : {n_round_gt1:,}")
    log(f"  P(spread == 1 tick)         : {p_eq_1 * 100:.2f}%")
    log(f"  P(spread <= 2 ticks)        : {p_le_2 * 100:.2f}%")
    log(f"  spread distribution (ticks) :")
    log(f"    p25 = {p25:.1f}  p50 = {p50:.1f}  p75 = {p75:.1f}")
    log(f"    p90 = {p90:.1f}  p95 = {p95:.1f}  p99 = {p99:.1f}  max = {max_t}")

    # Histogram clipped at SPREAD_HIST_MAX_TICK with a single overflow bucket.
    clipped = np.minimum(spread_ticks, SPREAD_HIST_MAX_TICK + 1)
    bin_edges = np.arange(0.5, SPREAD_HIST_MAX_TICK + 2.5, 1.0)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(clipped, bins=bin_edges, edgecolor="black")
    ax.set_yscale("log")
    ax.set_xlabel("spread (ticks)")
    ax.set_ylabel("frequency (log)")
    ticks_pos = list(range(1, SPREAD_HIST_MAX_TICK + 1)) + [SPREAD_HIST_MAX_TICK + 1]
    ticks_lab = [str(i) for i in range(1, SPREAD_HIST_MAX_TICK + 1)] + [
        SPREAD_HIST_OVERFLOW_LABEL
    ]
    ax.set_xticks(ticks_pos)
    ax.set_xticklabels(ticks_lab, fontsize=8)
    ax.set_title(
        f"{VENUE_LABEL} spread distribution {date}\n"
        f"P(spread = 1 tick) = {p_eq_1 * 100:.2f}%   "
        f"P(spread <= 2 ticks) = {p_le_2 * 100:.2f}%"
    )
    fig.tight_layout()
    out_png = PROC_DIR / f"spread_hist_{date.replace('-', '')}.png"
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
    log(f"  histogram saved : {out_png.name}")

    return {
        "spread_rows_used": n_valid,
        "spread_rows_filtered_crossed": n_crossed_or_zero,
        "spread_rows_filtered_nan": n_nan_dropped,
        "spread_rounded_to_0": n_round_0,
        "spread_rounded_to_1": n_round_1,
        "spread_rounded_gt_1": n_round_gt1,
        "p_eq_1": p_eq_1,
        "p_le_2": p_le_2,
        "spread_p25_ticks": float(p25),
        "spread_p50_ticks": float(p50),
        "spread_p75_ticks": float(p75),
        "spread_p90_ticks": float(p90),
        "spread_p95_ticks": float(p95),
        "spread_p99_ticks": float(p99),
        "spread_max_ticks": max_t,
    }


# --------------------------- main --------------------------------------------


def main() -> int:
    log = Tee()
    log(f"Step 5 sample inspection report")
    log(f"Generated  : {datetime.now(timezone.utc).isoformat()}")
    log(f"Manifest   : {MANIFEST_PATH}")
    log(f"Dates      : {', '.join(DATES)}")
    log(f"Raw dir    : {RAW_DIR}")
    log(f"Proc dir   : {PROC_DIR}")
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    if not MANIFEST_PATH.exists():
        raise SystemExit(f"FAIL: manifest missing at {MANIFEST_PATH}")
    # Light sanity: ensure all 9 files referenced by today's analysis are
    # present in the manifest (we don't sha-recheck here; Step 4/4.5 already
    # validated post-download).
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_files = {e["filename"] for e in manifest["files"]}
    for d in DATES:
        for dt in ("incremental_book_L2", "trades", "book_snapshot_5"):
            f = filename_for(dt, d).name
            if f not in manifest_files:
                raise SystemExit(f"FAIL: {f} not in manifest; cannot proceed.")

    per_date: dict[str, dict] = {}
    for date in DATES:
        log()
        log("=" * 70)
        log(f"DATE: {date}")
        log("=" * 70)
        r_l2 = inspect_l2(log, date)
        r_tr = inspect_trades(log, date)
        r_tk = infer_tick_size(log, date)
        # Canonical tick = venue's documented tick (DOCUMENTED_TICK).
        # infer_tick_size() runs as a diagnostic only; if it disagrees with
        # the documented tick a LOUD WARN block fires inside that function,
        # but spread analysis proceeds with the documented value. The venue
        # spec is the source of truth; per-date inference can be contaminated
        # by off-grid data-quality artifacts (see 2024-03-01 BTCUSDT-perp).
        tick = DOCUMENTED_TICK
        r_sp = analyse_spread(log, date, tick)
        per_date[date] = {**r_l2, **r_tr, **r_tk, **r_sp, "tick_size_used": tick}

    # Cross-date tick-regime check
    log()
    log("=" * 70)
    log("CROSS-DATE TICK REGIME CHECK")
    log("=" * 70)
    # Invariant guard: with canonical_tick sourced from a profile-level
    # constant, this triggers only if PROFILES is manually edited to
    # introduce per-date tick inconsistency within one profile.
    ticks = {d: per_date[d]["tick_size_used"] for d in DATES}
    for d, t in ticks.items():
        log(f"  {d}: tick = {t}")
    if len(set(ticks.values())) > 1:
        log("  WARN: tick regime change detected between dates.")
    else:
        log("  OK: identical tick size across all 3 dates.")

    # Final summary table
    log()
    log("=" * 70)
    log("FINAL SUMMARY")
    log("=" * 70)
    log()
    log("Spread is computed using the venue's documented tick (0.10 USDT for")
    log("binance-futures BTCUSDT, 0.01 USDT for binance ETHUSDT).")
    log()
    header_cols = [
        "Date",
        "Rows used",
        "P(spread=1 tick)",
        "P(spread<=2 ticks)",
        "Median ticks",
        "P95 ticks",
        "Trades/sec p50",
        "L2 interval p50 (ms)",
    ]
    log("| " + " | ".join(header_cols) + " |")
    log("|" + "|".join(["-" * (len(c) + 2) for c in header_cols]) + "|")
    for d in DATES:
        r = per_date[d]
        row = [
            d,
            f"{r['spread_rows_used']:,}",
            f"{r['p_eq_1'] * 100:.2f}%",
            f"{r['p_le_2'] * 100:.2f}%",
            f"{r['spread_p50_ticks']:.1f}",
            f"{r['spread_p95_ticks']:.1f}",
            f"{r['trades_tps_p50']:.2f}",
            f"{r['l2_interval_p50_ms']:.3f}",
        ]
        log("| " + " | ".join(row) + " |")

    # Cross-date consistency check on P(spread=1)
    log()
    p_eq_1_vals = [per_date[d]["p_eq_1"] * 100 for d in DATES]
    p_eq_1_span = max(p_eq_1_vals) - min(p_eq_1_vals)
    log(
        f"P(spread=1 tick) range across dates: "
        f"{min(p_eq_1_vals):.2f}% - {max(p_eq_1_vals):.2f}%  (span {p_eq_1_span:.2f} pp)"
    )
    if p_eq_1_span > 15.0:
        log(f"  WARN: span > 15 pp -- {VENUE_LABEL} spread regime is non-stationary across the year.")
    else:
        log("  OK: span <= 15 pp -- spread regime is reasonably consistent across dates.")

    # Interpretation guidance (script does NOT make a pair-switch decision)
    log()
    log("Interpretation guidance (decision belongs to the human reader):")
    log()
    log(f"  P(spread == 1 tick) interpretation for {VENUE_LABEL}:")
    log("    > 95%   -> severe degeneracy; pair-switch strongly recommended")
    log("    80-95%  -> marginal; possibly usable with documented caveats")
    log("    60-80%  -> acceptable; quote-placement is a meaningful decision")
    log("    < 60%   -> good; healthy decision space")
    log()
    log("  Cross-date consistency check:")
    log("    If P(spread == 1 tick) varies by more than 15 pp across the 3 dates,")
    log(f"    the {VENUE_LABEL} spread regime itself is non-stationary across the year")
    log("    -- flag this as a finding for the thesis writeup.")

    log()
    log(f"Report length: {len(per_date)} dates  /  outputs in {PROC_DIR.name}/")
    REPORT_PATH.write_text(log.text(), encoding="utf-8")
    # Final notice goes to stdout only (already-written report doesn't need a
    # 'I just wrote myself' self-reference).
    print()
    print(f"Saved: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
