"""Download Tardis free-tier samples via a profile selector.

Phase 1A covers two venue-scoped datasets, each with 9 files (3 dates x 3
datatypes for first-of-month 2024-{03,06,09}-01):

  - "ethusdt_spot"  : Binance Spot ETHUSDT (Step 4 + 4.5 original target).
  - "btcusdt_perp"  : Binance Futures BTCUSDT perpetual (post-pivot target,
                      Step 6 onward, after ETHUSDT showed structural spread
                      degeneracy >= 99.40% at all tested cadences).

PROFILES (below) is the source of truth for what each dataset comprises:
its raw_dir, manifest_path, proc_dir, fname_prefix, and the 9-entry target
list. ACTIVE_PROFILE selects which profile this run operates on; the rest
of the script is profile-agnostic. Flipping ACTIVE_PROFILE back to
"ethusdt_spot" reproduces the original Step 4 + 4.5 behavior byte-for-byte
because that profile's paths are exactly the ones the pre-profile code
hardcoded.

Manifest-merge semantics: the active profile's targets are the source of
truth for its manifest. On rerun, files already downloaded with matching
sha256 are skipped and their existing manifest entries are reused verbatim
(preserves download_utc, content_length headers, etc. from the original
download). New targets are downloaded fresh. The final manifest contains
exactly the entries listed in the active profile's targets, in that order;
old entries for files NOT in the target list are dropped, but the orphan-
file preflight check guards against losing data silently.

The two profiles use *different* raw_dir and manifest_path values, so a
run with ACTIVE_PROFILE="btcusdt_perp" cannot read or write the
ethusdt_spot manifest, and vice versa. This venue isolation is the
mechanism that protects each manifest from cross-contamination.

Validation per file (in order, failing fast on any mismatch):
  - HTTP status 200
  - Bytes written == Content-Length header
  - First 2 bytes are the gzip magic signature (0x1f 0x8b)
  - gzip.open() succeeds and yields a readable first line
  - sha256 recorded post-rename

Resume-safe behaviour at startup:
  - file exists + matching sha256 in _manifest.json  -> skip
  - file exists + mismatching sha256 in manifest     -> FAIL LOUD
  - file exists but no manifest entry (orphan)       -> FAIL LOUD
  - stale *.partial files present                    -> FAIL LOUD
  - clean dir / no manifest                          -> proceed (fresh start)

Hard-stop on any failure: do not continue with remaining files. The batch
should succeed atomically; better to debug one failure than to ship a
half-complete batch.

Download mechanics:
  - requests.get(url, stream=True, timeout=30, allow_redirects=True)
  - iter_content(chunk_size=1 MiB), written to <final>.partial, then
    atomic os.replace() to final filename on success
  - progress: prints a one-line milestone roughly every 10% of expected bytes

Filename convention: {exchange}_{datatype}_{symbol}_{YYYYMMDD}.csv.gz
Manifest path: <profile.raw_dir>/_manifest.json  (this file IS tracked).
  - ethusdt_spot : HFMM_REALDATA/data/raw/_manifest.json
  - btcusdt_perp : HFMM_REALDATA/data/phase1a_btcusdt_perp/raw/_manifest.json
All timestamps timezone-aware UTC.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


BASE_URL = "https://datasets.tardis.dev/v1"
CHUNK_SIZE = 1_048_576  # 1 MiB
TIMEOUT_S = 30
GZIP_MAGIC = b"\x1f\x8b"

# Resolve paths relative to this script (HFMM_REALDATA/notebooks/01_tardis_download.py).
SCRIPT_DIR = Path(__file__).resolve().parent
HFMM_ROOT = SCRIPT_DIR.parent

# === Dataset profiles ====================================================
# Each profile bundles everything venue-specific so the rest of the script
# is data/path-agnostic. The "ethusdt_spot" entry's raw_dir/manifest_path
# match the pre-profile-refactor hardcoded paths exactly -- flipping
# ACTIVE_PROFILE back reproduces Step 4 + 4.5 behavior byte-for-byte.
# proc_dir + report_basename are carried here for cross-script consistency
# with notebooks 02/03 (script 01 itself does not use them).
PROFILES = {
    "ethusdt_spot": {
        "raw_dir":        HFMM_ROOT / "data" / "raw",
        "manifest_path":  HFMM_ROOT / "data" / "raw" / "_manifest.json",
        "proc_dir":       HFMM_ROOT / "data" / "processed",
        "report_basename": "step5_inspection_report.txt",
        "fname_prefix":   "binance",
        "targets": [
            # === Group C: incremental_book_L2 + trades (Step 4) ===
            {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2024-03-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2024-06-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "incremental_book_L2", "date": "2024-09-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "trades",              "date": "2024-03-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "trades",              "date": "2024-06-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "trades",              "date": "2024-09-01", "symbol": "ETHUSDT"},
            # === Group D: book_snapshot_5 (Step 4.5, appended) ===
            {"exchange": "binance", "datatype": "book_snapshot_5",     "date": "2024-03-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "book_snapshot_5",     "date": "2024-06-01", "symbol": "ETHUSDT"},
            {"exchange": "binance", "datatype": "book_snapshot_5",     "date": "2024-09-01", "symbol": "ETHUSDT"},
        ],
    },
    "btcusdt_perp": {
        "raw_dir":        HFMM_ROOT / "data" / "phase1a_btcusdt_perp" / "raw",
        "manifest_path":  HFMM_ROOT / "data" / "phase1a_btcusdt_perp" / "raw" / "_manifest.json",
        "proc_dir":       HFMM_ROOT / "data" / "phase1a_btcusdt_perp" / "processed",
        "report_basename": "step5_inspection_report.txt",
        "fname_prefix":   "binance-futures",
        "targets": [
            # === Group E: Binance Futures BTCUSDT perpetual (pivot venue, 2024-{03,06,09}-01) ===
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
DOWNLOAD_TARGETS = _active["targets"]
RAW_DIR = _active["raw_dir"].resolve()
MANIFEST_PATH = _active["manifest_path"].resolve()


def build_url(t: dict) -> str:
    yyyy, mm, dd = t["date"].split("-")
    return f"{BASE_URL}/{t['exchange']}/{t['datatype']}/{yyyy}/{mm}/{dd}/{t['symbol']}.csv.gz"


def build_filename(t: dict) -> str:
    yyyymmdd = t["date"].replace("-", "")
    return f"{t['exchange']}_{t['datatype']}_{t['symbol']}_{yyyymmdd}.csv.gz"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_gzip(path: Path) -> tuple[bool, bool]:
    """Return (magic_ok, decompressible_ok). Reads only the first line for decomp check."""
    with path.open("rb") as f:
        magic = f.read(2)
    magic_ok = magic == GZIP_MAGIC
    decompressible_ok = False
    if magic_ok:
        try:
            with gzip.open(path, "rb") as gz:
                _ = gz.readline()
            decompressible_ok = True
        except OSError:
            decompressible_ok = False
    return magic_ok, decompressible_ok


def load_existing_manifest() -> dict[str, dict]:
    if not MANIFEST_PATH.exists():
        return {}
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {entry["filename"]: entry for entry in data.get("files", [])}


def write_manifest(entries: list[dict]) -> None:
    payload = {
        "manifest_version": 1,
        "written_utc": datetime.now(timezone.utc).isoformat(),
        "files": entries,
    }
    tmp = MANIFEST_PATH.with_suffix(".json.partial")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, MANIFEST_PATH)


def preflight_check_partials() -> None:
    """Fail loud if any stale .partial files are present in data/raw/."""
    stale = list(RAW_DIR.glob("*.partial"))
    if stale:
        names = ", ".join(p.name for p in stale)
        raise SystemExit(
            f"FAIL: stale .partial file(s) present in {RAW_DIR}: {names}\n"
            "Likely an interrupted prior run. Investigate and remove manually before re-running."
        )


def stream_download(url: str, dest_partial: Path) -> dict:
    """GET-stream the URL into dest_partial. Returns response metadata + bytes_written."""
    started = datetime.now(timezone.utc)
    bytes_written = 0
    with requests.get(url, stream=True, allow_redirects=True, timeout=TIMEOUT_S) as r:
        status = r.status_code
        content_length_header = r.headers.get("Content-Length")
        last_modified_header = r.headers.get("Last-Modified")
        content_type_header = r.headers.get("Content-Type")
        if status != 200:
            raise SystemExit(f"FAIL: HTTP {status} for {url}")
        expected_bytes = int(content_length_header) if content_length_header else None
        next_progress_pct = 10

        with dest_partial.open("wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                f.write(chunk)
                bytes_written += len(chunk)
                if expected_bytes:
                    pct = (bytes_written * 100) // expected_bytes
                    while pct >= next_progress_pct and next_progress_pct <= 100:
                        print(f"    {next_progress_pct:3d}%  ({bytes_written:>12,} / {expected_bytes:,} bytes)")
                        next_progress_pct += 10
    return {
        "started_utc": started.isoformat(),
        "status": status,
        "content_length_header": content_length_header,
        "last_modified_header": last_modified_header,
        "content_type_header": content_type_header,
        "bytes_written": bytes_written,
    }


def process_target(t: dict, existing_manifest: dict[str, dict]) -> dict:
    url = build_url(t)
    filename = build_filename(t)
    final_path = RAW_DIR / filename
    partial_path = RAW_DIR / (filename + ".partial")

    if final_path.exists():
        existing = existing_manifest.get(filename)
        if existing is None:
            raise SystemExit(
                f"FAIL: {filename} exists on disk but has no _manifest.json entry. "
                "Refusing to silently overwrite or skip - investigate manually."
            )
        actual_sha = sha256_file(final_path)
        if actual_sha != existing["sha256"]:
            raise SystemExit(
                f"FAIL: {filename} exists but sha256 mismatches manifest.\n"
                f"  manifest sha256: {existing['sha256']}\n"
                f"  actual sha256  : {actual_sha}\n"
                "Refusing to silently re-download - investigate manually."
            )
        print(f"[SKIP] {filename} already present, sha256 matches manifest.")
        return existing

    print(f"[GET] {url}")
    print(f"  -> {final_path.name}")
    resp = stream_download(url, partial_path)
    if resp["content_length_header"]:
        expected = int(resp["content_length_header"])
        if resp["bytes_written"] != expected:
            raise SystemExit(
                f"FAIL: byte count mismatch for {filename}: "
                f"wrote {resp['bytes_written']}, Content-Length said {expected}"
            )

    os.replace(partial_path, final_path)

    magic_ok, decomp_ok = verify_gzip(final_path)
    if not magic_ok:
        raise SystemExit(f"FAIL: {filename} does not start with gzip magic bytes 0x1f 0x8b.")
    if not decomp_ok:
        raise SystemExit(f"FAIL: {filename} has gzip magic but gzip.open() could not read the first line.")
    sha = sha256_file(final_path)

    print(f"  bytes        : {resp['bytes_written']:,}")
    print(f"  sha256       : {sha}")
    print(f"  gzip magic   : OK")
    print(f"  decompressible: OK")

    return {
        "filename": filename,
        "url": url,
        "exchange": t["exchange"],
        "datatype": t["datatype"],
        "symbol": t["symbol"],
        "date": t["date"],
        "sha256": sha,
        "bytes": resp["bytes_written"],
        "download_utc": resp["started_utc"],
        "content_length_header": int(resp["content_length_header"]) if resp["content_length_header"] else None,
        "last_modified_header": resp["last_modified_header"],
        "content_type_header": resp["content_type_header"],
        "http_status": resp["status"],
        "gzip_signature_ok": magic_ok,
        "gzip_first_line_decompressed_ok": decomp_ok,
    }


def main() -> int:
    print(f"Tardis batch download started at {datetime.now(timezone.utc).isoformat()}")
    print(f"  raw dir : {RAW_DIR}")
    print(f"  manifest: {MANIFEST_PATH}")
    print(f"  targets : {len(DOWNLOAD_TARGETS)}\n")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    preflight_check_partials()
    existing_manifest = load_existing_manifest()
    print(f"Existing manifest entries: {len(existing_manifest)}\n")

    entries: list[dict] = []
    overall_started = datetime.now(timezone.utc)
    for i, t in enumerate(DOWNLOAD_TARGETS, start=1):
        print(f"--- [{i}/{len(DOWNLOAD_TARGETS)}] {t['exchange']}/{t['datatype']}/{t['date']}/{t['symbol']} ---")
        entries.append(process_target(t, existing_manifest))
        print()

    write_manifest(entries)
    overall_elapsed_s = (datetime.now(timezone.utc) - overall_started).total_seconds()
    total_bytes = sum(e["bytes"] for e in entries)
    print("=" * 70)
    print(f"OK: {len(entries)}/{len(DOWNLOAD_TARGETS)} files present (downloaded or already cached).")
    print(f"  Total bytes : {total_bytes:,}")
    print(f"  Elapsed     : {overall_elapsed_s:.1f}s")
    print(f"  Manifest    : {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
