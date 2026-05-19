"""Streamed-GET verification of Tardis free-sample URLs (status + headers only).

Phase 1A Step 3 (revision 2): verify the URL pattern works without downloading
the payload. Two changes vs. the first attempt:

1. METHOD: switched from HEAD to GET-with-streaming.
   The Tardis CDN appears to not serve HEAD on the datasets endpoint — every
   HEAD probe returned 404 with `Content-Type: application/json`, while public
   tutorials show plain GET (e.g. wget) returning 200 OK for the same URLs as
   recently as 2024-08-09. This is a known Cloudflare-style pattern where HEAD
   takes a different route from GET and lands on an error backend. We now use
   `requests.get(url, stream=True, ...)`, read status + headers, then close
   the response without consuming the body. This is equivalent in bandwidth
   cost to HEAD (TCP handshake + response head, no payload bytes pulled) but
   goes through the GET endpoint that the CDN actually serves.

2. SCOPE: 10 targets in 3 groups, closing two open questions in one run.

   Group A — Binance Spot (BTCUSDT 2019-12-01), 2 targets:
     Documented free sample, our study's intended venue. Acts as the canonical
     reference: if Group A is 200 the method/URL pattern is right.

   Group B — Binance Futures (BTCUSDT 2020-02-01), 2 targets:
     Externally confirmed working via HftBacktest tutorial (GET, 2024-08-09,
     200 OK). Acts as the cross-venue control: if A and B both 200, the
     URL/host pattern is venue-agnostic.

   Group C — Binance Spot ETHUSDT, 2024-{03,06,09}-01, 6 targets:
     The *original* Step 3 target. The first attempt got 404 across these via
     HEAD; we never confirmed whether GET works for them. This group answers
     the actual study-readiness question:
       - If C returns 200: "first of each month, any actively traded pair" is
         a real free-tier guarantee. ETHUSDT spot is reachable; we proceed
         with the original plan.
       - If C returns 404 while A returns 200: free access is narrower than
         documented and is tied to specific documented combinations. We fall
         back to BTCUSDT spot (or another documented pair) for the study.

   Group D — book_snapshot_5 for ETHUSDT spot, 2024-{03,06,09}-01, 3 targets:
     Reconstructed top-5 level snapshots. Needed for the Step 5 spread-
     degeneracy decision gate (top-of-book bid/ask per update). If free-tier
     access exists for this datatype on our target pair, we use it directly;
     if not, we fall back to a simpler proxy (e.g. on-the-fly L2 book replay)
     and document the limitation in the methodology.

   Group E - Binance Futures BTCUSDT perpetual, 2024-{03,06,09}-01, 9 targets:
     Pivot venue after Phase 1A on ETHUSDT spot showed P(spread=1 tick)
     >= 99.40% at raw and >= 99.52% at 100ms / 500ms / 1s cadences across
     all 3 dates (per step5_5_clocktime_sanity_report.txt, min cell at
     2024-03-01 / 500ms). Group E replays the same probe pattern on Binance
     Futures BTCUSDT perp: 3 dates x 3 datatypes (incremental_book_L2,
     trades, book_snapshot_5). Snapshot depth: top-5 only.

Pair/date selection for the actual study (ETHUSDT vs BTCUSDT vs mid-cap, what
time window) is a separate downstream decision driven by the Step 5 spread-
degeneracy metric, not by this script.

Behaviour:
  - issues `requests.get(url, stream=True, allow_redirects=True, timeout=30)`
    per target;
  - reports URL, HTTP status, Content-Length, Last-Modified, Content-Type;
  - immediately closes the response without iterating content — no payload
    bytes are downloaded;
  - if ANY target returns non-200, stops and reports — does NOT try alternative
    symbol cases, exchange codes, or dates as recovery.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import requests


# Validation targets — see module docstring for group rationale.
VALIDATION_TARGETS = [
    # === Group A: Documented Binance Spot sample (canonical reference, expected 200) ===
    {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2019-12-01", "symbol": "BTCUSDT"},
    {"exchange": "binance", "datatype": "trades",              "date": "2019-12-01", "symbol": "BTCUSDT"},

    # === Group B: Binance Futures sample (externally confirmed working, expected 200) ===
    {"exchange": "binance-futures", "datatype": "incremental_book_L2", "date": "2020-02-01", "symbol": "BTCUSDT"},
    {"exchange": "binance-futures", "datatype": "trades",              "date": "2020-02-01", "symbol": "BTCUSDT"},

    # === Group C: Original target re-tested via GET (ETHUSDT spot, first-of-month, varied dates) ===
    # If these return 200, the original 404s were HEAD-only and our actual study target is reachable for free.
    # If they return 404, "first of each month" free access is narrower than documentation suggests
    # (probably tied to specific documented combinations) and we fall back to BTCUSDT.
    {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2024-03-01", "symbol": "ETHUSDT"},
    {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2024-06-01", "symbol": "ETHUSDT"},
    {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2024-09-01", "symbol": "ETHUSDT"},
    {"exchange": "binance", "datatype": "trades",              "date": "2024-03-01", "symbol": "ETHUSDT"},
    {"exchange": "binance", "datatype": "trades",              "date": "2024-06-01", "symbol": "ETHUSDT"},
    {"exchange": "binance", "datatype": "trades",              "date": "2024-09-01", "symbol": "ETHUSDT"},

    # === Group D: book_snapshot_5 for ETHUSDT spot (needed for Step 5 spread metric) ===
    # If free-tier, we use this for top-of-book reconstruction; if not, we fall back
    # to a simpler proxy and document the limitation in the methodology.
    {"exchange": "binance", "datatype": "book_snapshot_5", "date": "2024-03-01", "symbol": "ETHUSDT"},
    {"exchange": "binance", "datatype": "book_snapshot_5", "date": "2024-06-01", "symbol": "ETHUSDT"},
    {"exchange": "binance", "datatype": "book_snapshot_5", "date": "2024-09-01", "symbol": "ETHUSDT"},

    # === Group E: Binance Futures BTCUSDT perpetual (pivot venue, 2024-{03,06,09}-01) ===
    # Same 3 dates x 3 datatypes pattern as Group C+D, on the perp venue.
    {"exchange": "binance-futures", "datatype": "incremental_book_L2", "date": "2024-03-01", "symbol": "BTCUSDT"},
    {"exchange": "binance-futures", "datatype": "incremental_book_L2", "date": "2024-06-01", "symbol": "BTCUSDT"},
    {"exchange": "binance-futures", "datatype": "incremental_book_L2", "date": "2024-09-01", "symbol": "BTCUSDT"},
    {"exchange": "binance-futures", "datatype": "trades",              "date": "2024-03-01", "symbol": "BTCUSDT"},
    {"exchange": "binance-futures", "datatype": "trades",              "date": "2024-06-01", "symbol": "BTCUSDT"},
    {"exchange": "binance-futures", "datatype": "trades",              "date": "2024-09-01", "symbol": "BTCUSDT"},
    {"exchange": "binance-futures", "datatype": "book_snapshot_5",     "date": "2024-03-01", "symbol": "BTCUSDT"},
    {"exchange": "binance-futures", "datatype": "book_snapshot_5",     "date": "2024-06-01", "symbol": "BTCUSDT"},
    {"exchange": "binance-futures", "datatype": "book_snapshot_5",     "date": "2024-09-01", "symbol": "BTCUSDT"},
]

BASE_URL = "https://datasets.tardis.dev/v1"
TIMEOUT_S = 30


def build_url(target: dict) -> str:
    yyyy, mm, dd = target["date"].split("-")
    return (
        f"{BASE_URL}/{target['exchange']}/{target['datatype']}/"
        f"{yyyy}/{mm}/{dd}/{target['symbol']}.csv.gz"
    )


def probe(url: str) -> dict:
    """GET with stream=True, read status+headers, close without consuming body."""
    started = datetime.now(timezone.utc)
    try:
        with requests.get(url, stream=True, allow_redirects=True, timeout=TIMEOUT_S) as r:
            return {
                "url": url,
                "status": r.status_code,
                "content_length": r.headers.get("Content-Length"),
                "last_modified": r.headers.get("Last-Modified"),
                "content_type": r.headers.get("Content-Type"),
                "final_url": r.url,
                "checked_utc": started.isoformat(),
                "error": None,
            }
    except requests.RequestException as exc:
        return {
            "url": url,
            "status": None,
            "content_length": None,
            "last_modified": None,
            "content_type": None,
            "final_url": None,
            "checked_utc": started.isoformat(),
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    print(f"Tardis URL probe (GET stream, no body) started at {datetime.now(timezone.utc).isoformat()}")
    print(f"Checking {len(VALIDATION_TARGETS)} URL(s) (timeout={TIMEOUT_S}s each, no payload downloaded).\n")

    results = [probe(build_url(t)) for t in VALIDATION_TARGETS]

    for r in results:
        print(f"URL            : {r['url']}")
        print(f"  HTTP status  : {r['status']}")
        print(f"  Content-Length : {r['content_length']}")
        print(f"  Last-Modified  : {r['last_modified']}")
        print(f"  Content-Type   : {r['content_type']}")
        if r["final_url"] and r["final_url"] != r["url"]:
            print(f"  Redirected to: {r['final_url']}")
        if r["error"]:
            print(f"  ERROR        : {r['error']}")
        print()

    # Compact summary table
    print("Summary:")
    print(f"  {'exchange':<17} {'datatype':<22} {'date':<12} {'symbol':<8} {'status':<7} {'bytes':>14}")
    for t, r in zip(VALIDATION_TARGETS, results):
        cl = r["content_length"] if r["content_length"] else "-"
        print(f"  {t['exchange']:<17} {t['datatype']:<22} {t['date']:<12} {t['symbol']:<8} {str(r['status']):<7} {cl:>14}")
    print()

    non_200 = [r for r in results if r["status"] != 200]
    print("=" * 70)
    if non_200:
        print(f"FAIL: {len(non_200)}/{len(results)} URL(s) did not return 200 OK.")
        print("Per task brief: stop here, do NOT try alternative cases/codes/dates.")
        return 1
    print(f"OK: all {len(results)} URL(s) returned 200 OK.")
    total_bytes = sum(int(r["content_length"]) for r in results if r["content_length"])
    print(f"Total advertised payload size (sum of Content-Length): {total_bytes:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
