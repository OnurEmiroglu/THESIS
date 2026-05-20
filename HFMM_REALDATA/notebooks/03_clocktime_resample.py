"""Phase 1A Step 5.5: clock-time resampled spread sanity check.

Step 5 measured P(spread=1 tick) at raw book-update granularity (every change
to top-of-book). An RL market-making agent does not decide at infinite
frequency; it operates on a discrete clock-time grid with finite latency.
This script answers: if we resample top-of-book to a realistic agent decision
cadence, does the spread degeneracy persist, or does it dilute because rapid
sub-step microbursts average out?

For each of the 3 dates configured under ACTIVE_PROFILE and each cadence in
{raw, 100ms, 500ms, 1000ms}, we report P(spread=1 tick), P(spread<=2 ticks),
median ticks, p95 ticks, sample size, and the count of rows that rounded to
0 ticks (sub-tick spreads -- impossible per venue spec; off-grid artifact).
The "raw" row is recomputed in this script from the same book_snapshot_5
source so the comparison is internally consistent (and should match Step 5's
report to within rounding).

Last-tick semantics: at each grid timestamp t, the agent sees the last book
observation with local_timestamp <= t. Implemented via pd.merge_asof with
direction='backward'. No interpolation. Grid points before the first valid
observation are dropped.

Tick size: sourced from PROFILES[ACTIVE_PROFILE]['documented_tick'] -- the
venue spec is the source of truth (0.10 USDT for binance-futures BTCUSDT,
0.01 USDT for binance ETHUSDT). 02_sample_inspect.py runs the per-date
GCD/min-diff diagnostic and emits a LOUD WARN block when inferred disagrees
with documented (as happens on 2024-03-01 BTCUSDT-perp due to off-grid
prices); this script trusts the documented value and reports rounded-to-0
counts so any clock-time impact of off-grid contamination is visible per
cadence.

This script does NOT make a pivot decision; it prints metrics and the
interpretation rubric.
"""

from __future__ import annotations

import gzip
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


SCRIPT_DIR = Path(__file__).resolve().parent
HFMM_ROOT = SCRIPT_DIR.parent

# === Dataset profiles (shape matches 02_sample_inspect.py) ===
# NUMERIC-LEVEL byte-for-byte preservation under the "ethusdt_spot" profile:
# flipping ACTIVE_PROFILE back yields the same documented tick (0.01), the
# same rounding policy (np.round / banker's, half-to-even), and the same
# percentile values at the previously-emitted breakpoints (p50/p95) for the
# raw + 100ms + 500ms + 1000ms cadences. The REPORT TEXT now also emits a
# Round->0 column in the per-date table; for ethusdt_spot these counts are
# all 0 (matching 02's ETHUSDT report) so the new column does not alter the
# pre-existing numeric fields.
# Profile structure mirrors 02 verbatim so 02 and 03 share a single bundle
# definition mentally. report_basename + manifest_path are kept for cross-
# script symmetry even though 03 only uses raw_dir / proc_dir / documented_
# tick / venue_label / targets. documented_tick is the venue spec and is
# the source of truth here; 02 runs the per-date tick-inference diagnostic.
PROFILES = {
    "ethusdt_spot": {
        "raw_dir":         HFMM_ROOT / "data" / "raw",
        "manifest_path":   HFMM_ROOT / "data" / "raw" / "_manifest.json",
        "proc_dir":        HFMM_ROOT / "data" / "processed",
        "report_basename": "step5_5_clocktime_sanity_report.txt",
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
        "report_basename": "step5_5_clocktime_sanity_report.txt",
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
REPORT_PATH = PROC_DIR / _active["report_basename"]
DATES = sorted({t["date"] for t in _active["targets"]})
_TARGETS_BY_KEY = {(t["datatype"], t["date"]): t for t in _active["targets"]}
DOCUMENTED_TICK = _active["documented_tick"]
VENUE_LABEL = _active["venue_label"]

CADENCES_MS = [100, 500, 1000]
ASK_COL = "asks[0].price"
BID_COL = "bids[0].price"
TS_COL = "local_timestamp"


class Tee:
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
    # venue/symbol here. (Same pattern as 02_sample_inspect.py.)
    t = _TARGETS_BY_KEY[(datatype, date)]
    return RAW_DIR / f"{t['exchange']}_{datatype}_{t['symbol']}_{date.replace('-', '')}.csv.gz"


def read_header(path: Path) -> list[str]:
    with gzip.open(path, "rt") as f:
        return f.readline().rstrip("\r\n").split(",")


def require_columns(actual: list[str], required: list[str], where: str) -> None:
    missing = [c for c in required if c not in actual]
    if missing:
        raise SystemExit(
            f"FAIL: {where} missing expected columns: {missing}. Got: {actual}"
        )


def spread_stats(spread_ticks: np.ndarray) -> dict:
    n = int(spread_ticks.size)
    if n == 0:
        return {"n_used": 0, "n_round_0": 0, "n_round_1": 0, "n_round_gt1": 0,
                "p_eq_1": float("nan"), "p_le_2": float("nan"),
                "p50_ticks": float("nan"), "p95_ticks": float("nan")}
    p50, p95 = np.percentile(spread_ticks, [50, 95])
    return {
        "n_used": n,
        # Sub-tick spreads (round-to-0) are impossible per venue spec and
        # surface off-grid contamination (relevant for 2024-03-01 BTCUSDT-perp).
        "n_round_0":   int((spread_ticks == 0).sum()),
        "n_round_1":   int((spread_ticks == 1).sum()),
        "n_round_gt1": int((spread_ticks > 1).sum()),
        "p_eq_1": float((spread_ticks == 1).mean()),
        "p_le_2": float((spread_ticks <= 2).mean()),
        "p50_ticks": float(p50),
        "p95_ticks": float(p95),
    }


def load_valid_book(log: Tee, date: str) -> pd.DataFrame:
    path = filename_for("book_snapshot_5", date)
    log(f"  source                : {path.name}")
    header = read_header(path)
    require_columns(header, [TS_COL, ASK_COL, BID_COL], "book_snapshot_5")
    df = pd.read_csv(
        path,
        compression="gzip",
        usecols=[TS_COL, ASK_COL, BID_COL],
        dtype={TS_COL: "int64", ASK_COL: "float64", BID_COL: "float64"},
    )
    n_raw = len(df)
    # Stable sort to preserve collector order on equal-timestamp ties.
    df = df.sort_values(TS_COL, kind="stable").reset_index(drop=True)
    df = df.dropna(subset=[ASK_COL, BID_COL])
    n_after_nan = len(df)
    valid = (df[ASK_COL] > df[BID_COL]) & (df[BID_COL] > 0)
    df = df.loc[valid].reset_index(drop=True)
    n_valid = len(df)
    log(f"  raw rows              : {n_raw:,}")
    log(f"  after NaN drop        : {n_after_nan:,}")
    log(f"  after crossed/zero    : {n_valid:,}")
    return df


def analyse_raw(df_valid: pd.DataFrame) -> dict:
    spread_price = df_valid[ASK_COL].to_numpy() - df_valid[BID_COL].to_numpy()
    spread_ticks = np.round(spread_price / DOCUMENTED_TICK).astype(int)
    return spread_stats(spread_ticks)


def analyse_at_cadence(df_valid: pd.DataFrame, cadence_ms: int) -> dict:
    cadence_us = cadence_ms * 1000
    first_us = int(df_valid[TS_COL].iloc[0])
    last_us = int(df_valid[TS_COL].iloc[-1])
    grid_ts = np.arange(first_us, last_us + 1, cadence_us, dtype=np.int64)
    n_grid = int(grid_ts.size)
    grid = pd.DataFrame({TS_COL: grid_ts})
    # pd.merge_asof requires both sides sorted on the key (df_valid already is).
    # direction='backward' -> for each grid t, take the last book row with ts <= t.
    merged = pd.merge_asof(grid, df_valid, on=TS_COL, direction="backward")
    # Grid points before first observation become NaN; drop them. By construction
    # the rest carry a previously-validated (valid) book row, so we don't need
    # to re-filter crossed/zero here.
    merged = merged.dropna(subset=[ASK_COL, BID_COL])
    spread_price = merged[ASK_COL].to_numpy() - merged[BID_COL].to_numpy()
    spread_ticks = np.round(spread_price / DOCUMENTED_TICK).astype(int)
    stats = spread_stats(spread_ticks)
    stats["n_grid"] = n_grid
    return stats


def fmt_pct(x: float) -> str:
    if x != x:  # NaN
        return "  n/a "
    return f"{x * 100:6.2f}%"


def emit_date_table(log: Tee, date: str, raw: dict, cad: dict[int, dict]) -> None:
    log()
    log(f"=== {date} ===")
    log()
    cols = ["Cadence", "Grid points", "Used", "Round->0", "P(spread=1 tick)",
            "P(spread<=2 ticks)", "Median ticks", "P95 ticks"]
    log("| " + " | ".join(cols) + " |")
    log("|" + "|".join("-" * (len(c) + 2) for c in cols) + "|")

    raw_row = [
        "raw (Step 5)",
        "-",  # raw has no grid; ASCII to avoid Windows cp1252 console issues
        f"{raw['n_used']:,}",
        f"{raw['n_round_0']:,}",
        fmt_pct(raw["p_eq_1"]),
        fmt_pct(raw["p_le_2"]),
        f"{raw['p50_ticks']:.1f}",
        f"{raw['p95_ticks']:.1f}",
    ]
    log("| " + " | ".join(raw_row) + " |")

    for ms in CADENCES_MS:
        s = cad[ms]
        row = [
            f"{ms}ms",
            f"{s['n_grid']:,}",
            f"{s['n_used']:,}",
            f"{s['n_round_0']:,}",
            fmt_pct(s["p_eq_1"]),
            fmt_pct(s["p_le_2"]),
            f"{s['p50_ticks']:.1f}",
            f"{s['p95_ticks']:.1f}",
        ]
        log("| " + " | ".join(row) + " |")


def main() -> int:
    log = Tee()
    log("Step 5.5 clock-time resampled spread sanity report")
    log(f"Generated  : {datetime.now(timezone.utc).isoformat()}")
    log(f"Dates      : {', '.join(DATES)}")
    log(f"Cadences   : raw + {', '.join(str(c) + 'ms' for c in CADENCES_MS)}")
    log(f"Profile    : {ACTIVE_PROFILE}  ({VENUE_LABEL})")
    log(f"Tick size  : {DOCUMENTED_TICK} USDT  (documented venue tick; see 02_sample_inspect.py for per-date diagnostic)")
    log(f"   (documented tick must match the tick verified in 02; "
        f"see processed/step5_inspection_report.txt for the per-date "
        f"diagnostic.)")
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    per_date: dict[str, dict] = {}
    for date in DATES:
        log()
        log("=" * 70)
        log(f"DATE: {date}")
        log("=" * 70)
        df_valid = load_valid_book(log, date)
        raw = analyse_raw(df_valid)
        cad = {ms: analyse_at_cadence(df_valid, ms) for ms in CADENCES_MS}
        per_date[date] = {"raw": raw, "cadence": cad}
        emit_date_table(log, date, raw, cad)

    # Cross-date summary -- how P(spread=1) behaves as cadence coarsens.
    log()
    log("=" * 70)
    log("CROSS-DATE SUMMARY: P(spread = 1 tick) by cadence")
    log("=" * 70)
    log()
    head = ["Cadence"] + DATES
    log("| " + " | ".join(head) + " |")
    log("|" + "|".join("-" * (len(c) + 2) for c in head) + "|")
    raw_row = ["raw"] + [fmt_pct(per_date[d]["raw"]["p_eq_1"]) for d in DATES]
    log("| " + " | ".join(raw_row) + " |")
    for ms in CADENCES_MS:
        row = [f"{ms}ms"] + [
            fmt_pct(per_date[d]["cadence"][ms]["p_eq_1"]) for d in DATES
        ]
        log("| " + " | ".join(row) + " |")

    # Interpretation guidance (the script does NOT decide).
    log()
    log("Interpretation guidance (decision belongs to the human reader):")
    log()
    log(f"  If P(spread=1 tick) remains > 95% across ALL cadences (raw, 100ms,")
    log(f"    500ms, 1000ms) for ALL 3 dates:")
    log(f"    -> {VENUE_LABEL} is unsuitable for spread-based MM RL regardless")
    log(f"       of discretization. Venue pivot is fully justified.")
    log()
    log(f"  If P(spread=1 tick) drops below 80% at any cadence:")
    log(f"    -> {VENUE_LABEL} may still be viable with appropriate discretization.")
    log(f"       Reconsider pivot decision; document the discretization-degeneracy")
    log(f"       tradeoff.")
    log()
    log(f"  If degeneracy stays in the 80-95% band:")
    log(f"    -> Marginal; document this in methodology and let downstream")
    log(f"       decisions drive the choice.")

    REPORT_PATH.write_text(log.text(), encoding="utf-8")
    print()
    print(f"Saved: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
