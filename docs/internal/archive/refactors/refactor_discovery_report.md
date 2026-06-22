# Audit report — five `src/` root job scripts

## Part A — Internal imports

### `src/w0_smoke.py`
```
8:  from __future__ import annotations
11: import numpy as np                     (inside try/except)
15: import matplotlib.pyplot as plt
17: from .run_context import RunContext, save_json
```
Note: this is the **only** one of the five using a *relative* import (`.run_context`); the others use `src.*` absolute imports.

### `src/w1_as_baseline.py`
```
8:  from __future__ import annotations
10: import json
11: from pathlib import Path
13: import numpy as np
14: import pandas as pd
15: import matplotlib.pyplot as plt
17: from src.wp1.sim import MarketParams, ExecParams, MMSimulator
```

### `src/w1_compare.py`
```
1:  from __future__ import annotations
3:  import json
4:  from pathlib import Path
6:  import numpy as np
7:  import pandas as pd
8:  import matplotlib.pyplot as plt
10: from src.wp1.sim import MarketParams, ExecParams, MMSimulator
```

### `src/w1_naive_sweep.py`
```
1:  from __future__ import annotations
3:  from dataclasses import asdict
4:  from pathlib import Path
5:  import json
7:  import numpy as np
8:  import pandas as pd
9:  import matplotlib.pyplot as plt
11: from src.wp1.sim import MarketParams, ExecParams, MMSimulator
```

### `src/w3_sanity.py`
```
3:  from __future__ import annotations
5:  import copy
6:  import json
7:  from pathlib import Path
9:  import matplotlib.pyplot as plt
10: import numpy as np
11: import pandas as pd
13: from src.w1_as_baseline import as_deltas_ticks, compute_metrics
14: from src.wp1.sim import ExecParams, MarketParams, MMSimulator
15: from src.wp2.synth_regime import run_wp2
16: from src.wp3.env import MMEnv
```

## Part B — External references

### `w0_smoke`
| File | Line | Content |
|---|---|---|
| `run.py` | 25 | `from src.w0_smoke import wp0_smoke` |
| `docs/internal/codebase_snapshot.py` | 35 | `from src.w0_smoke import wp0_smoke` *(static source dump, not executed)* |
| `scripts/gen_thesis_15.py` | 731 | `["src/w0_smoke.py", "WP0 smoke test"]` *(thesis file-list table; documentation string)* |
| `scripts/gen_thesis_17.py` | 781 | same string-list entry |
| `scripts/gen_thesis_18.py` | 851 | same |
| `scripts/gen_thesis_19.py` | 849 | same |
| `scripts/gen_thesis_20.py` | 851 | same |
| `scripts/gen_thesis_21.py` | 852 | same |
| `scripts/gen_thesis_22.py` | 859 | same |
| `scripts/gen_thesis_23.py` | 923 | same |
| `scripts/gen_thesis_24.py` | 938 | same |
| `scripts/gen_thesis_25.py` | 943 | same |
| `scripts/gen_thesis_26.py` | 1045 | same |

### `w1_as_baseline`  ← most-imported of the five
| File | Line | Content |
|---|---|---|
| `run.py` | 27 | `from src.w1_as_baseline import job_entry as w1_as_baseline` |
| `src/w3_sanity.py` | 13 | `from src.w1_as_baseline import as_deltas_ticks, compute_metrics` |
| `src/wp4/job_w4_ppo.py` | 21 | `from src.w1_as_baseline import compute_metrics` |
| `src/wp5/job_w5_eval.py` | 22 | `from src.w1_as_baseline import as_deltas_ticks, compute_metrics` |
| `src/wp5/job_w5_ablation_eta.py` | 21 | `from src.w1_as_baseline import compute_metrics` |
| `src/wp5/job_w5_ablation_skew.py` | 21 | `from src.w1_as_baseline import compute_metrics` |
| `src/wp5/job_w5_detector_compare.py` | 20 | `from src.w1_as_baseline import compute_metrics` |
| `scripts/eval_only_seed1to7.py` | 19 | `from src.w1_as_baseline import as_deltas_ticks, compute_metrics` |
| `docs/internal/codebase_snapshot.py` | 37, 1016, 2022, 2200, 2511, 2681, 2939 | repeated lines from source dump |
| `scripts/gen_thesis_15..26.py` | (line varies) | `["src/w1_as_baseline.py", ...]` documentation entry |

### `w1_compare`
| File | Line | Content |
|---|---|---|
| `run.py` | 28 | `from src.w1_compare import job_entry as w1_compare` |
| `docs/internal/codebase_snapshot.py` | 38 | source-dump line |
| `scripts/gen_thesis_15..26.py` | (line varies) | `["src/w1_compare.py", "WP1 strateji karşılaştırması"]` |

### `w1_naive_sweep`
| File | Line | Content |
|---|---|---|
| `run.py` | 26 | `from src.w1_naive_sweep import job_entry as w1_naive_sweep` |
| `docs/internal/codebase_snapshot.py` | 36 | source-dump line |
| `scripts/gen_thesis_15..26.py` | (line varies) | `["src/w1_naive_sweep.py", "Naive sabit-spread sweep deneyi"]` |

### `w3_sanity`
| File | Line | Content |
|---|---|---|
| `run.py` | 30 | `from src.w3_sanity import job_entry as w3_sanity` |
| `docs/internal/codebase_snapshot.py` | 40 | source-dump line |
| `scripts/gen_thesis_15..26.py` | (line varies) | `["src/w3_sanity.py", "Gymnasium ortamı sanity check"]` |

**Notes on the non-import callers:**
- `docs/internal/codebase_snapshot.py` is a frozen text dump of the codebase (every match there is verbatim source from another file embedded as text). It will not break at runtime, but its contents will become out-of-date after the move. Decide separately whether to regenerate it.
- `scripts/gen_thesis_*.py` files (15 through 26) only reference these names as **string literals** inside a file-listing table for the thesis manuscript. They do not import the modules. Only `gen_thesis_26.py` is the current generator (per CLAUDE.md the active version is `thesis_25` / now `thesis_26`); the older numbered variants are archived.

## Part C — Config references

JSON configs that name one of the five modules in their `"job"` key:

| Config file | Key | Value |
|---|---|---|
| `config/w1_as_baseline.json` | `job` | `"w1_as_baseline"` |
| `config/w1_compare.json` | `job` | `"w1_compare"` |
| `config/w1_naive_sweep.json` | `job` | `"w1_naive_sweep"` |
| `config/w3_sanity.json` | `job` | `"w3_sanity"` |
| `config/w3_sanity_both.json` | `job` | `"w3_sanity"` |

No config explicitly sets `"job": "w0_smoke"`. However, `config/base.json` has `"run_tag": "wp0-smoke"` and no `job` key — `run.py` line 57 defaults missing `job` to `"w0_smoke"`, so `base.json` runs the smoke test implicitly.

## Part D — `run.py` mechanics and wp folder structure

### 1. How `run.py` resolves modules

The full file is 99 lines (shown above). Key mechanism:

- Lines 24–35 perform **fully qualified, hardcoded `from src.<module>` imports** at module load time. There is no dynamic import based on the config string, no `importlib`, no path prefix logic.
- Line 57 reads `job = cfg.get("job", "w0_smoke")` — the value is a **bare routing key** (e.g. `"w1_compare"`), used only by the `if/elif` ladder on lines 59–88 to pick which already-imported `job_entry` to call.
- Lines 81–86 are the only dynamic case: `w55_audit` and `w55_runtime` use lazy `from src.wp5_5...` imports inside the elif branches. The five files we're moving are NOT in this lazy block.

**Implication for refactor:** the `cfg["job"]` strings in JSON do *not* need to change, because they are routing keys, not import paths. Only `run.py`'s top-level `from src.<x> import` lines need updating, plus any other `from src.w1_as_baseline import ...` site in the codebase (Part B above lists all six in-code import sites + one script).

### 2. wp folder contents and `__init__.py`

| Folder | `__init__.py`? | Other files |
|---|---|---|
| `src/wp1/` | yes | `sim.py` |
| `src/wp2/` | yes | `job_w2_synth.py`, `synth_regime.py`, `compare_detectors.py` |
| `src/wp3/` | yes | `env.py` |
| `src/wp4/` | yes | `job_w4_ppo.py` |
| `src/wp5/` | yes | `job_w5_eval.py`, `job_w5_ablation_eta.py`, `job_w5_ablation_skew.py`, `job_w5_detector_compare.py`, `analyze_actions.py`, `stats_detector_robustness.py`, `figure_thesis.py`, `figure_thesis_23.py` |
| `src/wp5_5/` | yes | `signal_degradation.py`, `signal_audit.py`, `job_w55_audit.py`, `job_w55_runtime.py` |

### 3. `src/wp0/`

**Does not exist.** Confirmed via `Glob src/wp0/**` returning no files. Will need to be created (with an `__init__.py`) before `w0_smoke.py` can be relocated.

## Part E — Summary table

| File | current_path | internal_imports | external_callers (real Python imports) | config_references |
|---|---|---:|---:|---:|
| `w0_smoke` | `src/w0_smoke.py` | 4 | 1 (`run.py`) | 0 explicit, 1 implicit (`base.json` via default) |
| `w1_as_baseline` | `src/w1_as_baseline.py` | 7 | 8 (`run.py`, `src/w3_sanity.py`, `src/wp4/job_w4_ppo.py`, `src/wp5/job_w5_eval.py`, `src/wp5/job_w5_ablation_eta.py`, `src/wp5/job_w5_ablation_skew.py`, `src/wp5/job_w5_detector_compare.py`, `scripts/eval_only_seed1to7.py`) | 1 (`w1_as_baseline.json`) |
| `w1_compare` | `src/w1_compare.py` | 7 | 1 (`run.py`) | 1 (`w1_compare.json`) |
| `w1_naive_sweep` | `src/w1_naive_sweep.py` | 8 | 1 (`run.py`) | 1 (`w1_naive_sweep.json`) |
| `w3_sanity` | `src/w3_sanity.py` | 11 | 1 (`run.py`) | 2 (`w3_sanity.json`, `w3_sanity_both.json`) |

`external_callers` excludes the static dump in `docs/internal/codebase_snapshot.py` and the string-list entries in `scripts/gen_thesis_15..26.py` (neither imports anything; both will go stale after the move but won't break runtime).

## Headlines for the move

- **Hot spot:** `w1_as_baseline` is the only file with non-trivial fan-in (7 in-repo Python callers + run.py). All seven import the same two helpers: `compute_metrics` and/or `as_deltas_ticks`. Worth deciding whether to update those import paths to `src.wp1.w1_as_baseline` everywhere, or extract `compute_metrics`/`as_deltas_ticks` into a shared `src/wp1/` utility module first.
- **`w0_smoke` has a relative import (`from .run_context`)** — moving it to `src/wp0/` will break that line; it'll need to become `from ..run_context import ...` or `from src.run_context import ...`.
- **`src/wp0/` does not exist yet** — create it with an `__init__.py` before the move.
- **Config files do not need editing**: the `cfg["job"]` strings are routing keys, not import paths. Only `run.py`'s import block (and the seven other importers of `w1_as_baseline`) need to change.
- **Two stale-after-move artefacts to flag (out of scope today, but worth noting):** `docs/internal/codebase_snapshot.py` and `scripts/gen_thesis_*.py` reference the old paths only as text/strings; neither blocks runtime, but the thesis generator's file-list table will show wrong paths until the active `gen_thesis_26.py` is regenerated.
