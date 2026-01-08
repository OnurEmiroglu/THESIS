# THESIS

## Structure
- `manuscript/` — thesis text (Markdown) and final figures/tables
- `notebooks/` — exploration and figure generation
- `src/` — reusable Python code
- `data/raw/` — raw data (ignored by git)
- `data/processed/` — processed data (ignored by git)
- `results/runs/` — experiment outputs (ignored by git)
- `config/` — configuration files
- `references/` — bibliography and notes

## Writing
Main file: `manuscript/thesis.md`

Preview in VS Code:
- Open `thesis.md`
- Press `Ctrl+Shift+V`

## Reproducibility
- Keep code in `src/`
- Save run outputs under `results/runs/<run_id>/`
