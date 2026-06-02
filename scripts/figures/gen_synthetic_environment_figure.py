"""Generate an illustrative synthetic HFMM environment methodology figure.

This script is documentation-only. It reuses the WP2 synthetic-regime helper
functions but does not run PPO, WP5, WP6, or any performance experiment.
The figure is rendered with Pillow so it can be produced without installing
additional plotting software.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "w5_main.json"
OUT_DIR = ROOT / "results" / "plots" / "thesis_32"
PNG_PATH = OUT_DIR / "fig_synthetic_environment.png"
PDF_PATH = OUT_DIR / "fig_synthetic_environment.pdf"
META_PATH = OUT_DIR / "fig_synthetic_environment_metadata.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.wp2.synth_regime import (  # noqa: E402
    REGIME_LABELS,
    compute_rolling_rv,
    generate_mid_series,
    generate_regime_series,
)


WIDTH = 2200
HEIGHT = 1500
LEFT = 170
RIGHT = 2120
PANEL_TOPS = [170, 610, 1005]
PANEL_HEIGHTS = [320, 285, 245]
REGIME_COLORS = {
    0: (143, 185, 232, 35),
    1: (185, 221, 178, 35),
    2: (240, 179, 126, 35),
}


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def contiguous_runs(values: np.ndarray) -> list[tuple[int, int, int]]:
    runs: list[tuple[int, int, int]] = []
    start = 0
    current = int(values[0])
    for i, value in enumerate(values[1:], start=1):
        value = int(value)
        if value != current:
            runs.append((start, i, current))
            start = i
            current = value
    runs.append((start, len(values), current))
    return runs


def x_to_px(x: float, n_max: int) -> float:
    return LEFT + (float(x) / float(n_max)) * (RIGHT - LEFT)


def y_to_px(y: float, y_min: float, y_max: float, top: int, height: int) -> float:
    if y_max <= y_min:
        return top + height / 2
    pad = 0.08 * (y_max - y_min)
    y_min -= pad
    y_max += pad
    return top + height - ((float(y) - y_min) / (y_max - y_min)) * height


def draw_dashed_line(draw: ImageDraw.ImageDraw, xy: tuple[float, float, float, float], fill, width=3, dash=12) -> None:
    x1, y1, x2, y2 = xy
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    dx = (x2 - x1) / length
    dy = (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        if int(pos / dash) % 2 == 0:
            draw.line((x1 + dx * pos, y1 + dy * pos, x1 + dx * end, y1 + dy * end), fill=fill, width=width)
        pos += dash


def draw_panel_frame(draw: ImageDraw.ImageDraw, top: int, height: int, title: str, y_label: str) -> None:
    draw.rectangle((LEFT, top, RIGHT, top + height), outline=(170, 170, 170), width=2)
    for frac in [0.25, 0.5, 0.75]:
        y = top + height * frac
        draw.line((LEFT, y, RIGHT, y), fill=(218, 218, 218), width=1)
    for frac in [0.25, 0.5, 0.75]:
        x = LEFT + (RIGHT - LEFT) * frac
        draw.line((x, top, x, top + height), fill=(226, 226, 226), width=1)
    draw.text((LEFT, top - 38), title, fill=(31, 77, 120), font=font(27, bold=True))
    if y_label != "Regime":
        draw.text((32, top + height / 2 - 15), y_label, fill=(70, 70, 70), font=font(24))


def draw_regime_shading(base: Image.Image, regimes: np.ndarray, top: int, height: int) -> None:
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    odraw = ImageDraw.Draw(overlay)
    n_max = len(regimes) - 1
    for start, end, state in contiguous_runs(regimes):
        x0 = x_to_px(start, n_max)
        x1 = x_to_px(end, n_max)
        odraw.rectangle((x0, top, x1, top + height), fill=REGIME_COLORS[state])
    base.alpha_composite(overlay)


def draw_series(
    draw: ImageDraw.ImageDraw,
    values: np.ndarray,
    top: int,
    height: int,
    color: tuple[int, int, int],
    width: int,
    y_min: float | None = None,
    y_max: float | None = None,
) -> None:
    n_max = len(values) - 1
    finite = values[np.isfinite(values)]
    if y_min is None:
        y_min = float(np.min(finite))
    if y_max is None:
        y_max = float(np.max(finite))
    points: list[tuple[float, float]] = []
    for i, value in enumerate(values):
        if not np.isfinite(value):
            if len(points) > 1:
                draw.line(points, fill=color, width=width, joint="curve")
            points = []
            continue
        points.append((x_to_px(i, n_max), y_to_px(float(value), y_min, y_max, top, height)))
    if len(points) > 1:
        draw.line(points, fill=color, width=width, joint="curve")


def draw_step_regime(draw: ImageDraw.ImageDraw, regimes: np.ndarray, top: int, height: int) -> None:
    n_max = len(regimes) - 1
    points: list[tuple[float, float]] = []
    for i, value in enumerate(regimes):
        x = x_to_px(i, n_max)
        y = y_to_px(float(value), -0.2, 2.2, top, height)
        if points:
            points.append((x, points[-1][1]))
        points.append((x, y))
    draw.line(points, fill=(35, 35, 35), width=4)
    for state, label in enumerate(["Low", "Medium", "High"]):
        y = y_to_px(float(state), -0.2, 2.2, top, height)
        draw.text((90, y - 13), label, fill=(70, 70, 70), font=font(22))


def main() -> None:
    cfg = load_config()
    seed = int(cfg.get("seed", 1))
    n_steps = int(cfg["episode"]["n_steps"])
    train_frac = float(cfg["wp5"]["train_frac"])
    train_split = int(n_steps * train_frac)
    rv_window = int(cfg["regime"]["rv_window"])
    warmup_steps = int(cfg["regime"]["warmup_steps"])
    tick_size = float(cfg["market"]["tick_size"])
    sigma_base = float(cfg["regime"]["sigma_mid_ticks_base"])
    sigma_mult = [float(x) for x in cfg["regime"]["sigma_mult"]]

    rng = np.random.default_rng(seed)
    regime_true = generate_regime_series(n_steps, seed=seed, cfg=cfg, rng=rng)
    mid, _ret = generate_mid_series(regime_true, cfg, rng)
    _rv, sigma_hat = compute_rolling_rv(mid, rv_window, tick_size)

    regime_full = np.concatenate([[regime_true[0]], regime_true])
    sigma_levels = np.array([sigma_base * sigma_mult[int(s)] for s in regime_full])
    n_max = len(mid) - 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    draw.text((LEFT, 45), "Illustrative synthetic HFMM environment path", fill=(11, 37, 69), font=font(40, bold=True))
    draw.text(
        (LEFT, 96),
        "Methodology illustration only: canonical synthetic-environment parameters, not a performance experiment.",
        fill=(85, 85, 85),
        font=font(23),
    )

    titles = [
        "Synthetic mid-price path",
        "Rolling realized-volatility signal and true regime volatility",
        "Latent Markov volatility-regime sequence",
    ]
    labels = ["Mid-price", "Volatility", "Regime"]
    for top, height, title, label in zip(PANEL_TOPS, PANEL_HEIGHTS, titles, labels):
        draw_regime_shading(image, regime_full, top, height)
        draw_panel_frame(draw, top, height, title, label)
        x_split = x_to_px(train_split, n_max)
        draw_dashed_line(draw, (x_split, top, x_split, top + height), fill=(45, 45, 45), width=3)

    draw_series(draw, mid, PANEL_TOPS[0], PANEL_HEIGHTS[0], color=(31, 77, 120), width=4)
    y_min = float(np.nanmin(sigma_hat))
    y_max = float(max(np.nanmax(sigma_hat), np.max(sigma_levels)))
    draw_series(draw, sigma_hat, PANEL_TOPS[1], PANEL_HEIGHTS[1], color=(46, 116, 181), width=4, y_min=y_min, y_max=y_max)
    draw_series(draw, sigma_levels, PANEL_TOPS[1], PANEL_HEIGHTS[1], color=(155, 28, 28), width=3, y_min=y_min, y_max=y_max)
    draw_step_regime(draw, regime_full, PANEL_TOPS[2], PANEL_HEIGHTS[2])

    x_split = x_to_px(train_split, n_max)
    draw.text((x_split + 12, PANEL_TOPS[0] + 12), "70/30 train-test split", fill=(45, 45, 45), font=font(22))
    draw.rectangle((LEFT, PANEL_TOPS[1], x_to_px(warmup_steps, n_max), PANEL_TOPS[1] + PANEL_HEIGHTS[1]), outline=(110, 110, 110), width=1)
    draw.text((LEFT + 10, PANEL_TOPS[1] + 10), "warmup", fill=(80, 80, 80), font=font(20))

    legend_y = 1320
    legend_items = [
        ((143, 185, 232), "Low regime"),
        ((185, 221, 178), "Medium regime"),
        ((240, 179, 126), "High regime"),
        ((31, 77, 120), "Mid / sigma_hat"),
        ((155, 28, 28), "True volatility"),
        ((45, 45, 45), "Train-test split"),
    ]
    x_cursor = LEFT
    for color, label in legend_items:
        draw.rectangle((x_cursor, legend_y, x_cursor + 36, legend_y + 18), fill=color)
        draw.text((x_cursor + 46, legend_y - 4), label, fill=(50, 50, 50), font=font(20))
        x_cursor += 285

    draw.text((LEFT, 1415), "Simulation step", fill=(70, 70, 70), font=font(23))
    for tick in [0, 2000, 4000, 6000, 8000]:
        x = x_to_px(tick, n_max)
        draw.text((x - 35, 1375), str(tick), fill=(70, 70, 70), font=font(19))

    image_rgb = image.convert("RGB")
    image_rgb.save(PNG_PATH, "PNG")
    image_rgb.save(PDF_PATH, "PDF", resolution=220)

    metadata = {
        "script_name": "scripts/figures/gen_synthetic_environment_figure.py",
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "config_source_path": str(CONFIG_PATH.relative_to(ROOT)),
        "parameters": {
            "mid0": cfg["market"]["mid0"],
            "tick_size": cfg["market"]["tick_size"],
            "dt": cfg["market"]["dt"],
            "n_steps": n_steps,
            "train_test_split": train_frac,
            "train_split_step": train_split,
            "rv_window": rv_window,
            "warmup_steps": warmup_steps,
            "sigma_mid_ticks_base": sigma_base,
            "sigma_mult": sigma_mult,
            "trans_matrix": cfg["regime"]["trans_matrix"],
            "regime_labels": REGIME_LABELS,
        },
        "note": "Illustrative methodology figure only; not a new performance experiment.",
        "outputs": {
            "png": str(PNG_PATH.relative_to(ROOT)),
            "pdf": str(PDF_PATH.relative_to(ROOT)),
            "metadata": str(META_PATH.relative_to(ROOT)),
        },
    }
    META_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote {PNG_PATH.relative_to(ROOT)}")
    print(f"Wrote {PDF_PATH.relative_to(ROOT)}")
    print(f"Wrote {META_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
