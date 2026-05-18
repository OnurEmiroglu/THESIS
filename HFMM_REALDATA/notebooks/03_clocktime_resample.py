"""Phase 1A Step 5.5: clock-time resampled spread sanity check.

Step 5 measured P(spread=1 tick) at raw book-update granularity (every change
to top-of-book). An RL market-making agent does not decide at infinite
frequency; it operates on a discrete clock-time grid with finite latency.
This script answers: if we resample top-of-book to a realistic agent decision
cadence, does the spread degeneracy persist, or does it dilute because rapid
sub-step microbursts average out?

For each of the 3 ETHUSDT spot dates and each cadence in {raw, 100ms, 500ms,
1000ms}, we report P(spread=1 tick), P(spread<=2 ticks), median ticks, p95
ticks, sample size. The "raw" row is recomputed in this script from the same
book_snapshot_5 source so the comparison is internally consistent (and should
match Step 5's report to within rounding).

Last-tick semantics: at each grid timestamp t, the agent sees the last book
observation with local_timestamp <= t. Implemented via pd.merge_asof with
direction='backward'. No interpolation. Grid points before the first valid
observation are dropped.

Tick size: 0.01 USDT, hardcoded. Step 5 verified this on all 3 dates via two
independent estimators (GCD over a 10k-price sample and min-diff over the
full distinct grid), both yielding 0.01 with estimates agreeing -- so this
is a verified constant for these files, not a hidden assumption.

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
RAW_DIR = (SCRIPT_DIR / ".." / "data" / "raw").resolve()
PROC_DIR = (SCRIPT_DIR / ".." / "data" / "processed").resolve()
REPORT_PATH = PROC_DIR / "step5_5_clocktime_sanity_report.txt"

DATES = ["2024-03-01", "2024-06-01", "2024-09-01"]
CADENCES_MS = [100, 500, 1000]
TICK_SIZE = 0.01  # USDT. Verified in Step 5 (gcd & min-diff agree on all 3 dates).
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
    return RAW_DIR / f"binance_{datatype}_ETHUSDT_{date.replace('-', '')}.csv.gz"


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
        return {"n_used": 0, "p_eq_1": float("nan"), "p_le_2": float("nan"),
                "p50_ticks": float("nan"), "p95_ticks": float("nan")}
    p50, p95 = np.percentile(spread_ticks, [50, 95])
    return {
        "n_used": n,
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
    spread_ticks = np.round(spread_price / TICK_SIZE).astype(int)
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
    spread_ticks = np.round(spread_price / TICK_SIZE).astype(int)
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
    cols = ["Cadence", "Grid points", "Used", "P(spread=1 tick)",
            "P(spread<=2 ticks)", "Median ticks", "P95 ticks"]
    log("| " + " | ".join(cols) + " |")
    log("|" + "|".join("-" * (len(c) + 2) for c in cols) + "|")

    raw_row = [
        "raw (Step 5)",
        "-",  # raw has no grid; ASCII to avoid Windows cp1252 console issues
        f"{raw['n_used']:,}",
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
    log(f"Tick size  : {TICK_SIZE} USDT  (verified in Step 5 via GCD+min-diff)")
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
    log("  If P(spread=1 tick) remains > 95% across ALL cadences (raw, 100ms,")
    log("    500ms, 1000ms) for ALL 3 dates:")
    log("    -> ETHUSDT spot is unsuitable for spread-based MM RL regardless")
    log("       of discretization. Venue pivot is fully justified.")
    log()
    log("  If P(spread=1 tick) drops below 80% at any cadence:")
    log("    -> ETHUSDT spot may still be viable with appropriate discretization.")
    log("       Reconsider pivot decision; document the discretization-degeneracy")
    log("       tradeoff.")
    log()
    log("  If degeneracy stays in the 80-95% band:")
    log("    -> Marginal; document this in methodology and let downstream")
    log("       decisions drive the choice.")

    REPORT_PATH.write_text(log.text(), encoding="utf-8")
    print()
    print(f"Saved: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
