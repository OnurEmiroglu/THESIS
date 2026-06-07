"""Generate thesis_39.docx/pdf from the named final submission with cosmetic polish.

This documentation-only generator does not run experiments, regenerate
protected CSVs, or regenerate performance figures. It copies the named final
submission document (Onur_Emiroglu_MSc_Thesis.docx, whose content is thesis_38
plus the title-field fills and the Section 8.4 "Experiment 4:" clarification)
and applies only:

  (A) Section 8.2 / 8.3 heading "Experiment N:" prefixes (numbering consistency
      with the already-present 8.1/8.4/8.5 "Experiment N:" labels),
  (B) two title-page value-cell cleanups (Programme, Submission date), and
  (C) manuscript-version self-reference + provenance-chain updates (38 -> 39,
      source 37 -> 38; the frozen thesis_29 baseline is left untouched).

The base is Onur_Emiroglu_MSc_Thesis.docx (NOT the raw thesis_38.docx) because
that document already carries the Section 8.4 "Experiment 4:" prefix that must
remain in place. Figures, equations, frozen evidence, and Python logic are
unchanged.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "manuscript" / "Onur_Emiroglu_MSc_Thesis.docx"
DST = ROOT / "manuscript" / "thesis_39.docx"
PDF = ROOT / "manuscript" / "thesis_39.pdf"

PROTECTED_HASHES = {
    ROOT / "results" / "metrics_detector_compare.csv": "28E7AD40BB47214F8576132846E9E1D4CD643F623CF1187743091FC367A206ED",
    ROOT / "docs" / "internal" / "wp6_sweep_full" / "summary_condition_variant.csv": "6DD627E81637A49A60163F58AC1D3EF23B8D694E39AC55BA64FBF808E978C6EA",
    ROOT / "docs" / "internal" / "wp6_sweep_full" / "summary_paired_combined_vs_sigma.csv": "4BABCAAACE1DD5228C674E2CED9D977236F8D3ACB503C098FAEB06FF6C10B796",
    ROOT / "docs" / "internal" / "wp6_sweep_full" / "summary_paired_combined_vs_regime.csv": "2087FEFBE5DC39AF23372EA2D8999AC0F1071D0FEE90BC1B3668F2158130E8F9",
}

# (A) Section 8.2 / 8.3 heading prefixes. Matched on style == Heading 2 AND
# exact paragraph text, so body/caption occurrences of these phrases are safe.
HEADING_REPLACEMENTS = {
    "8.2 Five-Variant Ablation": "8.2 Experiment 2: Five-Variant Ablation",
    "8.3 Detector Robustness": "8.3 Experiment 3: Detector Robustness",
}

# Regression guard: these "Experiment N:" labels must remain present unchanged.
HEADINGS_PRESERVED = (
    "8.1 Experiment 1: Main Out-of-Sample Evaluation",
    "8.4 Experiment 4: Reward-Shaping and Misspecification Checks",
    "8.5 Experiment 5: Signal-Informativeness Sweep",
)

# (B) Title-page value cells, keyed by the row's label cell.
TITLE_CELL_REPLACEMENTS = {
    "Programme": ("Financial Engineering MSc Programme", "Financial Engineering MSc"),
    "Submission date": ("Submission: 2026-06-06", "2026-06-06"),
}

# (C) Version self-references + provenance chain (exact-string, same pattern as
# gen_thesis_38.py). thesis_38 -> thesis_39 for self-refs; in the provenance
# chain final 38 -> 39 and source 37 -> 38; the frozen thesis_29 baseline is
# never matched and therefore never changed.
VERSION_REPLACEMENTS = {
    "The final thesis_38 manuscript embeds existing figures": (
        "The final thesis_39 manuscript embeds existing figures"
    ),
    "The final thesis_38 manuscript reuses frozen performance results.": (
        "The final thesis_39 manuscript reuses frozen performance results."
    ),
    (
        "final manuscript manuscript/thesis_38.pdf and .docx; "
        "source manuscript manuscript/thesis_37.pdf and .docx"
    ): (
        "final manuscript manuscript/thesis_39.pdf and .docx; "
        "source manuscript manuscript/thesis_38.pdf and .docx"
    ),
    "thesis_38 finalization did not rerun experiments": (
        "thesis_39 finalization did not rerun experiments"
    ),
    "this final thesis_38 generation": "this final thesis_39 generation",
    "Status in thesis_38": "Status in thesis_39",
    (
        "thesis_38 is the final formatting-consistency pass built on thesis_37; "
        "frozen evidence remains unchanged."
    ): (
        "thesis_39 is the final formatting-consistency pass built on thesis_38; "
        "frozen evidence remains unchanged."
    ),
    "Documented validation; not rerun for thesis_38": (
        "Documented validation; not rerun for thesis_39"
    ),
}

# Regression guard: Section 9 equation strings must remain intact.
SECTION9_EQUATIONS = (
    "(16)   Sharpe-like = mean(ΔWₜ) / std(ΔWₜ) × √(1/Δt)",
    "(17)   inv_p99 = percentile₉₉(|qₜ|)",
    "(18)   fill_rate = filled quote opportunities / total quote opportunities",
    "(19)   t = mean(dᵢ) / (sd(dᵢ) / √n)",
)


def iter_all_paragraphs(doc: Document):
    for paragraph in doc.paragraphs:
        yield paragraph
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs
    for section in doc.sections:
        yield from section.header.paragraphs
        yield from section.footer.paragraphs


def has_drawing(paragraph) -> bool:
    return any(run._r.xpath(".//w:drawing") for run in paragraph.runs)


def set_paragraph_text(paragraph, text: str) -> None:
    """Replace a paragraph's text while preserving its first run's formatting."""
    if has_drawing(paragraph) or paragraph.text == text:
        return
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            if not run._r.xpath(".//w:drawing"):
                run.text = ""
    else:
        paragraph.add_run(text)


def apply_heading_prefixes(doc: Document) -> None:
    counts = {old: 0 for old in HEADING_REPLACEMENTS}
    for paragraph in doc.paragraphs:
        style = paragraph.style.name if paragraph.style else ""
        if "Heading" not in style:
            continue
        text = paragraph.text.strip()
        if text in HEADING_REPLACEMENTS:
            set_paragraph_text(paragraph, HEADING_REPLACEMENTS[text])
            counts[text] += 1
    bad = {old: n for old, n in counts.items() if n != 1}
    if bad:
        raise RuntimeError(f"Heading prefix targets not matched exactly once: {bad}")


def apply_title_cells(doc: Document) -> None:
    cover = doc.tables[0]
    found: set[str] = set()
    for row in cover.rows:
        if len(row.cells) < 2:
            continue
        label = row.cells[0].text.strip()
        if label not in TITLE_CELL_REPLACEMENTS:
            continue
        old, new = TITLE_CELL_REPLACEMENTS[label]
        value_cell = row.cells[1]
        if value_cell.text.strip() != old:
            raise RuntimeError(
                f"Title cell '{label}' value mismatch: {value_cell.text.strip()!r} != {old!r}"
            )
        set_paragraph_text(value_cell.paragraphs[0], new)
        for extra in value_cell.paragraphs[1:]:
            set_paragraph_text(extra, "")
        found.add(label)
    missing = set(TITLE_CELL_REPLACEMENTS) - found
    if missing:
        raise RuntimeError(f"Title-page labels not found: {sorted(missing)}")


def apply_version_references(doc: Document) -> None:
    for paragraph in iter_all_paragraphs(doc):
        if has_drawing(paragraph):
            continue
        new_text = paragraph.text
        for old, new in VERSION_REPLACEMENTS.items():
            new_text = new_text.replace(old, new)
        if new_text != paragraph.text:
            set_paragraph_text(paragraph, new_text)


def document_text(doc: Document) -> str:
    return "\n".join(p.text for p in iter_all_paragraphs(doc))


def heading_texts(doc: Document) -> list[str]:
    return [
        paragraph.text.strip()
        for paragraph in doc.paragraphs
        if paragraph.style and "Heading" in paragraph.style.name
    ]


def validate(doc: Document, expected_shapes: int) -> None:
    text = document_text(doc)

    # (A) headings present in their new form, exactly once; old form gone.
    # Checked against actual Heading paragraphs, NOT whole-document text: the TOC
    # field still caches the old heading strings until Word refreshes it during
    # PDF export, so a whole-document substring check would false-positive.
    headings = heading_texts(doc)
    for old, new in HEADING_REPLACEMENTS.items():
        if old in headings:
            raise RuntimeError(f"Old heading still present as a heading: {old!r}")
        if headings.count(new) != 1:
            raise RuntimeError(f"New heading not present exactly once: {new!r}")
    for preserved in HEADINGS_PRESERVED:
        if headings.count(preserved) != 1:
            raise RuntimeError(f"Preserved heading missing/duplicated: {preserved!r}")

    # (B) title-page values updated.
    cover = doc.tables[0]
    for row in cover.rows:
        if len(row.cells) < 2:
            continue
        label = row.cells[0].text.strip()
        if label in TITLE_CELL_REPLACEMENTS:
            _, new = TITLE_CELL_REPLACEMENTS[label]
            if row.cells[1].text.strip() != new:
                raise RuntimeError(
                    f"Title cell '{label}' not updated: {row.cells[1].text.strip()!r}"
                )

    # (C) version-string accounting: 8 self-refs -> thesis_39; provenance source
    # + built-on predecessor remain thesis_38 (2); no thesis_37; frozen thesis_29
    # untouched (2).
    counts = {
        "thesis_39": text.count("thesis_39"),
        "thesis_38": text.count("thesis_38"),
        "thesis_37": text.count("thesis_37"),
        "thesis_29": text.count("thesis_29"),
    }
    expected = {"thesis_39": 8, "thesis_38": 2, "thesis_37": 0, "thesis_29": 2}
    if counts != expected:
        raise RuntimeError(f"Version-string accounting mismatch: {counts} != {expected}")

    # Section 9 equations intact.
    for eq in SECTION9_EQUATIONS:
        if eq not in text:
            raise RuntimeError(f"Section 9 equation altered/missing: {eq!r}")

    if len(doc.inline_shapes) != expected_shapes:
        raise RuntimeError(
            f"Inline shape count changed: {expected_shapes} -> {len(doc.inline_shapes)}"
        )


def media_hashes(path: Path) -> dict[str, str]:
    with ZipFile(path) as archive:
        return {
            name: hashlib.sha256(archive.read(name)).hexdigest().upper()
            for name in archive.namelist()
            if name.startswith("word/media/")
        }


def verify_protected_hashes() -> None:
    matches = 0
    for path, expected in PROTECTED_HASHES.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        if actual != expected:
            raise RuntimeError(
                f"Protected artifact hash mismatch: {path.relative_to(ROOT)}"
            )
        matches += 1
    print(f"Protected CSV hashes: {matches}/{len(PROTECTED_HASHES)} MATCH")


def export_pdf_with_word() -> None:
    tmp_pdf = PDF.with_name(PDF.stem + "_export_tmp.pdf")
    ps = (
        "$ErrorActionPreference = 'Stop'; "
        f"$tmp = '{str(tmp_pdf)}'; "
        "if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }; "
        "$word = New-Object -ComObject Word.Application; "
        "$word.Visible = $false; "
        "try { "
        f"$doc = $word.Documents.Open('{str(DST)}', $false, $false); "
        "$doc.Fields.Update() | Out-Null; "
        "foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }; "
        "$doc.Save(); "
        "$doc.ExportAsFixedFormat($tmp, 17); "
        "$doc.Close($false); "
        "} finally { $word.Quit() }; "
        f"Move-Item -LiteralPath $tmp -Destination '{str(PDF)}' -Force"
    )
    subprocess.run(
        ["powershell", "-Command", ps],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> int:
    if not SRC.exists():
        raise FileNotFoundError(SRC)
    verify_protected_hashes()
    source_media = media_hashes(SRC)
    shutil.copy2(SRC, DST)

    doc = Document(DST)
    before_shapes = len(doc.inline_shapes)
    apply_heading_prefixes(doc)
    apply_title_cells(doc)
    apply_version_references(doc)

    validate(doc, before_shapes)
    doc.save(DST)

    if media_hashes(DST) != source_media:
        raise RuntimeError("Embedded media changed relative to the base document.")

    print(f"Wrote {DST.relative_to(ROOT)}")
    print(f"Preserved inline_shapes: {before_shapes}")

    if sys.platform.startswith("win"):
        export_pdf_with_word()
        print(f"Wrote {PDF.relative_to(ROOT)}")
    else:
        print("PDF export skipped: Microsoft Word automation requires Windows.")

    verify_protected_hashes()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
