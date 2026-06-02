# Thesis 30 Literature Review Integration Note

Date: 2026-05-28

Scope: thesis draft strengthening only. No experiments were run, no WP5/WP6 figures were regenerated, and no protected evidence CSVs, configs, models, or result artifacts were modified.

## Inputs

- `manuscript/thesis_29.docx`
- `docs/internal/literature_review_chapter_draft_2026-05-27.md`
- `docs/internal/literature_review_sources_2026-05-27.md`
- `docs/internal/literature_review_positioning_2026-05-27.md`
- `docs/internal/project_full_notes_13may.md`
- `docs/internal/defense_claim_matrix.md`
- `docs/internal/defense_risk_register.md`

## Outputs

- `scripts/gen_thesis_30.py`
- `manuscript/thesis_30.docx`
- `manuscript/thesis_30.pdf`
- `docs/internal/thesis_30_literature_review_integration_note.md`

## Structural Changes

- Inserted a standalone Chapter 3: `3. LİTERATÜR TARAMASI / RELATED WORK`.
- Renumbered the previous Chapter 3 onward by +1:
  - `3. TEORİ VE METODOLOJİ` -> `4. TEORİ VE METODOLOJİ`
  - `4. SONUÇLAR VE TARTIŞMA` -> `5. SONUÇLAR VE TARTIŞMA`
  - `5. SİNYAL BİLGİLENDİRİCİLİK SÜPÜRMESİ` -> `6. SİNYAL BİLGİLENDİRİCİLİK SÜPÜRMESİ`
  - `6. SONUÇ` -> `7. SONUÇ`
- Updated obvious body-text section references affected by the renumbering.

## Wording Changes

- Lightly revised the Introduction to frame the research question as an incremental signal-value test:
  - whether explicit categorical volatility-regime labels add robust value once `sigma_hat` is already observed by the PPO policy.
- Added defense-safe language that the evidence is consistent with signal redundancy in the tested synthetic HFMM setting.
- Preserved the boundary that this does not imply volatility regimes are irrelevant and does not identify the internal PPO mechanism.

## Bibliography Changes

Added literature-review bibliography entries for Guéant et al. (2013), Fodra and Labadie (2012, 2013), Spooner and Savani (2020), Gašperov and Kostanjčar (2021, 2022), Gašperov et al. (2021), Zimmer and Costa (2025), and Lakens (2017, 2018). Existing Avellaneda-Stoikov and Spooner et al. (2018) entries were preserved.

Preprints remain marked as preprints where appropriate. Secondary-only sources from the planning inventory were not added because they are not used in the inserted prose.

## Known Follow-Up Checks

- Render and visually inspect `thesis_30.docx` once a safe DOCX-to-PDF path is available.
- Review bibliography formatting against the final thesis template.
- Later, when the thesis template is provided, adapt `thesis_30` rather than modifying frozen `thesis_29`.
