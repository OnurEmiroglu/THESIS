"""Run lifecycle management: context, seeding, logging, and metrics."""
# Çalıştırma Yaşam Döngüsü (WP0)
# ----------------------------------
# Her deneyi benzersiz run_id ile izler, config snapshot ve git bilgisi kaydeder.
# setup_run() → RunContext oluşturur, finalize_run() → durumu yazar.
# CSVMetricLogger ile metrikler satır satır CSV'ye eklenir.

from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import random

try:
    import numpy as np
except Exception:
    np = None


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def get_git_commit_short() -> str:
    """Return short git commit hash if available, otherwise 'nogit'."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8").strip()
    except Exception:
        return "nogit"


# Benzersiz çalıştırma kimliği üretir: YYYYMMDD-HHMMSS_seed<S>_<tag>_<commit>
# Tekrarlanabilirlik için seed ve git commit hash'i içerir.
def make_run_id(seed: int, run_tag: Optional[str] = None) -> str:
    """
    run_id format: YYYYMMDD-HHMMSS_seed<seed>_<tag>_<commit>
    """
    ts = _utc_timestamp()
    commit = get_git_commit_short()
    tag = (run_tag or "run").replace(" ", "-")
    return f"{ts}_seed{seed}_{tag}_{commit}"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def set_global_seed(seed: int) -> None:
    """
    Best-effort reproducibility across stdlib + numpy.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    if np is not None:
        np.random.seed(seed)


def build_logger(run_dir: Path, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("thesis")
    logger.setLevel(level.upper())
    logger.handlers.clear()
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = logging.FileHandler(run_dir / "run.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


class CSVMetricLogger:
    def __init__(self, path: Path):
        self.path = path
        self._header_written = False

    def log(self, row: Dict[str, Any]) -> None:
        import csv

        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = (not self._header_written) and (not self.path.exists())

        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
                self._header_written = True
            writer.writerow(row)


@dataclass
class RunContext:
    run_id: str
    run_dir: Path
    plots_dir: Path
    config: Dict[str, Any]
    logger: logging.Logger
    metrics: CSVMetricLogger
    resume_run_id: Optional[str] = None


# Yeni bir deney çalıştırmasını başlatır: dizin oluşturur, seed ayarlar,
# config snapshot ve meta bilgilerini kaydeder, logger ve metrics nesnelerini döner.
def setup_run(
    config_path: str | Path,
    results_root: str | Path = "results/runs",
    resume_run_id: Optional[str] = None,
) -> RunContext:
    config_path = Path(config_path)
    cfg = load_json(config_path)

    if "seed" not in cfg or not isinstance(cfg["seed"], int):
        raise ValueError("Config must include an integer field: 'seed'")

    seed = int(cfg["seed"])
    results_root = Path(results_root)
    if resume_run_id is not None:
        run_id = resume_run_id
        run_dir = results_root / run_id
        if not run_dir.exists():
            raise FileNotFoundError(
                f"--resume target does not exist: {run_dir.as_posix()}"
            )
        plots_dir = run_dir / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_id = make_run_id(seed=seed, run_tag=cfg.get("run_tag"))
        run_dir = results_root / run_id
        plots_dir = run_dir / "plots"
        run_dir.mkdir(parents=True, exist_ok=False)
        plots_dir.mkdir(parents=True, exist_ok=True)

    set_global_seed(seed)

    logger = build_logger(run_dir)

    cfg = {**cfg, "run_id": run_id}
    if resume_run_id is None:
        save_json(run_dir / "config_snapshot.json", cfg)
        meta = {
            "run_id": run_id,
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "config_path": str(config_path.as_posix()),
            "git_commit": get_git_commit_short(),
            "python": sys.version,
            "platform": platform.platform(),
        }
        save_json(run_dir / "meta.json", meta)
        logger.info(f"Run started: {run_id}")
    else:
        logger.info(f"Run RESUMED: {run_id}")
    logger.info(f"Run dir: {run_dir.as_posix()}")

    metrics = CSVMetricLogger(run_dir / "metrics.csv")
    return RunContext(
        run_id=run_id,
        run_dir=run_dir,
        plots_dir=plots_dir,
        config=cfg,
        logger=logger,
        metrics=metrics,
        resume_run_id=resume_run_id,
    )

# Çalıştırmayı sonlandırır: status.json dosyasına başarı/hata durumunu yazar.
def finalize_run(ctx: RunContext, status: str = "success", error: str | None = None) -> None:
    payload = {
        "run_id": ctx.run_id,
        "status": status,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }
    save_json(ctx.run_dir / "status.json", payload)

    if status == "success":
        ctx.logger.info("Run finished successfully.")
    else:
        ctx.logger.error(f"Run finished with status={status}. error={error}")



