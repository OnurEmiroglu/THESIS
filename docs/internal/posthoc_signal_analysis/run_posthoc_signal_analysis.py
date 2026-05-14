"""Lightweight post-hoc signal redundancy diagnostics.

This script is intentionally read-only with respect to existing experiment
artifacts. It writes all new outputs into docs/internal/posthoc_signal_analysis.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    normalized_mutual_info_score,
    r2_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RANDOM_STATE = 123
REGIME_LABELS = ["L", "M", "H"]
TICK_SIZE = 0.01


ACTION_RUNS = [
    {
        "run_group": "wp5_main",
        "path": ROOT / "results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc",
        "strategies": {"ppo_aware", "ppo_blind"},
    },
    {
        "run_group": "wp5_ablation",
        "path": ROOT / "results/runs/20260327-171914_seed1_wp5-ablation_e1545a5",
        "strategies": {"ppo_sigma_only", "ppo_combined", "ppo_regime_only"},
    },
    {
        "run_group": "wp5_misspec_mild",
        "path": ROOT / "results/runs/20260408-160248_seed1_w5-misspec-mild_5d9dc23",
        "strategies": {"ppo_sigma_only", "ppo_combined", "ppo_regime_only"},
    },
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def valid_regime(series: pd.Series) -> pd.Series:
    return series.astype(str).isin(REGIME_LABELS)


def add_group_time_split(df: pd.DataFrame, group_cols: list[str], frac: float = 0.7) -> pd.DataFrame:
    out = df.copy()
    out["split"] = "test"
    group_key = group_cols[0] if len(group_cols) == 1 else group_cols
    for _, idx in out.groupby(group_key, sort=False).groups.items():
        idx = list(idx)
        cutoff = max(1, min(len(idx) - 1, int(math.floor(frac * len(idx)))))
        out.loc[idx[:cutoff], "split"] = "train"
        out.loc[idx[cutoff:], "split"] = "test"
    return out


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def discover_wp2_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates: list[Path] = []
    direct = ROOT / "data/processed/wp2_synth.csv"
    if direct.exists():
        candidates.append(direct)
    candidates.extend(sorted((ROOT / "results/runs").rglob("wp2_synth_snapshot.csv")))
    candidates.extend(sorted((ROOT / "results/runs").rglob("wp2_synth.csv")))

    seen: dict[str, Path] = {}
    duplicates: dict[str, list[str]] = {}
    for path in candidates:
        if not path.exists():
            continue
        digest = sha256_file(path)
        duplicates.setdefault(digest, []).append(rel(path))
        if digest not in seen:
            seen[digest] = path

    frames = []
    manifest_rows = []
    required = {"t", "mid", "ret", "rv", "sigma_hat", "regime_true", "regime_hat"}
    for i, (digest, path) in enumerate(sorted(seen.items(), key=lambda kv: rel(kv[1]))):
        df = pd.read_csv(path)
        missing = required - set(df.columns)
        if missing:
            continue
        source_id = f"wp2_{i:02d}"
        df = df.copy()
        df["source_id"] = source_id
        df["source_path"] = rel(path)
        df["row_in_source"] = np.arange(len(df))
        frames.append(df)
        manifest_rows.append(
            {
                "source_id": source_id,
                "source_path": rel(path),
                "sha256": digest,
                "rows": len(df),
                "duplicate_paths": " | ".join(duplicates[digest]),
            }
        )

    if not frames:
        raise FileNotFoundError("No usable frozen WP2 synthetic CSVs were found.")

    panel = pd.concat(frames, ignore_index=True)
    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(OUT / "source_manifest.csv", index=False)
    return panel, manifest


def split_wp2_dataset(panel: pd.DataFrame, target_col: str) -> pd.DataFrame:
    df = panel.copy()
    df = df.dropna(subset=["sigma_hat"])
    df = df[valid_regime(df["regime_hat"])]
    df = df[valid_regime(df[target_col])]
    df = df.sort_values(["source_id", "row_in_source"]).reset_index(drop=True)
    return add_group_time_split(df, ["source_id"])


def classification_row(
    target: str,
    model_name: str,
    evaluation_mode: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_train: int,
) -> dict:
    return {
        "target_label": target,
        "model": model_name,
        "evaluation_mode": evaluation_mode,
        "n_train": n_train,
        "n_test": len(y_true),
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, labels=REGIME_LABELS, average="macro"),
        "normalized_mutual_information": normalized_mutual_info_score(y_true, y_pred),
    }


def plot_confusion(predictions: dict[str, tuple[np.ndarray, np.ndarray]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), constrained_layout=True)
    for ax, (model_name, (y_true, y_pred)) in zip(axes, predictions.items()):
        cm = confusion_matrix(y_true, y_pred, labels=REGIME_LABELS, normalize="true")
        im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
        ax.set_title(model_name)
        ax.set_xticks(range(len(REGIME_LABELS)), REGIME_LABELS)
        ax.set_yticks(range(len(REGIME_LABELS)), REGIME_LABELS)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Observed")
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, f"{cm[i, j]:.2f}", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.85, label="Row-normalized share")
    fig.suptitle("Regime_hat from sigma_hat only, within-source calibration")
    fig.savefig(OUT / "confusion_matrix.png", dpi=180)
    plt.close(fig)


def plot_sigma_overlap(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cap = float(np.nanpercentile(df["sigma_hat"], 99.5))
    bins = np.linspace(0, cap, 55)
    colors = {"L": "#2E7D32", "M": "#F9A825", "H": "#C62828"}
    for lab in REGIME_LABELS:
        vals = df.loc[df["regime_hat"] == lab, "sigma_hat"].clip(upper=cap)
        ax.hist(vals, bins=bins, density=True, alpha=0.42, label=lab, color=colors[lab])
    ax.set_xlabel("sigma_hat")
    ax.set_ylabel("Density")
    ax.set_title("Sigma_hat overlap by observed regime_hat")
    ax.legend(title="regime_hat")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "sigma_regime_overlap.png", dpi=180)
    plt.close(fig)


def run_predictability(panel: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    confusion_predictions: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    primary_df = split_wp2_dataset(panel, "regime_hat")

    for target_col in ["regime_hat", "regime_true"]:
        df = split_wp2_dataset(panel, target_col)
        train = df[df["split"] == "train"]
        test = df[df["split"] == "test"]
        x_train = train[["sigma_hat"]].to_numpy()
        y_train = train[target_col].astype(str).to_numpy()
        x_test = test[["sigma_hat"]].to_numpy()
        y_test = test[target_col].astype(str).to_numpy()

        model_factories = {
            "logistic_regression": Pipeline(
                [
                    ("scale", StandardScaler()),
                    (
                        "clf",
                        LogisticRegression(
                            max_iter=2000,
                            class_weight="balanced",
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=80,
                max_depth=5,
                min_samples_leaf=50,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=1,
            ),
        }

        for model_name, model in model_factories.items():
            model.fit(x_train, y_train)
            pred = model.predict(x_test)
            rows.append(classification_row(target_col, model_name, "pooled_global", y_test, pred, len(train)))

        for model_name in ["logistic_regression", "random_forest"]:
            all_true: list[str] = []
            all_pred: list[str] = []
            total_train = 0
            for _sid, g in df.groupby("source_id", sort=False):
                g_train = g[g["split"] == "train"]
                g_test = g[g["split"] == "test"]
                if g_train[target_col].nunique() < 2 or g_test.empty:
                    continue
                if model_name == "logistic_regression":
                    model = Pipeline(
                        [
                            ("scale", StandardScaler()),
                            (
                                "clf",
                                LogisticRegression(
                                    max_iter=2000,
                                    class_weight="balanced",
                                    random_state=RANDOM_STATE,
                                ),
                            ),
                        ]
                    )
                else:
                    model = RandomForestClassifier(
                        n_estimators=80,
                        max_depth=5,
                        min_samples_leaf=10,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=1,
                    )
                model.fit(g_train[["sigma_hat"]].to_numpy(), g_train[target_col].astype(str).to_numpy())
                pred = model.predict(g_test[["sigma_hat"]].to_numpy())
                all_true.extend(g_test[target_col].astype(str).tolist())
                all_pred.extend(pred.tolist())
                total_train += len(g_train)

            rows.append(
                classification_row(
                    target_col,
                    model_name,
                    "within_source_calibrated",
                    np.asarray(all_true),
                    np.asarray(all_pred),
                    total_train,
                )
            )
            if target_col == "regime_hat":
                title = "Logistic regression" if model_name == "logistic_regression" else "Random forest"
                confusion_predictions[title] = (np.asarray(all_true), np.asarray(all_pred))

    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "predictability_metrics.csv", index=False)
    plot_confusion(confusion_predictions)
    plot_sigma_overlap(primary_df)

    main = metrics[
        (metrics["target_label"] == "regime_hat")
        & (metrics["evaluation_mode"] == "within_source_calibrated")
    ].copy()
    best = main.sort_values("balanced_accuracy", ascending=False).iloc[0]
    pooled_best = metrics[
        (metrics["target_label"] == "regime_hat") & (metrics["evaluation_mode"] == "pooled_global")
    ].sort_values("balanced_accuracy", ascending=False).iloc[0]
    true_best = metrics[
        (metrics["target_label"] == "regime_true")
        & (metrics["evaluation_mode"] == "within_source_calibrated")
    ].sort_values("balanced_accuracy", ascending=False).iloc[0]

    md = [
        "# Regime Predictability From sigma_hat",
        "",
        "## Scope",
        "",
        (
            "This diagnostic asks whether the categorical regime labels present in frozen "
            "synthetic artifacts are predictable from `sigma_hat` alone. The primary target "
            "is `regime_hat`, because that is the explicit categorical label used by the "
            "main regime-aware policies. `regime_true` is reported as a secondary reference."
        ),
        "",
        "## Data",
        "",
        f"- Unique WP2-style synthetic CSVs used: {len(manifest)}",
        f"- Post-warmup rows for primary classifier: {len(primary_df):,}",
        "- Split: chronological 70/30 within each source CSV.",
        "- Features: `sigma_hat` only.",
        "",
        "## Main Results",
        "",
        (
            f"- Best within-source `regime_hat` classifier: {best['model']} with accuracy "
            f"{best['accuracy']:.3f}, balanced accuracy {best['balanced_accuracy']:.3f}, "
            f"macro F1 {best['macro_f1']:.3f}, and NMI {best['normalized_mutual_information']:.3f}."
        ),
        (
            f"- Best pooled-global `regime_hat` classifier: {pooled_best['model']} with balanced "
            f"accuracy {pooled_best['balanced_accuracy']:.3f}. The lower pooled score reflects "
            "source-specific calibration of the thresholded regime detector."
        ),
        (
            f"- Secondary `regime_true` reference: best balanced accuracy "
            f"{true_best['balanced_accuracy']:.3f}. This indicates that `sigma_hat` also tracks "
            "the latent synthetic volatility state, although the thesis claim concerns the "
            "observed categorical channel used by the policies."
        ),
        "",
        "## Interpretation",
        "",
        (
            "The primary result is consistent with the redundancy interpretation: once each "
            "synthetic source is calibrated on its own training portion, the observed categorical "
            "`regime_hat` channel is almost entirely recoverable from `sigma_hat` alone. This "
            "should be read as mechanistic support for overlap between the two observed signals, "
            "not as evidence that all latent regime information is absent."
        ),
    ]
    (OUT / "predictability_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return metrics


def build_incremental_dataset(panel: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for sid, g in panel.sort_values(["source_id", "row_in_source"]).groupby("source_id", sort=False):
        h = g.copy()
        h["future_abs_return_ticks"] = h["ret"].shift(-1).abs() / TICK_SIZE
        h = h.dropna(subset=["sigma_hat", "future_abs_return_ticks"])
        h = h[valid_regime(h["regime_hat"])]
        h = h.sort_values("row_in_source").reset_index(drop=True)
        h = add_group_time_split(h, ["source_id"])
        frames.append(h)
    return pd.concat(frames, ignore_index=True)


def linear_design(df: pd.DataFrame, include_regime: bool) -> pd.DataFrame:
    x = pd.DataFrame({"sigma_hat": df["sigma_hat"].astype(float).to_numpy()}, index=df.index)
    if include_regime:
        x["regime_M"] = (df["regime_hat"].astype(str) == "M").astype(float).to_numpy()
        x["regime_H"] = (df["regime_hat"].astype(str) == "H").astype(float).to_numpy()
    return sm.add_constant(x, has_constant="add")


def run_incremental_value(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = build_incremental_dataset(panel)
    train = df[df["split"] == "train"]
    test = df[df["split"] == "test"]
    y_train = train["future_abs_return_ticks"].astype(float)
    y_test = test["future_abs_return_ticks"].astype(float)

    fits = {}
    rows = []
    for model_name, include_regime in [
        ("A_sigma_hat", False),
        ("B_sigma_hat_plus_regime", True),
    ]:
        x_train = linear_design(train, include_regime)
        x_test = linear_design(test, include_regime)
        x_test = x_test.reindex(columns=x_train.columns, fill_value=0.0)
        fit = sm.OLS(y_train, x_train).fit()
        pred = fit.predict(x_test)
        fits[model_name] = fit
        rows.append(
            {
                "target": "future_abs_return_ticks",
                "model": model_name,
                "n_train": len(train),
                "n_test": len(test),
                "oos_r2": r2_score(y_test, pred),
                "mae": mean_absolute_error(y_test, pred),
                "rmse": rmse(y_test.to_numpy(), pred.to_numpy()),
                "aic_train": fit.aic,
                "bic_train": fit.bic,
            }
        )

    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "incremental_metrics.csv", index=False)

    fit_a = fits["A_sigma_hat"]
    fit_b = fits["B_sigma_hat_plus_regime"]
    f_stat, f_pvalue, f_df_diff = fit_b.compare_f_test(fit_a)
    a = metrics[metrics["model"] == "A_sigma_hat"].iloc[0]
    b = metrics[metrics["model"] == "B_sigma_hat_plus_regime"].iloc[0]
    comparison = pd.DataFrame(
        [
            {
                "target": "future_abs_return_ticks",
                "comparison": "B_minus_A",
                "delta_oos_r2": b["oos_r2"] - a["oos_r2"],
                "delta_mae": b["mae"] - a["mae"],
                "delta_rmse": b["rmse"] - a["rmse"],
                "delta_aic_train": b["aic_train"] - a["aic_train"],
                "delta_bic_train": b["bic_train"] - a["bic_train"],
                "nested_f_stat": f_stat,
                "nested_f_pvalue": f_pvalue,
                "nested_f_df_diff": f_df_diff,
                "coef_sigma_hat_model_B": fit_b.params.get("sigma_hat", np.nan),
                "p_sigma_hat_model_B": fit_b.pvalues.get("sigma_hat", np.nan),
                "coef_regime_M": fit_b.params.get("regime_M", np.nan),
                "p_regime_M": fit_b.pvalues.get("regime_M", np.nan),
                "coef_regime_H": fit_b.params.get("regime_H", np.nan),
                "p_regime_H": fit_b.pvalues.get("regime_H", np.nan),
            }
        ]
    )
    comparison.to_csv(OUT / "model_comparison_table.csv", index=False)

    delta_r2 = float(comparison["delta_oos_r2"].iloc[0])
    delta_mae = float(comparison["delta_mae"].iloc[0])
    delta_rmse = float(comparison["delta_rmse"].iloc[0])
    md = [
        "# Incremental Predictive Value After sigma_hat",
        "",
        "## Scope",
        "",
        (
            "The predictive target is next-step absolute mid return in ticks, "
            "`abs(ret[t+1]) / tick_size`. Features are measured at time `t`, so the "
            "target is forward-looking while the regressors remain contemporaneously observed."
        ),
        "",
        "## Design",
        "",
        "- Model A: `future_abs_return_ticks ~ sigma_hat`.",
        "- Model B: `future_abs_return_ticks ~ sigma_hat + regime_hat`.",
        "- Split: chronological 70/30 within each source CSV.",
        "- Estimator: OLS on the training split, evaluated out of sample on the held-out tail.",
        "",
        "## Main Results",
        "",
        (
            f"- OOS R2 changes by {delta_r2:+.6f} when `regime_hat` is added after "
            "`sigma_hat`."
        ),
        f"- MAE changes by {delta_mae:+.6f}; RMSE changes by {delta_rmse:+.6f}.",
        (
            f"- Nested training-set F-test p-value for the regime terms: "
            f"{float(comparison['nested_f_pvalue'].iloc[0]):.4g}."
        ),
        "",
        "## Interpretation",
        "",
        (
            "The relevant evidence is the held-out predictive change, not only the training "
            "significance of extra step-function terms. Small OOS deltas support the view "
            "that, for this synthetic setting and target, the explicit label adds limited "
            "incremental predictive content once `sigma_hat` is observed."
        ),
    ]
    (OUT / "incremental_value_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return metrics, comparison


def read_run_config(run_dir: Path) -> dict:
    with (run_dir / "config_snapshot.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def action_test_exog(run_dir: Path) -> tuple[pd.DataFrame, int, int]:
    cfg = read_run_config(run_dir)
    n_full = int(cfg["episode"]["n_steps"])
    train_frac = float(cfg.get("wp5", {}).get("train_frac", cfg.get("sweep", {}).get("train_frac", 0.7)))
    n_train = math.floor(train_frac * n_full)
    n_test = n_full - n_train
    exog_path = run_dir / "wp2_synth_snapshot.csv"
    if not exog_path.exists():
        raise FileNotFoundError(f"Missing WP2 snapshot for {run_dir}")
    exog = pd.read_csv(exog_path)
    return exog.iloc[n_train : n_train + n_test + 1].reset_index(drop=True), n_train, n_test


def load_action_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    curve_re = re.compile(r"seed(\d+)_(.+)_test\.csv$")
    frames = []
    rows = []

    for spec in ACTION_RUNS:
        run_dir = spec["path"]
        if not run_dir.exists():
            rows.append({"run_group": spec["run_group"], "status": "missing_run", "detail": rel(run_dir)})
            continue
        try:
            exog, _n_train, n_test = action_test_exog(run_dir)
        except FileNotFoundError as exc:
            rows.append({"run_group": spec["run_group"], "status": "missing_exog", "detail": str(exc)})
            continue

        curves_dir = run_dir / "curves"
        for curve_path in sorted(curves_dir.glob("*_test.csv")):
            match = curve_re.match(curve_path.name)
            if not match:
                continue
            seed = int(match.group(1))
            strategy = match.group(2)
            if strategy not in spec["strategies"]:
                continue
            curve = pd.read_csv(curve_path)
            if len(curve) != n_test + 1 or len(exog) != len(curve):
                rows.append(
                    {
                        "run_group": spec["run_group"],
                        "seed": seed,
                        "strategy": strategy,
                        "status": "skipped_length_mismatch",
                        "detail": rel(curve_path),
                    }
                )
                continue
            if "regime_hat" not in curve.columns:
                rows.append(
                    {
                        "run_group": spec["run_group"],
                        "seed": seed,
                        "strategy": strategy,
                        "status": "skipped_no_regime_hat",
                        "detail": rel(curve_path),
                    }
                )
                continue
            match_rate = float(
                (curve["regime_hat"].astype(str).to_numpy() == exog["regime_hat"].astype(str).to_numpy()).mean()
            )
            if match_rate < 0.995:
                rows.append(
                    {
                        "run_group": spec["run_group"],
                        "seed": seed,
                        "strategy": strategy,
                        "status": "skipped_snapshot_not_aligned",
                        "match_rate": match_rate,
                        "detail": rel(curve_path),
                    }
                )
                continue

            joined = curve.copy()
            joined["sigma_hat"] = exog["sigma_hat"].to_numpy()
            joined["regime_true"] = exog["regime_true"].astype(str).to_numpy()
            joined["run_group"] = spec["run_group"]
            joined["run_path"] = rel(run_dir)
            joined["curve_path"] = rel(curve_path)
            joined["seed"] = seed
            joined["strategy"] = strategy
            joined["source_id"] = f"{spec['run_group']}__seed{seed}__{strategy}"
            frames.append(joined)
            rows.append(
                {
                    "run_group": spec["run_group"],
                    "seed": seed,
                    "strategy": strategy,
                    "status": "accepted",
                    "match_rate": match_rate,
                    "detail": rel(curve_path),
                }
            )

    audit = pd.DataFrame(rows)
    audit.to_csv(OUT / "action_curve_alignment.csv", index=False)
    if not frames:
        raise FileNotFoundError("No action curves could be aligned to frozen WP2 snapshots.")
    actions = pd.concat(frames, ignore_index=True)
    actions = actions.dropna(subset=["h", "m", "sigma_hat"])
    actions = actions[valid_regime(actions["regime_hat"])]
    actions = actions.sort_values(["run_group", "strategy", "seed", "t"]).reset_index(drop=True)
    actions = add_group_time_split(actions, ["source_id"])
    return actions, audit


def action_design(df: pd.DataFrame, include_regime: bool) -> pd.DataFrame:
    x = pd.DataFrame({"sigma_hat": df["sigma_hat"].astype(float).to_numpy()}, index=df.index)
    if include_regime:
        for lab in REGIME_LABELS:
            x[f"regime_{lab}"] = (df["regime_hat"].astype(str) == lab).astype(float).to_numpy()
    return x


def run_action_explanation() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    actions, audit = load_action_data()
    metric_rows = []
    importance_rows = []

    for (run_group, strategy), g in actions.groupby(["run_group", "strategy"], sort=True):
        train = g[g["split"] == "train"]
        test = g[g["split"] == "test"]
        if len(train) < 50 or len(test) < 20:
            continue
        for target in ["h", "m"]:
            y_train = train[target].astype(float)
            y_test = test[target].astype(float)
            fitted = {}
            for model_name, include_regime in [
                ("A_sigma_hat", False),
                ("B_sigma_hat_plus_regime", True),
            ]:
                x_train = action_design(train, include_regime)
                x_test = action_design(test, include_regime).reindex(columns=x_train.columns, fill_value=0.0)
                model = RandomForestRegressor(
                    n_estimators=80,
                    max_depth=5,
                    min_samples_leaf=20,
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                )
                model.fit(x_train, y_train)
                pred = model.predict(x_test)
                fitted[model_name] = (model, x_test)
                metric_rows.append(
                    {
                        "run_group": run_group,
                        "strategy": strategy,
                        "target": target,
                        "model": model_name,
                        "n_train": len(train),
                        "n_test": len(test),
                        "r2": r2_score(y_test, pred),
                        "mae": mean_absolute_error(y_test, pred),
                        "rmse": rmse(y_test.to_numpy(), pred),
                    }
                )

            model_b, x_test_b = fitted["B_sigma_hat_plus_regime"]
            perm = permutation_importance(
                model_b,
                x_test_b,
                y_test,
                scoring="r2",
                n_repeats=8,
                random_state=RANDOM_STATE,
                n_jobs=1,
            )
            for feature, imp_mean, imp_std in zip(x_test_b.columns, perm.importances_mean, perm.importances_std):
                importance_rows.append(
                    {
                        "run_group": run_group,
                        "strategy": strategy,
                        "target": target,
                        "feature": feature,
                        "permutation_importance_r2_mean": imp_mean,
                        "permutation_importance_r2_std": imp_std,
                    }
                )

    metrics = pd.DataFrame(metric_rows)
    imp = pd.DataFrame(importance_rows)
    metrics.to_csv(OUT / "action_model_metrics.csv", index=False)

    if not imp.empty:
        plot_action_importance(imp)

    write_action_summary(metrics, imp, actions, audit)
    return metrics, imp, audit


def plot_action_importance(imp: pd.DataFrame) -> None:
    agg = (
        imp.groupby(["target", "feature"], as_index=False)["permutation_importance_r2_mean"]
        .mean()
        .sort_values(["target", "feature"])
    )
    features = ["sigma_hat", "regime_L", "regime_M", "regime_H"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharex=False, constrained_layout=True)
    for ax, target in zip(axes, ["h", "m"]):
        sub = agg[agg["target"] == target].set_index("feature").reindex(features).fillna(0.0)
        vals = sub["permutation_importance_r2_mean"].to_numpy()
        colors = ["#1565C0" if f == "sigma_hat" else "#757575" for f in features]
        ax.barh(features, vals, color=colors)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_title(f"Target: {target}")
        ax.set_xlabel("Mean permutation importance (R2 drop)")
        ax.grid(axis="x", alpha=0.25)
    fig.suptitle("Action model feature importance, Model B")
    fig.savefig(OUT / "action_feature_importance.png", dpi=180)
    plt.close(fig)


def summarize_action_deltas(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, g in metrics.groupby(["run_group", "strategy", "target"], sort=True):
        a = g[g["model"] == "A_sigma_hat"]
        b = g[g["model"] == "B_sigma_hat_plus_regime"]
        if a.empty or b.empty:
            continue
        a = a.iloc[0]
        b = b.iloc[0]
        rows.append(
            {
                "run_group": keys[0],
                "strategy": keys[1],
                "target": keys[2],
                "r2_sigma_only": a["r2"],
                "r2_with_regime": b["r2"],
                "delta_r2": b["r2"] - a["r2"],
                "mae_sigma_only": a["mae"],
                "mae_with_regime": b["mae"],
                "delta_mae": b["mae"] - a["mae"],
            }
        )
    return pd.DataFrame(rows)


def write_action_summary(metrics: pd.DataFrame, imp: pd.DataFrame, actions: pd.DataFrame, audit: pd.DataFrame) -> None:
    deltas = summarize_action_deltas(metrics)
    accepted = audit[audit["status"] == "accepted"] if "status" in audit.columns else pd.DataFrame()
    mean_delta_h = float(deltas[deltas["target"] == "h"]["delta_r2"].mean()) if not deltas.empty else np.nan
    mean_delta_m = float(deltas[deltas["target"] == "m"]["delta_r2"].mean()) if not deltas.empty else np.nan
    mean_r2_a_h = float(deltas[deltas["target"] == "h"]["r2_sigma_only"].mean()) if not deltas.empty else np.nan
    mean_r2_a_m = float(deltas[deltas["target"] == "m"]["r2_sigma_only"].mean()) if not deltas.empty else np.nan

    if not imp.empty:
        imp_agg = imp.groupby("feature")["permutation_importance_r2_mean"].mean().sort_values(ascending=False)
        top_features = ", ".join([f"{k} ({v:.3f})" for k, v in imp_agg.head(3).items()])
    else:
        top_features = "not available"

    md = [
        "# PPO Action Explanation Test",
        "",
        "## Scope",
        "",
        (
            "This analysis uses frozen WP5 curve CSVs and joins `sigma_hat` only when the "
            "run-level frozen WP2 snapshot matches the curve regime sequence. This avoids "
            "regenerating synthetic paths and limits the action explanation test to aligned "
            "curve/snapshot pairs."
        ),
        "",
        "## Data",
        "",
        f"- Accepted aligned curve files: {len(accepted)}",
        f"- Action rows after cleaning: {len(actions):,}",
        "- Split: chronological 70/30 within each aligned run/seed/strategy curve.",
        "- Estimator: small random forest regressor.",
        "",
        "## Main Results",
        "",
        f"- Mean sigma-only R2 for `h`: {mean_r2_a_h:.3f}; mean delta from adding regime: {mean_delta_h:+.3f}.",
        f"- Mean sigma-only R2 for `m`: {mean_r2_a_m:.3f}; mean delta from adding regime: {mean_delta_m:+.3f}.",
        f"- Largest average Model B permutation features: {top_features}.",
        "",
        "## Interpretation",
        "",
        (
            "The action evidence is mixed. The simple sigma-only models explain some half-spread "
            "variation in selected aligned curves, but they do not explain skew reliably and they "
            "do not establish that PPO actions are largely determined by `sigma_hat` alone. The "
            "more stable finding is incremental: adding regime dummies after `sigma_hat` changes "
            "held-out action R2 only modestly in these aligned curve/snapshot pairs. Because this "
            "is a post-hoc approximation to trained PPO actions, it should not be described as a "
            "causal mechanism proof."
        ),
        "",
        "## Alignment Caveat",
        "",
        (
            "Only curves whose `regime_hat` sequence matched the frozen WP2 snapshot at "
            ">= 99.5% were used. Other curve files remain untouched but were excluded because "
            "their per-seed `sigma_hat` path is not present as a frozen curve-level column."
        ),
    ]
    (OUT / "action_explanation_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def load_strategy_means(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "strategy" not in df.columns or "sharpe_like" not in df.columns:
        return {}
    return df.groupby("strategy")["sharpe_like"].mean().to_dict()


def write_final_assessment(
    pred_metrics: pd.DataFrame,
    inc_metrics: pd.DataFrame,
    inc_comp: pd.DataFrame,
    action_metrics: pd.DataFrame,
    action_audit: pd.DataFrame,
    manifest: pd.DataFrame,
) -> None:
    pred_primary = pred_metrics[
        (pred_metrics["target_label"] == "regime_hat")
        & (pred_metrics["evaluation_mode"] == "within_source_calibrated")
    ].sort_values("balanced_accuracy", ascending=False).iloc[0]
    pred_pooled = pred_metrics[
        (pred_metrics["target_label"] == "regime_hat") & (pred_metrics["evaluation_mode"] == "pooled_global")
    ].sort_values("balanced_accuracy", ascending=False).iloc[0]
    inc_delta = inc_comp.iloc[0]
    action_deltas = summarize_action_deltas(action_metrics)
    h_delta = float(action_deltas[action_deltas["target"] == "h"]["delta_r2"].mean())
    m_delta = float(action_deltas[action_deltas["target"] == "m"]["delta_r2"].mean())
    h_r2 = float(action_deltas[action_deltas["target"] == "h"]["r2_sigma_only"].mean())
    m_r2 = float(action_deltas[action_deltas["target"] == "m"]["r2_sigma_only"].mean())

    wp5_main = load_strategy_means(ROOT / "results/runs/20260228-093733_seed1_wp5-eval-main_3e8eacc/metrics_wp5_oos.csv")
    wp5_ablation = load_strategy_means(
        ROOT / "results/runs/20260327-171914_seed1_wp5-ablation_e1545a5/metrics_wp5_oos_combined.csv"
    )
    wp5_misspec = load_strategy_means(
        ROOT / "results/runs/20260408-160248_seed1_w5-misspec-mild_5d9dc23/metrics_wp5_oos.csv"
    )

    wp6_summary_path = ROOT / "docs/internal/wp6_sweep_full/summary_condition_variant.csv"
    wp6_pair_path = ROOT / "docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv"
    wp6_text = "WP6 summary CSVs were not available."
    if wp6_summary_path.exists() and wp6_pair_path.exists():
        wp6 = pd.read_csv(wp6_summary_path)
        pair = pd.read_csv(wp6_pair_path)
        full_sigma = float(wp6[(wp6["condition"] == "full") & (wp6["variant"] == "sigma_only")]["mean"].iloc[0])
        full_combined = float(wp6[(wp6["condition"] == "full") & (wp6["variant"] == "combined")]["mean"].iloc[0])
        avg_pair_diff = float(pair["mean_diff"].mean())
        wp6_text = (
            f"WP6 full-condition means are sigma_only {full_sigma:.3f} and combined "
            f"{full_combined:.3f}; the mean paired combined-minus-sigma difference "
            f"across informative conditions is {avg_pair_diff:+.3f}."
        )

    accepted_actions = action_audit[action_audit["status"] == "accepted"] if "status" in action_audit.columns else []
    md = [
        "# Final Signal Redundancy Assessment",
        "",
        "## Bottom Line",
        "",
        (
            "The post-hoc diagnostics strengthen the cautious signal-redundancy interpretation, "
            "mainly through the classifier and incremental-prediction tests. In the tested "
            "synthetic setting, the observed categorical regime channel is highly predictable "
            "from source-calibrated `sigma_hat` and adds limited held-out predictive value for "
            "next-step absolute returns after `sigma_hat`. The action explanation test is more "
            "mixed: it does not show that `sigma_hat` alone explains PPO actions broadly, but it "
            "does show little additional explanatory gain from adding regime labels in the "
            "aligned frozen curves."
        ),
        "",
        "## Evidence Added Here",
        "",
        (
            f"- Classifier evidence: best within-source `regime_hat` from `sigma_hat` alone achieved "
            f"accuracy {pred_primary['accuracy']:.3f}, balanced accuracy "
            f"{pred_primary['balanced_accuracy']:.3f}, macro F1 {pred_primary['macro_f1']:.3f}, "
            f"and NMI {pred_primary['normalized_mutual_information']:.3f}. In the pooled-global "
            f"setting, the best balanced accuracy was {pred_pooled['balanced_accuracy']:.3f}."
        ),
        (
            f"- Incremental predictive value: adding `regime_hat` after `sigma_hat` changed "
            f"OOS R2 by {float(inc_delta['delta_oos_r2']):+.6f}, MAE by "
            f"{float(inc_delta['delta_mae']):+.6f}, and RMSE by "
            f"{float(inc_delta['delta_rmse']):+.6f} for next-step absolute mid return."
        ),
        (
            f"- Action explanation: across aligned frozen PPO curves, mean sigma-only R2 was "
            f"{h_r2:.3f} for `h` and {m_r2:.3f} for `m`; adding regime changed mean R2 by "
            f"{h_delta:+.3f} for `h` and {m_delta:+.3f} for `m`. This is weak evidence for "
            "sigma-only action explanation, but supportive evidence that the explicit label has "
            "limited incremental action-explanatory value in the aligned subset."
        ),
        "",
        "## Connection To Existing WP5/WP6 Evidence",
        "",
        (
            f"- WP5 main OOS means: ppo_aware {wp5_main.get('ppo_aware', np.nan):.3f}, "
            f"ppo_blind {wp5_main.get('ppo_blind', np.nan):.3f}."
        ),
        (
            f"- WP5 ablation means: sigma_only {wp5_ablation.get('ppo_sigma_only', np.nan):.3f}, "
            f"combined {wp5_ablation.get('ppo_combined', np.nan):.3f}, "
            f"regime_only {wp5_ablation.get('ppo_regime_only', np.nan):.3f}, "
            f"oracle_full {wp5_ablation.get('ppo_oracle_full', np.nan):.3f}."
        ),
        (
            f"- WP5 misspec mild means: sigma_only {wp5_misspec.get('ppo_sigma_only', np.nan):.3f}, "
            f"combined {wp5_misspec.get('ppo_combined', np.nan):.3f}, "
            f"regime_only {wp5_misspec.get('ppo_regime_only', np.nan):.3f}, "
            f"oracle_full {wp5_misspec.get('ppo_oracle_full', np.nan):.3f}."
        ),
        f"- {wp6_text}",
        "",
        "## Contradictory Or Limiting Evidence",
        "",
        (
            "The main contradictory note is the action test: sigma-only models do not explain "
            "PPO actions broadly, especially skew. This tempers any action-level mechanistic "
            "claim. The aligned action analysis is also limited to curve/snapshot pairs with "
            "exact frozen alignment, so it is best treated as supportive rather than exhaustive."
        ),
        "",
        "## Defense-Safe Interpretation",
        "",
        (
            "These results are consistent with the view that most policy-relevant and "
            "predictive structure conveyed by the observed categorical regime channel may "
            "already be embedded in `sigma_hat`. The action evidence should be framed more "
            "narrowly: explicit labels appear to add little after `sigma_hat` in the aligned "
            "post-hoc action regressions, but sigma-only action determination is not established. "
            "These diagnostics do not show that regime labels contain zero information, and they "
            "do not identify a causal PPO learning mechanism."
        ),
        "",
        "## Suggested Thesis Wording",
        "",
        (
            "In the tested synthetic setting, post-hoc diagnostics indicate that the observed "
            "categorical regime labels are highly recoverable from source-calibrated `sigma_hat` "
            "and add only limited held-out predictive value once `sigma_hat` is observed. In "
            "aligned post-hoc action regressions, explicit labels also provide little additional "
            "explanatory gain beyond `sigma_hat`, although the simple sigma-only action models do "
            "not fully explain PPO action variation. Together with the WP5/WP6 policy results, "
            "this supports the interpretation that most economically relevant regime structure "
            "available to the policies may already be embedded in the continuous volatility "
            "signal, while leaving open the possibility that explicit labels could matter in "
            "settings where `sigma_hat` is weaker, differently calibrated, or unavailable."
        ),
        "",
        "## Audit Notes",
        "",
        f"- Unique WP2 synthetic CSVs read: {len(manifest)}.",
        f"- Accepted aligned action curves: {len(accepted_actions)}.",
        "- No PPO model was retrained.",
        "- No WP5/WP6 experiment was rerun.",
        "- No protected CSV or protected figure artifact was modified.",
    ]
    (OUT / "final_signal_redundancy_assessment.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    panel, manifest = discover_wp2_sources()
    pred_metrics = run_predictability(panel, manifest)
    inc_metrics, inc_comp = run_incremental_value(panel)
    action_metrics, _action_imp, action_audit = run_action_explanation()
    write_final_assessment(pred_metrics, inc_metrics, inc_comp, action_metrics, action_audit, manifest)
    print(f"Wrote post-hoc signal analysis outputs to {OUT}")


if __name__ == "__main__":
    main()
