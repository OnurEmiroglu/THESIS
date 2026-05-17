# Legacy generator scripts

Historical thesis and decisions-log DOCX generators. Each file
produced the named output at the time of its last commit. Kept
for provenance; not invoked by any current build pipeline.

Active (current) generators live one directory up:
- `scripts/gen_thesis_29.py`        - produces `manuscript/thesis_29.docx`
- `scripts/gen_decisions_log_13.py` - produces `manuscript/decisions_log_13.docx`

## Thesis generators (python-docx chain)

| File                | Output produced     | Notes                                                          |
|---------------------|---------------------|----------------------------------------------------------------|
| gen_thesis_docx.py  | (v1 ancestor)       | "From scratch" generator; predates the numbered chain.         |
| gen_thesis_15.py    | thesis_15.docx      | Mar 29                                                         |
| gen_thesis_17.py    | thesis_17.docx      | Mar 31 (gen_thesis_16.py was never committed)                  |
| gen_thesis_18.py    | thesis_18.docx      | Apr 12                                                         |
| gen_thesis_19.py    | thesis_19.docx      | Apr 13                                                         |
| gen_thesis_20.py    | thesis_20.docx      | Apr 13                                                         |
| gen_thesis_21.py    | thesis_21.docx      | Apr 13                                                         |
| gen_thesis_22.py    | thesis_22.docx      | Apr 14                                                         |
| gen_thesis_23.py    | thesis_23.docx      | Apr 14                                                         |
| gen_thesis_24.py    | thesis_24.docx      | Apr 17                                                         |
| gen_thesis_25.py    | thesis_25.docx      | Apr 17                                                         |
| gen_thesis_26.py    | thesis_26.docx      | Apr 23                                                         |
| gen_thesis_27.py    | thesis_27.docx      | May 12                                                         |
| gen_thesis_28.py    | thesis_28.docx      | May 12                                                         |

## Alternate-format draft generator (Node.js)

| File                 | Output produced              | Notes                                                          |
|----------------------|------------------------------|----------------------------------------------------------------|
| gen_thesis_draft.js  | thesis_draft.docx (METU 2-col) | Single commit (Mar 5); not invoked by manuscript/build.ps1 nor any VS Code task. |

## Decisions-log generators

| File                       | Output produced       | Notes                                              |
|----------------------------|------------------------|----------------------------------------------------|
| gen_decisions_log_2.py     | decisions_log_2.docx   | (gen_decisions_log_1.py was never committed)       |
| gen_decisions_log_3.py     | decisions_log_3.docx   |                                                    |
| gen_decisions_log_4.py     | decisions_log_4.docx   |                                                    |
| gen_decisions_log_5.py     | decisions_log_5.docx   |                                                    |
| gen_decisions_log_6.py     | decisions_log_6.docx   |                                                    |
| gen_decisions_log_7.py     | decisions_log_7.docx   |                                                    |
| gen_decisions_log_8.py     | decisions_log_8.docx   |                                                    |
| gen_decisions_log_9.py     | decisions_log_9.docx   |                                                    |
| gen_decisions_log_10.py    | decisions_log_10.docx  |                                                    |
| gen_decisions_log_11.py    | decisions_log_11.docx  |                                                    |
| gen_decisions_log_12.py    | decisions_log_12.docx  |                                                    |

## Note on appendix file-list paths

The legacy generator `scripts/legacy/gen_thesis_28.py` contains an
appendix file-list that references the pre-move paths
`scripts/gen_thesis_docx.py` and `scripts/gen_thesis_draft.js`. Those
were documentation metadata embedded in the frozen historical artifact
`thesis_28.docx`, not operational dependencies. The active generator
`scripts/gen_thesis_29.py` is the current source of truth for appendix
file-list paths.
