"""Shared helpers for --resume aware sweep jobs (wp6).

A cell is considered complete only if BOTH:
  * the expected model .zip exists on disk, AND
  * a (seed, condition, variant) row exists in the metrics CSV.

If exactly one of those exists, the run is in an inconsistent state.
The job must stop and report — silently skipping such an orphan would
risk data loss (the metric row may have been written for a partially
trained model, or the model may exist for a cell whose metrics never
landed). Re-evaluation from a saved model is not implemented; until
it is, fail loudly so the operator can decide.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_completed_set(metrics_path: Path):
    """Return (rows, completed_set) from an existing metrics CSV.

    rows           — list[dict], original CSV rows preserved as-is for
                     re-emission at the end of the run.
    completed_set  — set[tuple[int, str, str]] keyed by
                     (seed, condition, variant).

    If the file does not exist, returns ([], set()).
    """
    if not metrics_path.exists():
        return [], set()
    df = pd.read_csv(metrics_path)
    rows = df.to_dict("records")
    completed: set[tuple[int, str, str]] = set()
    for r in rows:
        completed.add((int(r["seed"]), str(r["condition"]), str(r["variant"])))
    return rows, completed


def check_cell_consistency(
    model_exists: bool,
    metric_exists: bool,
    *,
    seed: int,
    condition: str,
    variant: str,
) -> str:
    """Classify a cell during resume and raise on inconsistency.

    Returns:
        "skip"  — both model and metric row already present; skip the cell.
        "train" — neither present; train normally.

    Raises:
        RuntimeError — exactly one of (model, metric) is present. The
            error message names the orphan tuple and which artifact is
            missing.
    """
    if model_exists and metric_exists:
        return "skip"
    if not model_exists and not metric_exists:
        return "train"

    cell = (seed, condition, variant)
    if model_exists and not metric_exists:
        missing = "metrics row"
        present = "model file"
    else:
        missing = "model file"
        present = "metrics row"
    raise RuntimeError(
        f"Inconsistent resume state for cell {cell}: {present} exists but "
        f"{missing} is missing. Re-evaluation from saved models is not "
        f"implemented. To proceed: either delete the orphan {present.lower()} "
        f"so the cell re-trains from scratch, or implement re-evaluation. "
        f"Stopping to avoid silent data loss."
    )
