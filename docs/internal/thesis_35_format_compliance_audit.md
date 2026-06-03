# Thesis 35 Format Compliance Audit

Date: 2026-06-03

## Guide Source

`Student_Report_Format_Guide11.pdf` and `Student_Report_Format_Guide-1-1.pdf`
were searched for in the repository and Codex attachment directory, but neither
file was present. This audit therefore records the compliance pass against the
format requirements supplied in the thesis_35 task brief, not against a directly
extracted guide PDF. No assessor-facing optional section is added unless it is
appropriate for a student submission.

## Required Structure Interpreted for thesis_35

- Title page: author, programme, institution, course/module, supervisor,
  advisor/co-supervisor if applicable, matriculation number, submission/draft
  date, Git repository, current draft, frozen baseline, and decision log.
- Front matter: table of contents before the abstract; abstract; symbols,
  abbreviations, and glossary.
- Main report: numbered sections 1 through 12, with methodology, algorithms,
  experimental setup, results, metrics, discussion, reproducibility, and
  conclusion.
- Tables and figures: captions should be consistently numbered. Figures remain
  the existing figure set and are not regenerated.
- Equations: existing numbered display-text equations are preserved to avoid
  corrupting formulas during DOCX generation.
- Algorithms: Section 6 pseudocode is labeled as Algorithm 1 through Algorithm 4.
- Experimental setup: Section 7 includes fixed configuration, strategy variants,
  detector variants, PPO hyperparameters, and an added fixed/no-search
  hyperparameter selection protocol.
- Unit-test appendix: Appendix B is expanded to describe local tests, sanity
  checks, protected evidence hash checks, pass/fail criteria, and coverage/CI
  limitations.
- Reproducibility: Section 11 clarifies local venv setup, requirements.txt,
  commands, protected SHA256 checks, seeds, config snapshots, and logged run
  metadata.
- Authorship/contribution: Appendix D adds a single-author contribution
  statement without claiming a multi-author contribution matrix.

## Changes from thesis_34 to thesis_35

- Created `scripts/gen_thesis_35.py` as a documentation-only generator that
  copies `manuscript/thesis_34.docx`.
- Added a title-page compliance pass with the requested metadata fields.
- Added a Word TOC field plus a static contents fallback.
- Added numbered captions for the main body tables and appendix tables.
- Added Algorithm 1 through Algorithm 4 labels to Section 6 pseudocode.
- Added Section 7.6.1, "Hyperparameter Selection Protocol".
- Expanded Appendix B into a unit-test and validation appendix.
- Strengthened Section 11 reproducibility language.
- Added Appendix D, "Author Contribution Statement".
- Rounded excessive decimals in the five-variant ablation metrics table only;
  p-values, confidence intervals, hashes, formulas, and scientific claims were
  not changed.

## Placeholders Requiring User Input Before Final Submission

- Course / Module
- Supervisor
- Advisor / Co-supervisor, if applicable
- Matriculation No.
- Git Repository

## Intentionally Not Included

- No assessor-facing optional sections are added.
- No Docker, Conda, CI, or formal line-coverage claims are made because no
  Dockerfile, environment.yml, CI configuration, or coverage report was found.
- No new literature sources, experiments, or evidence pipelines are added.

## Evidence and No-Rerun Confirmation

- No PPO, WP5, WP6, detector robustness, ablation, misspecification, or
  signal-informativeness experiment was run during this pass.
- Protected performance figures and protected CSVs were not regenerated.
- The generator reuses existing figures from `manuscript/thesis_34.docx`.
- Protected CSV hashes were checked after generation and remained 4/4 MATCH:
  `results/metrics_detector_compare.csv`,
  `docs/internal/wp6_sweep_full/summary_condition_variant.csv`,
  `docs/internal/wp6_sweep_full/summary_paired_combined_vs_sigma.csv`, and
  `docs/internal/wp6_sweep_full/summary_paired_combined_vs_regime.csv`.

## Remaining Caveat

The format guide PDF was unavailable in the local workspace, so this compliance
audit should be reviewed once the official guide PDF is supplied. The thesis_35
changes are intentionally conservative and focus on the structural elements
specified in the task brief.
