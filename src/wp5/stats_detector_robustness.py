"""Statistical analysis of detector robustness experiment results."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


def find_results_csv() -> Path:
    """Find the most recent detector-full run's metrics CSV."""
    runs_dir = Path("results/runs")
    candidates = sorted(runs_dir.glob("*detector-full*"), key=lambda p: p.name)
    if not candidates:
        print("ERROR: No detector-full run found under results/runs/")
        sys.exit(1)
    run_dir = candidates[-1]
    csv_path = run_dir / "metrics_detector_pilot.csv"
    if not csv_path.exists():
        csv_path = run_dir / "metrics_detector_compare.csv"
    if not csv_path.exists():
        print(f"ERROR: No metrics CSV in {run_dir}")
        sys.exit(1)
    return csv_path


def paired_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Paired t-test: ppo_aware vs ppo_blind for each detector x metric."""
    rows = []
    for detector in sorted(df["detector"].unique()):
        sub = df[df["detector"] == detector]
        aware = sub[sub["strategy"] == "ppo_aware"].sort_values("seed")
        blind = sub[sub["strategy"] == "ppo_blind"].sort_values("seed")

        for metric in ["sharpe_like", "final_equity"]:
            a = aware[metric].values
            b = blind[metric].values
            diff = a - b
            t_stat, p_val = stats.ttest_rel(a, b)
            rows.append({
                "detector": detector,
                "metric": metric,
                "mean_aware": float(np.mean(a)),
                "mean_blind": float(np.mean(b)),
                "mean_diff": float(np.mean(diff)),
                "t_stat": float(t_stat),
                "p_value": float(p_val),
                "significant": "Yes" if p_val < 0.05 else "No",
            })
    return pd.DataFrame(rows)


def anova_across_detectors(df: pd.DataFrame) -> dict:
    """One-way ANOVA: does ppo_aware sharpe differ across detectors?"""
    aware = df[df["strategy"] == "ppo_aware"]
    groups = [
        g["sharpe_like"].values
        for _, g in aware.groupby("detector")
    ]
    f_stat, p_val = stats.f_oneway(*groups)
    return {
        "test": "one-way ANOVA (ppo_aware sharpe_like across detectors)",
        "F_stat": float(f_stat),
        "p_value": float(p_val),
        "significant": "Yes" if p_val < 0.05 else "No",
    }


def main():
    csv_path = find_results_csv()
    print(f"Reading: {csv_path}\n")

    df = pd.read_csv(csv_path)
    print(f"Rows: {len(df)}, Detectors: {sorted(df['detector'].unique())}")
    print(f"Seeds: {sorted(df['seed'].unique())}\n")

    # --- Paired t-tests ---
    results = paired_tests(df)

    fmt = {
        "mean_aware": "{:.4f}",
        "mean_blind": "{:.4f}",
        "mean_diff": "{:.4f}",
        "t_stat": "{:.4f}",
        "p_value": "{:.4f}",
    }
    table_str = results.to_string(
        index=False,
        formatters={k: v.format for k, v in fmt.items()},
    )

    print("=" * 90)
    print("PAIRED T-TEST: ppo_aware vs ppo_blind (per detector, per metric)")
    print("=" * 90)
    print(table_str)

    # --- ANOVA ---
    anova = anova_across_detectors(df)
    anova_str = (
        f"\n{'=' * 90}\n"
        f"ONE-WAY ANOVA: ppo_aware sharpe_like across detectors\n"
        f"{'=' * 90}\n"
        f"F-stat: {anova['F_stat']:.4f}, p-value: {anova['p_value']:.4f}, "
        f"significant: {anova['significant']}\n"
    )
    print(anova_str)

    # --- Summary ---
    summary_lines = [
        "\nSUMMARY",
        "-" * 40,
    ]
    sig_count = int((results["significant"] == "Yes").sum())
    summary_lines.append(
        f"Significant tests (p<0.05): {sig_count} / {len(results)}"
    )
    if sig_count == 0:
        summary_lines.append(
            "Null result: no detector shows significant aware vs blind difference."
        )
    else:
        sig_rows = results[results["significant"] == "Yes"]
        for _, r in sig_rows.iterrows():
            direction = "aware > blind" if r["mean_diff"] > 0 else "blind > aware"
            summary_lines.append(
                f"  {r['detector']} / {r['metric']}: p={r['p_value']:.4f} ({direction})"
            )
    summary_str = "\n".join(summary_lines)
    print(summary_str)

    # --- Save to file ---
    out_path = Path("results/stats_detector_robustness.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Source: {csv_path}\n\n")
        f.write("PAIRED T-TEST: ppo_aware vs ppo_blind (per detector, per metric)\n")
        f.write(table_str + "\n")
        f.write(anova_str + "\n")
        f.write(summary_str + "\n")
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
