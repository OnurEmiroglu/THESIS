# HECTOR Figure/Table Explanation Audit - v4

Date: 2026-06-22

## Source and scope

- Source DOCX: `manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v4.docx`
- Source size: 1,185,553 bytes
- Source SHA-256: `9094DECFE1CF4260F2DD1E62BE63D9ADE73508324D76B8873F6457C54E58D35D`
- The on-disk v4 DOCX was used because it is the file paired with `manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v4.pdf`. Word had that source open with an unsaved in-memory state; the source was not saved, closed, or modified. Its on-disk bytes were copied with shared read access and were hash-checked before editing.
- Scope was limited to nearby academic body-text explanations for existing figures and tables. No experiment, PPO/WP5/WP6 job, manuscript generator, figure generator, CSV generator, or protected-artifact script was run.

## Outputs

| Output | Size | SHA-256 |
| --- | ---: | --- |
| `manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v4_figtable.docx` | 1,182,295 bytes | `CB3C2B6B29FAF4C99449147DEBE1C23ADEF1FD2647AE5BF2F522E3B842C2E608` |
| `manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v4_figtable.pdf` | 1,736,755 bytes | `EF04828EEED5BE39E8C59A141FD9BA47FED702B54E9055D3EC0937DB120591EB` |

The audit file does not record its own hash because adding that hash would change the file.

## Word refresh and PDF export

- Microsoft Word 16.0 opened only the new output DOCX for editing/export.
- Word refreshed 81 main-document fields and 82 fields across story ranges, updated the live TOC, repaginated, and saved the DOCX.
- Page count was 46 before and after the Word field refresh.
- The PDF was exported with Word `ExportAsFixedFormat`, print optimization, all pages, heading bookmarks, and document-structure tags.
- PDF metadata identifies both Creator and Producer as `Microsoft Word 2024`.
- Final PDF page count: **46**.

## Figures and tables strengthened

Five existing explanatory paragraphs were strengthened and seventeen short explanatory paragraphs were inserted. Each reference below appears in body text outside its caption or table title.

| Item | PDF page(s) | Strengthened body-text role |
| --- | ---: | --- |
| Figure 3.1 | 15 | Explains the synthetic mid-price, `sigma_hat`, latent regimes, and chronological train/test split. |
| Table 3.1 | 18 | Separates naive/AS baselines, PPO aware/blind, `sigma_only`, `combined`, and oracle-label tests. |
| Figure 3.2 | 20 | Explains the traceable pipeline from synthetic paths through signals/environment/policies to OOS metrics. |
| Table 3.2 | 22 | Connects conceptual layers to reference source files for reproducibility. |
| Table 3.3 | 24 | Distinguishes the main causal detector from auxiliary robustness variants. |
| Table 3.4 | 24-25 | Explains that fixed PPO settings avoid a variant-specific tuning advantage. |
| Table 4.1 | 26 | Interprets PPO risk-adjusted performance jointly with AS inventory tail risk. |
| Figure 4.1 | 27 | Visually connects PPO risk-adjusted performance with inventory control and AS tail exposure. |
| Figure 4.2 | 27 | States that aware does not consistently dominate blind seed by seed. |
| Table 4.2 | 28 | Explains the strongest `sigma_only` mean result and lack of a robust label advantage. |
| Figure 4.3 | 29 | Gives the visual interpretation of the five-variant ablation. |
| Figure 4.4 | 29 | Explains why true labels not improving `sigma_hat` alone bounds the detector-noise objection. |
| Table 4.3 | 30 | Explains the complementary roles of paired t-tests and TOST for a bounded interpretation. |
| Table 4.4 | 30-31 | Explains detector choice as a robustness check rather than a stable aware-policy advantage. |
| Figure 4.5 | 31 | Shows that changing detector choice does not create a consistent aware advantage. |
| Figure 4.6 | 32 | Explains that regime-conditional eta still leaves `sigma_only` ahead of `combined`. |
| Figure 4.7 | 33 | Explains the closeness of `sigma_only` and `oracle_full` under mild misspecification. |
| Table 4.5 | 33 | Explains that tested signal degradation does not reveal a robust `combined` advantage. |
| Figure 4.8 | 34 | Explains that the tested degradation path does not reveal the proposed gap narrowing. |
| Figure 4.9 | 36 | Interprets the paired-seed `combined` versus `sigma_only` pattern. |
| Figure 4.10 | 37 | Explains the `combined` versus `regime_only` diagnostic and its bounded redundancy interpretation. |
| Table 5.1 | 40-41 | Explains how the risk table converts limitations into defense-safe mitigation statements. |

## Reference and content checks

- DOCX body-text scan: every required Figure/Table label appears at least once outside the `ResimYazs` caption style.
- PDF text scan: figure labels occur at least three times (List of Figures, caption, and body discussion); table labels occur at least twice (title and body discussion).
- Source and output table count: 17/17.
- All 17 table text sequences are identical between source and output.
- All 26 caption text sequences are identical between source and output.
- All 14 embedded media files are byte-identical by SHA-256.
- Equations, citations, captions, tables, figures, numerical values, scientific claims, and evidence interpretation were not edited.
- Added wording remains bounded to the controlled synthetic HFMM setting and does not claim live-trading validity or a proven PPO-internal mechanism.

## Visual QA

- All 46 Word-exported PDF pages were rendered with the bundled PDFium runtime and visually inspected.
- Every page containing a requested figure/table was checked at rendered resolution: pages 15, 18, 20, 22, 24-34, 36-37, and 40-41.
- TOC and List of Figures pages were checked after Word field refresh; page numbers are populated and reflect the 46-page document.
- No clipping, overlap, broken table, missing figure, missing-glyph box, caption separation defect, or header/footer defect was observed.
- Table 3.4 and Table 5.1 naturally continue their nearby explanation onto the following page; the continuation is readable and not clipped.

## Remaining TODO fields

The source and output retain the same two declaration placeholders:

- `TODO: location and date`
- `TODO: signature`

No personal/administrative TODO was filled or changed.

## Protected evidence status

The four protected hashes in `EVIDENCE_MANIFEST.md` remain unchanged:

| Protected artifact | Status | SHA-256 |
| --- | --- | --- |
| `results/metrics_detector_compare.csv` | MATCH | `28E7AD40BB47214F8576132846E9E1D4CD643F623CF1187743091FC367A206ED` |
| `docs/internal/wp6_sweep_full/summary_condition_variant.csv` | MATCH | `6DD627E81637A49A60163F58AC1D3EF23B8D694E39AC55BA64FBF808E978C6EA` |
| `docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv` | MATCH | `4BABCAAACE1DD5228C674E2CED9D977236F8D3ACB503C098FAEB06FF6C10B796` |
| `docs/internal/wp6_sweep_full/summary_paired_combined_vs_regime.csv` | MATCH | `2087FEFBE5DC39AF23372EA2D8999AC0F1071D0FEE90BC1B3668F2158130E8F9` |

Result: **4/4 MATCH**. No protected artifact was touched.

## Git status

`git status --short` after creating this audit:

```text
?? manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v4.docx
?? manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v4.pdf
?? manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v4_figtable.docx
?? manuscript/Onur_Emiroglu_MSc_Thesis_HECTOR_v4_figtable.pdf
?? manuscript/hector_figtable_explanation_audit_v4.md
```

No files were staged or committed.
