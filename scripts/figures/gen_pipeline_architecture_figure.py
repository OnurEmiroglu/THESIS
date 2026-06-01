"""Generate a methodology-only pipeline architecture figure for thesis_33.

This script does not run PPO training, OOS evaluation, detector robustness,
ablations, WP6 sweeps, or any protected evidence pipeline. It creates a static
illustration of the documentation pipeline only.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "plots" / "thesis_33"
PNG = OUT_DIR / "fig_pipeline_architecture.png"
PDF = OUT_DIR / "fig_pipeline_architecture.pdf"
META = OUT_DIR / "fig_pipeline_architecture_metadata.json"


WIDTH = 2200
HEIGHT = 640


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


TITLE_FONT = load_font(42, bold=True)
BOX_TITLE_FONT = load_font(26, bold=True)
BODY_FONT = load_font(22)
FOOT_FONT = load_font(21)


def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def center_text(draw: ImageDraw.ImageDraw, xy, text: str, font, fill: str, line_spacing: int = 8) -> None:
    x, y = xy
    lines = text.split("\n")
    heights = [text_size(draw, line, font)[1] for line in lines]
    total_h = sum(heights) + line_spacing * (len(lines) - 1)
    current_y = y - total_h / 2
    for line, h in zip(lines, heights):
        w, _ = text_size(draw, line, font)
        draw.text((x - w / 2, current_y), line, font=font, fill=fill)
        current_y += h + line_spacing


def add_box(draw: ImageDraw.ImageDraw, xy, width, height, title, body, facecolor, edgecolor):
    x, y = xy
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=22,
        fill=facecolor,
        outline=edgecolor,
        width=4,
    )
    center_text(draw, (x + width / 2, y + height * 0.32), title, BOX_TITLE_FONT, "#1f2933")
    center_text(draw, (x + width / 2, y + height * 0.63), body, BODY_FONT, "#334155", line_spacing=10)


def add_arrow(draw: ImageDraw.ImageDraw, start, end):
    draw.line((start[0], start[1], end[0] - 12, end[1]), fill="#475569", width=5)
    x, y = end
    draw.polygon([(x, y), (x - 24, y - 14), (x - 24, y + 14)], fill="#475569")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    boxes = [
        ((70, 190), 340, 230, "Synthetic path", "Markov regimes\nmid-price process", "#e8f3ef", "#2f855a"),
        ((500, 190), 355, 230, "Signals", "rolling sigma_hat\nregime_hat labels", "#eef2ff", "#4f46e5"),
        ((945, 190), 360, 230, "Gym environment", "inventory, time\nquotes, fills, reward", "#fff7ed", "#d97706"),
        ((1395, 190), 310, 230, "Policies", "PPO variants\nbaselines", "#fdf2f8", "#be185d"),
        ((1795, 190), 335, 230, "OOS metrics", "equity, Sharpe-like\ninventory, fills", "#f1f5f9", "#334155"),
    ]

    for args in boxes:
        add_box(draw, *args)

    add_arrow(draw, (420, 305), (490, 305))
    add_arrow(draw, (865, 305), (935, 305))
    add_arrow(draw, (1315, 305), (1385, 305))
    add_arrow(draw, (1715, 305), (1785, 305))

    center_text(
        draw,
        (WIDTH / 2, 80),
        "Controlled HFMM evaluation pipeline",
        TITLE_FONT,
        "#111827",
    )
    center_text(
        draw,
        (WIDTH / 2, 535),
        "Methodology illustration only; no performance evidence or protected experiment output is regenerated.",
        FOOT_FONT,
        "#475569",
    )

    image.save(PNG)
    image.save(PDF, "PDF", resolution=220.0)

    META.write_text(
        json.dumps(
            {
                "artifact": "fig_pipeline_architecture",
                "purpose": "methodology illustration only",
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "no_rerun_statement": (
                    "This script does not run PPO, WP5, WP6, detector robustness, "
                    "ablations, misspecification, or protected evidence pipelines."
                ),
                "outputs": [str(PNG.relative_to(ROOT)), str(PDF.relative_to(ROOT))],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {PNG.relative_to(ROOT)}")
    print(f"Wrote {PDF.relative_to(ROOT)}")
    print(f"Wrote {META.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
