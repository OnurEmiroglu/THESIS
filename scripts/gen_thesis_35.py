"""Generate thesis_35.docx/pdf from thesis_34 with format-guide polish.

This is a documentation-only generator. It does not run PPO, WP5, WP6,
detector robustness, ablations, misspecification checks, signal-informativeness
sweeps, protected CSV generation, or protected performance-figure generation.
It copies thesis_34 and applies only final submission structure/formatting
changes while preserving figures, formulas, numerical claims, and evidence.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "manuscript" / "thesis_34.docx"
DST = ROOT / "manuscript" / "thesis_35.docx"
PDF = ROOT / "manuscript" / "thesis_35.pdf"


MAIN_SECTIONS = [
    "Abstract",
    "Symbols, Abbreviations, and Glossary",
    "1 Introduction",
    "2 Mathematical Formulation",
    "3 Use-Case Scenario",
    "4 System Architecture",
    "5 Layered Experimental Model",
    "6 Algorithm Specification and Pseudocode",
    "7 Experimental Setup",
    "8 Results and Visualisation",
    "9 Evaluation Metrics",
    "10 Discussion",
    "11 Reproducibility Checklist",
    "12 Conclusion",
    "References",
    "Appendix A Code Appendix",
    "Appendix B Unit Tests and Validation Checks",
    "Appendix C Extended Evidence Tables",
    "Appendix D Author Contribution Statement",
]

TABLE_CAPTIONS = {
    4: "Table 3.1 Strategy variants",
    5: "Table 6.1 Reference implementation map",
    6: "Table 7.1 Detector variants",
    7: "Table 7.2 PPO hyperparameters",
    8: "Table 8.1 Main OOS strategy metrics",
    9: "Table 8.2 Five-variant ablation metrics",
    10: "Table 8.3 Compact statistical summary",
    11: "Table 8.4 Detector robustness summary",
    12: "Table 8.5 Signal information-value sweep",
    13: "Table 10.1 Risks to interpretation",
    14: "Table 11.1 Reproducibility checklist",
    15: "Table 11.2 Protected artifact hash checks",
    16: "Table 11.3 Reproducibility commands",
    17: "Appendix Table A.1 Code map",
    18: "Appendix Table B.1 Unit test and validation checklist",
    19: "Appendix Table C.1 Supporting diagnostics",
}

ALGORITHMS = [
    ("6.2 Synthetic Market and Regime Generation", "Algorithm 1: Synthetic market and regime generation"),
    ("6.3 Market-Making Environment Step", "Algorithm 2: Market-making environment step"),
    ("6.4 PPO Training and OOS Evaluation Protocol", "Algorithm 3: PPO training and OOS evaluation protocol"),
    ("6.5 Experiment 5: Signal-Informativeness Sweep", "Algorithm 4: Signal information-value sweep"),
]


def iter_all_paragraphs(doc: Document):
    paragraphs = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                paragraphs.extend(cell.paragraphs)
    for section in doc.sections:
        paragraphs.extend(section.header.paragraphs)
        paragraphs.extend(section.footer.paragraphs)
    return paragraphs


def has_drawing(paragraph) -> bool:
    return any(run._r.xpath(".//w:drawing") for run in paragraph.runs)


def safe_set_paragraph_text(paragraph, text: str) -> None:
    """Replace paragraph text only when the paragraph has no drawing runs."""
    if has_drawing(paragraph):
        return
    if paragraph.text == text:
        return
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            if not run._r.xpath(".//w:drawing"):
                run.text = ""
    else:
        paragraph.add_run(text)


def find_paragraph(doc: Document, exact_text: str):
    for paragraph in doc.paragraphs:
        if paragraph.text.strip() == exact_text:
            return paragraph
    raise RuntimeError(f"Could not find paragraph: {exact_text}")


def add_paragraph_before_element(doc: Document, element, text: str = "", style: str | None = None):
    paragraph = doc.add_paragraph(text, style=style)
    element.addprevious(paragraph._p)
    return paragraph


def insert_paragraph_after(anchor, text: str = "", style: str | None = None):
    paragraph = anchor._parent.add_paragraph(text, style=style)
    anchor._p.addnext(paragraph._p)
    return paragraph


def delete_paragraph(paragraph) -> None:
    paragraph._element.getparent().remove(paragraph._element)
    paragraph._p = paragraph._element = None


def style_caption(paragraph) -> None:
    paragraph.style = "Caption" if "Caption" in [s.name for s in paragraph.part.document.styles] else paragraph.style
    if paragraph.runs:
        paragraph.runs[0].bold = True
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(3)


def style_code(paragraph) -> None:
    for run in paragraph.runs:
        run.font.name = "Consolas"
        run.font.size = Pt(9)
    paragraph.paragraph_format.left_indent = Pt(18)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)


def add_toc_field(paragraph) -> None:
    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_char)

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    run._r.append(instr)

    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "separate")
    run._r.append(fld_char)

    paragraph.add_run("Right-click and update field if page numbers are not refreshed.")

    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char)


def ensure_cover_row(table, label: str, value: str) -> None:
    for row in table.rows:
        if row.cells[0].text.strip() == label:
            row.cells[1].text = value
            return
    row = table.add_row()
    row.cells[0].text = label
    row.cells[1].text = value


def update_title_page(doc: Document) -> list[str]:
    cover = doc.tables[0]
    placeholders = []
    known = {
        "Author": "Onur Emiroglu",
        "Programme": "Financial Engineering MSc Programme",
        "Institution": "Karlsruhe Institute of Technology",
        "Course / Module": "[Course / module to be inserted]",
        "Supervisor": "[Supervisor to be inserted]",
        "Advisor / Co-supervisor": "[Advisor / co-supervisor to be inserted, if applicable]",
        "Matriculation No.": "[Matriculation number to be inserted]",
        "Submission / Draft date": "June 2026",
        "Git Repository": "[Repository URL to be inserted]",
        "Current draft": "manuscript/thesis_35.pdf / .docx",
        "Frozen baseline": "manuscript/thesis_29.pdf, tag thesis-v29-frozen",
        "Decision log": "manuscript/decisions_log_13.pdf",
    }
    for label, value in known.items():
        ensure_cover_row(cover, label, value)
        if value.startswith("["):
            placeholders.append(label)
    ensure_cover_row(cover, "Previous source draft", "manuscript/thesis_34.pdf / .docx")
    for paragraph in doc.paragraphs:
        if "thesis_34" in paragraph.text and "documentation" in paragraph.text:
            safe_set_paragraph_text(
                paragraph,
                "Draft integrity note: thesis_35 is a final Student Report Format Guide compliance pass. "
                "Frozen experimental evidence is reused and not regenerated.",
            )
    return placeholders


def insert_table_of_contents(doc: Document) -> None:
    abstract = find_paragraph(doc, "Abstract")
    paragraphs = list(doc.paragraphs)
    abstract_idx = next(i for i, paragraph in enumerate(paragraphs) if paragraph._p is abstract._p)
    if abstract_idx > 0:
        previous = paragraphs[abstract_idx - 1]
        if not previous.text.strip() and previous._p.xpath(".//w:br"):
            delete_paragraph(previous)
    heading = add_paragraph_before_element(doc, abstract._p, "Contents")
    if heading.runs:
        heading.runs[0].bold = True
        heading.runs[0].font.size = Pt(16)
    toc = add_paragraph_before_element(doc, abstract._p)
    add_toc_field(toc)
    spacer = add_paragraph_before_element(doc, abstract._p)
    spacer.add_run().add_break(WD_BREAK.PAGE)
    heading.paragraph_format.keep_with_next = True


def add_table_captions(doc: Document) -> None:
    for index, caption in sorted(TABLE_CAPTIONS.items(), reverse=True):
        paragraph = add_paragraph_before_element(doc, doc.tables[index]._tbl, caption)
        style_caption(paragraph)


def add_algorithm_blocks(doc: Document) -> None:
    for heading_text, caption_text in reversed(ALGORITHMS):
        heading = find_paragraph(doc, heading_text)
        caption = insert_paragraph_after(heading, caption_text)
        style_caption(caption)
    in_algorithm = False
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("Algorithm "):
            in_algorithm = True
            continue
        if re.match(r"^6\.\d", text):
            in_algorithm = False
        if in_algorithm and text and not re.match(r"^6\.\d", text):
            style_code(paragraph)


def add_hyperparameter_protocol(doc: Document) -> None:
    heading = find_paragraph(doc, "7.6 PPO Hyperparameters")
    paragraphs = [
        "7.6.1 Hyperparameter Selection Protocol",
        "The thesis does not perform a broad hyperparameter optimization campaign. This is intentional because the central comparison is signal-channel design, not PPO tuning.",
        "PPO hyperparameters are held fixed across PPO variants to avoid giving one information condition a tuning advantage.",
        "eta = 0.001 is the canonical inventory-penalty scale selected after the earlier inventory-penalty ablation.",
        "No separate validation set is introduced because the study uses a fixed train/OOS evaluation protocol; this should be treated as a limitation and a future extension if full tuning is pursued.",
        "This is a methodological choice, not a claim that the PPO settings are globally optimal.",
    ]
    anchor = heading
    for text in paragraphs:
        style = "Heading 2" if text.startswith("7.6.1") else None
        anchor = insert_paragraph_after(anchor, text, style=style)


def remove_duplicate_hyperparameter_paragraph(doc: Document) -> None:
    old_prefix = "The PPO hyperparameters are held fixed across PPO variants to keep the signal-channel comparison fair."
    for paragraph in list(doc.paragraphs):
        if paragraph.text.strip().startswith(old_prefix):
            delete_paragraph(paragraph)
            return


def strengthen_reproducibility(doc: Document) -> None:
    heading = find_paragraph(doc, "11 Reproducibility Checklist")
    paragraphs = [
        "The reproducibility path uses a local Python virtual environment created with python -m venv .venv and dependencies installed from requirements.txt.",
        "Main commands are documented in Table 11.3. Exact reproducibility depends on using the project repository, config snapshots, fixed seeds, logged run metadata, and the protected evidence files recorded in EVIDENCE_MANIFEST.md.",
        "Protected evidence is checked by SHA256. No Dockerfile or environment.yml is present, so this report does not claim Docker or Conda reproducibility.",
        "No external CI service is claimed; validation is documented through local reproducibility checks and protected evidence hashes.",
        "Formal line-coverage percentage is not claimed; the tests are targeted regression and reproducibility checks.",
    ]
    anchor = heading
    for text in paragraphs:
        anchor = insert_paragraph_after(anchor, text)


def expand_appendix_b(doc: Document) -> None:
    heading = find_paragraph(doc, "Appendix B Sanity Checks and Unit Tests")
    safe_set_paragraph_text(heading, "Appendix B Unit Tests and Validation Checks")
    appendix_c = find_paragraph(doc, "Appendix C Extended Evidence Tables")
    paragraphs = [
        "How to run tests: pytest -q; pytest tests/test_csv_metric_logger.py -q; pytest tests/test_resume_validation.py -q; python run.py --config config/w3_sanity.json.",
        "Test categories include CSV metric logger schema stability, resume-mode config validation, WP3 environment sanity checks, figure/path existence checks, forbidden phrase or overclaim scans, and protected evidence SHA256 checks.",
        "Pass/fail criteria: all pytest tests pass; generated artifacts exist and are non-empty; protected CSV hashes match EVIDENCE_MANIFEST.md; no forbidden overclaim phrases are detected; no experiment reruns are required for document generation.",
        "Formal line-coverage percentage is not claimed; the tests are targeted regression and reproducibility checks.",
        "No external CI service is claimed; validation is documented through local reproducibility checks and protected evidence hashes.",
    ]
    for text in reversed(paragraphs):
        add_paragraph_before_element(doc, appendix_c._p, text)


def add_appendix_d(doc: Document) -> None:
    heading = doc.add_paragraph("Appendix D Author Contribution Statement", style="Heading 1")
    heading.paragraph_format.page_break_before = True
    doc.add_paragraph(
        "This thesis is submitted as a single-author MSc thesis by Onur Emiroglu. The reported implementation, "
        "experiments, documentation, and interpretation are organized in the project repository and were prepared "
        "under normal thesis supervision. Supervisory feedback is reflected in the final framing and limitations, "
        "but no multi-author contribution matrix is required."
    )


def update_thesis35_labels(doc: Document) -> None:
    replacements = {
        "Status in thesis_34": "Status in thesis_35",
        "thesis_34 is a defense-clarity polish draft built on thesis_33; frozen evidence remains unchanged.": (
            "thesis_35 is a final format-guide compliance polish draft built on thesis_34; frozen evidence remains unchanged."
        ),
        "The thesis_34 adaptation reuses frozen performance results.": (
            "The thesis_35 adaptation reuses frozen performance results."
        ),
        "the thesis_34 adaptation embeds existing figures": (
            "the thesis_35 adaptation embeds existing figures"
        ),
        "These commands document reproducibility paths only; thesis_34 adaptation did not rerun experiments.": (
            "These commands document reproducibility paths only; thesis_35 adaptation did not rerun experiments."
        ),
        "Ensures thesis_34 references existing frozen figure files.": (
            "Ensures thesis_35 references existing frozen figure files."
        ),
    }
    targets = list(doc.paragraphs)
    for table in doc.tables[1:]:
        for row in table.rows:
            for cell in row.cells:
                targets.extend(cell.paragraphs)
    for paragraph in targets:
        if has_drawing(paragraph):
            continue
        text = paragraph.text
        new_text = text
        for old, new in replacements.items():
            new_text = new_text.replace(old, new)
        if new_text != text:
            safe_set_paragraph_text(paragraph, new_text)


def round_ablation_table(doc: Document) -> None:
    table = doc.tables[9]
    for row in table.rows[1:]:
        for cell in row.cells[2:]:
            text = cell.text.strip()
            if re.fullmatch(r"-?\d+\.\d{4,}", text):
                cell.text = f"{float(text):.3f}"


def update_pdf_export_fields_with_word() -> None:
    tmp_pdf = PDF.with_name(PDF.stem + "_export_tmp.pdf")
    if tmp_pdf.exists():
        tmp_pdf.unlink()
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
    subprocess.run(["powershell", "-Command", ps], cwd=str(ROOT), check=True, capture_output=True, text=True)


def export_pdf() -> bool:
    if sys.platform.startswith("win"):
        try:
            update_pdf_export_fields_with_word()
            return True
        except Exception as err:
            print(f"Microsoft Word PDF export failed: {err}")
    return False


def main() -> int:
    if not SRC.exists():
        raise FileNotFoundError(SRC)
    shutil.copy2(SRC, DST)
    doc = Document(DST)
    before_shapes = len(doc.inline_shapes)

    placeholders = update_title_page(doc)
    insert_table_of_contents(doc)
    add_table_captions(doc)
    add_algorithm_blocks(doc)
    add_hyperparameter_protocol(doc)
    remove_duplicate_hyperparameter_paragraph(doc)
    strengthen_reproducibility(doc)
    expand_appendix_b(doc)
    add_appendix_d(doc)
    update_thesis35_labels(doc)
    round_ablation_table(doc)

    after_shapes = len(doc.inline_shapes)
    if after_shapes != before_shapes:
        raise RuntimeError(f"Figure preservation failed: inline_shapes {before_shapes} -> {after_shapes}")
    doc.save(DST)
    print(f"Wrote {DST.relative_to(ROOT)}")
    print(f"Preserved inline_shapes: {after_shapes}")
    print("Placeholders requiring user input: " + ", ".join(placeholders))

    if export_pdf():
        print(f"Wrote {PDF.relative_to(ROOT)}")
    else:
        print(f"PDF export failed; DOCX remains available at {DST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
