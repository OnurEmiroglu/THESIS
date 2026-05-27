# CONFIG SNAPSHOT — HFMM Thesis

Generated from config/*.json
Purpose: single-file upload context for ChatGPT 25-file limit.
This file is documentation-only and must not be executed as code.

## File inventory

| # | Path | SHA256 | Notes |
|---:|---|---|---|
| 1 | config/base.json | 450d90ad59cbb556fe8f963e2428acd3cfdd00a439bb1e3299c8e8729409e61f | active config |
| 2 | config/w1_as_baseline.json | 9b69caf624b67a0021f05bdd0decd5faada0be5f8ffb6f28e1da3dde66899986 | active config |
| 3 | config/w1_compare.json | 3ae36c0d11e89d938ed6dba3f4b9e0ecaa065020127474642ce36b8cfb002357 | active config |
| 4 | config/w1_naive_sweep.json | b140eb9132735462f399d919591f6331c76c23f1dfe49127d48b98f528a603eb | active config |
| 5 | config/w2_synth.json | 3d612af660799c48d69e7c85d51474e2c1487ebfe6b3b4dedab38f3e63b9bcae | active config |
| 6 | config/w3_sanity.json | e36c0b6e3e68ed1d6fab79c10ddb54671e9ecd6e9cdf98bc290f8814425a4718 | active config |
| 7 | config/w3_sanity_both.json | 6126493a98854fa0e02465f47ca59200e2e1c1d232c9c24294bedb078315c1cb | active config |
| 8 | config/w4_ppo.json | 198585647d9dfd33fdc316ebc2b1c07bcdf5d779436c59b301bd81edaf8b1a46 | active config |
| 9 | config/w5_ablation_eta.json | 21fb26c897823d6508d6c917844e97601dc63251fd158d4dac8ee5659df1486a | active config |
| 10 | config/w5_ablation_skew.json | ef5f7bacd32f7d9c967faf9bd8a9c17f37d325fbfd46c47ca95b447b05cc30d4 | active config |
| 11 | config/w5_detector_full.json | 1d5a3bc8fa98730f95f58dbf7d18480584208637d80d42c72824fe046f55fb75 | active config |
| 12 | config/w5_detector_pilot.json | bdc52db3c8c1c57d5a225cd9b92eb7bdaff6f34b06c917696e264d67fce3cef6 | active config |
| 13 | config/w5_eta_regime.json | 2d75b02477b37604035ae110bc20f3dd8ebf8569df070fcd4ce374cf674f727c | active config |
| 14 | config/w5_eval.json | ec74502f1c47e4e807d61d89a245a252e1799433deeab9a621b962d165189514 | active config |
| 15 | config/w5_main.json | 7120dfba821dc3b38866e04f8080f7f65fdcc811e6a02d265575ba8ef75591ca | active config |
| 16 | config/w5_misspec_mild.json | 745380265c4c8a07f3aa7a1aa75948972e4ec675540bac1782f7dae35b6343a7 | active config |
| 17 | config/w55_audit.json | 2d7e4b3b8ae194e82d3abb36d52801d95da924e7eea5513bb0f1437e317a0ec3 | active config |
| 18 | config/w55_calibration.json | ec77efdfdff00f969b314a01b09e13b10a9ab98ee9a020b798cad01c674f644d | active config |
| 19 | config/w55_runtime.json | 1c348b5fbd310e930b3dc72cc30c10b97e0610a815655be9daefd39b7dfe13f3 | active config |
| 20 | config/w6_sweep_full.json | eef4944807e9fde14bfaa59756fee870930aa0215550f5ad651b377c2211a878 | active config |
| 21 | config/w6_sweep_pilot.json | 8efbe04d11ed69d5f18c75340479c6902c2b4c678faa13193b36e6e82d04451c | active config |

## Excluded configs

None. All config/*.json files are included.

---
CONFIG FILE: config/base.json
SHA256: 450d90ad59cbb556fe8f963e2428acd3cfdd00a439bb1e3299c8e8729409e61f

BEGIN JSON
{
  "project": "thesis-hfmm",
  "seed": 123,
  "run_tag": "wp0-smoke",
  "n_steps": 200
}
END JSON

---
CONFIG FILE: config/w1_as_baseline.json
SHA256: 9b69caf624b67a0021f05bdd0decd5faada0be5f8ffb6f28e1da3dde66899986

BEGIN JSON
{
  "job": "w1_as_baseline",
  "seed": 123,
  "market": {
    "mid0": 100.0,
    "tick_size": 0.01,
    "dt": 0.2,
    "sigma_mid_ticks": 0.8
  },
  "exec": {
    "A": 5.0,
    "k": 1.5,
    "fee_bps": 0.2,
    "latency_steps": 1
  },
  "episode": {
    "n_steps": 8000
  },
  "as": {
    "gamma": 0.01,
    "horizon_steps": 8000,
    "min_delta_ticks": 1,
    "max_delta_ticks": 25
  }
}
END JSON

---
CONFIG FILE: config/w1_compare.json
SHA256: 3ae36c0d11e89d938ed6dba3f4b9e0ecaa065020127474642ce36b8cfb002357

BEGIN JSON
{
  "job": "w1_compare",
  "seed": 123,
  "market": {
    "mid0": 100.0,
    "tick_size": 0.01,
    "dt": 0.2,
    "sigma_mid_ticks": 0.8
  },
  "exec": {
    "A": 5.0,
    "k": 1.5,
    "fee_bps": 0.2,
    "latency_steps": 1
  },
  "episode": {
    "n_steps": 8000
  },
  "sweep": {
    "half_spreads_ticks": [1, 2, 3, 4, 5]
  },
  "as": {
    "gamma": 0.01,
    "horizon_steps": 8000,
    "min_delta_ticks": 1,
    "max_delta_ticks": 25
  }
}
END JSON

---
CONFIG FILE: config/w1_naive_sweep.json
SHA256: b140eb9132735462f399d919591f6331c76c23f1dfe49127d48b98f528a603eb

BEGIN JSON
{
  "job": "w1_naive_sweep",
  "seed": 123,
  "market": {
    "mid0": 100.0,
    "tick_size": 0.01,
    "dt": 0.2,
    "sigma_mid_ticks": 0.8
  },
  "exec": {
    "A": 5.0,
    "k": 1.5,
    "fee_bps": 0.2,
    "latency_steps": 1
  },
  "episode": {
    "n_steps": 8000
  },
  "sweep": {
    "half_spreads_ticks": [1, 2, 3, 4, 5]
  }
}
END JSON

---
CONFIG FILE: config/w2_synth.json
SHA256: 3d612af660799c48d69e7c85d51474e2c1487ebfe6b3b4dedab38f3e63b9bcae

BEGIN JSON
{
  "job": "w2_synth",
  "seed": 123,
  "run_tag": "wp2-synth",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2},
  "regime": {
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.5, 1.0, 2.0],
    "rv_window": 50,
    "warmup_steps": 1000,
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "episode": {"n_steps": 10000}
}
END JSON

---
CONFIG FILE: config/w3_sanity.json
SHA256: e36c0b6e3e68ed1d6fab79c10ddb54671e9ecd6e9cdf98bc290f8814425a4718

BEGIN JSON
{
  "job": "w3_sanity",
  "seed": 123,
  "run_tag": "wp3-sanity",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.01, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  }
}
END JSON

---
CONFIG FILE: config/w3_sanity_both.json
SHA256: 6126493a98854fa0e02465f47ca59200e2e1c1d232c9c24294bedb078315c1cb

BEGIN JSON
{
  "job": "w3_sanity",
  "seed": 123,
  "run_tag": "wp3-sanity-both",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.01, "use_regime": false},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  }
}
END JSON

---
CONFIG FILE: config/w4_ppo.json
SHA256: 198585647d9dfd33fdc316ebc2b1c07bcdf5d779436c59b301bd81edaf8b1a46

BEGIN JSON
{
  "job": "w4_ppo",
  "seed": 123,
  "run_tag": "wp4-ppo",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.01, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 200000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.0
  }
}
END JSON

---
CONFIG FILE: config/w5_ablation_eta.json
SHA256: 21fb26c897823d6508d6c917844e97601dc63251fd158d4dac8ee5659df1486a

BEGIN JSON
{
  "job": "w5_ablation_eta",
  "seed": 11,
  "run_tag": "wp5-ablation-eta",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.01, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 200000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.0
  },
  "wp5": {
    "seeds": [11, 22, 33],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0},
    "eta_values": [0.0001, 0.001, 0.01]
  }
}
END JSON

---
CONFIG FILE: config/w5_ablation_skew.json
SHA256: ef5f7bacd32f7d9c967faf9bd8a9c17f37d325fbfd46c47ca95b447b05cc30d4

BEGIN JSON
{
  "job": "w5_ablation_skew",
  "seed": 1,
  "run_tag": "wp5-ablation-skew",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.001, "use_regime": true, "skew_penalty_c": 0.0},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0},
    "skew_c_values": [1e-4]
  }
}
END JSON

---
CONFIG FILE: config/w5_detector_full.json
SHA256: 1d5a3bc8fa98730f95f58dbf7d18480584208637d80d42c72824fe046f55fb75

BEGIN JSON
{
  "job": "w5_detector_compare",
  "seed": 1,
  "run_tag": "wp5-detector-full",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.001, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0}
  }
}
END JSON

---
CONFIG FILE: config/w5_detector_pilot.json
SHA256: bdc52db3c8c1c57d5a225cd9b92eb7bdaff6f34b06c917696e264d67fce3cef6

BEGIN JSON
{
  "job": "w5_detector_compare",
  "seed": 1,
  "run_tag": "wp5-detector-pilot",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.001, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01
  },
  "wp5": {
    "seeds": [1, 2, 3],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0}
  }
}
END JSON

---
CONFIG FILE: config/w5_eta_regime.json
SHA256: 2d75b02477b37604035ae110bc20f3dd8ebf8569df070fcd4ce374cf674f727c

BEGIN JSON
{
  "job": "w5_eval",
  "seed": 42,
  "run_tag": "w5-eta-regime",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {
    "eta": 0.001,
    "eta_regime": {
      "L": 0.0005,
      "M": 0.001,
      "H": 0.0025
    },
    "use_sigma": true,
    "regime_source": "hat"
  },
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "device": "cpu"
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0}
  }
}
END JSON

---
CONFIG FILE: config/w5_eval.json
SHA256: ec74502f1c47e4e807d61d89a245a252e1799433deeab9a621b962d165189514

BEGIN JSON
{
  "job": "w5_eval",
  "seed": 11,
  "run_tag": "wp5-eval-oos",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.001, "use_regime": true},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 200000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.0
  },
  "wp5": {
    "seeds": [11, 22, 33],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0}
  }
}
END JSON

---
CONFIG FILE: config/w5_main.json
SHA256: 7120dfba821dc3b38866e04f8080f7f65fdcc811e6a02d265575ba8ef75591ca

BEGIN JSON
{
  "job": "w5_eval",
  "seed": 1,
  "run_tag": "wp5-ablation",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "wp3": {"eta": 0.001, "use_sigma": true, "regime_source": "hat"},
  "as": {"gamma": 0.01, "horizon_steps": 8000, "min_delta_ticks": 1, "max_delta_ticks": 25},
  "sweep": {"half_spreads_ticks": [1, 2, 3, 4, 5]},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "device": "cpu"
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0}
  }
}
END JSON

---
CONFIG FILE: config/w5_misspec_mild.json
SHA256: 745380265c4c8a07f3aa7a1aa75948972e4ec675540bac1782f7dae35b6343a7

BEGIN JSON
{
  "job": "w5_eval",
  "run_tag": "w5-misspec-mild",
  "seed": 1,
  "market": {
    "mid0": 100.0,
    "tick_size": 0.01,
    "dt": 0.2,
    "sigma_mid_ticks": 0.8
  },
  "exec": {
    "A": 5.0,
    "k": 1.5,
    "fee_bps": 0.2,
    "latency_steps": 1
  },
  "misspec": {
    "enabled": true,
    "params": {
      "L": {"A": 4.0, "k": 1.8},
      "M": {"A": 5.0, "k": 1.5},
      "H": {"A": 6.0, "k": 1.2}
    }
  },
  "episode": {
    "n_steps": 8000,
    "inv_max_clip": 50
  },
  "wp3": {
    "eta": 0.001,
    "use_regime": true,
    "use_sigma": true,
    "regime_source": "hat"
  },
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "device": "cuda"
  },
  "wp5": {
    "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    "train_frac": 0.7,
    "naive": {"h": 2, "m": 0},
    "variants": ["sigma_only", "regime_only", "combined", "oracle_pure", "oracle_full"]
  },
  "as": {
    "gamma": 0.01,
    "horizon_steps": 8000,
    "min_delta_ticks": 1,
    "max_delta_ticks": 25
  },
  "regime": {
    "rv_window": 50,
    "warmup_steps": 400,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.5, 1.0, 2.0],
    "trans_matrix": [[0.9967, 0.0023, 0.001], [0.0042, 0.9917, 0.0041], [0.001, 0.003, 0.996]]
  }
}
END JSON

---
CONFIG FILE: config/w55_audit.json
SHA256: 2d7e4b3b8ae194e82d3abb36d52801d95da924e7eea5513bb0f1437e317a0ec3

BEGIN JSON
{
  "project": "thesis-hfmm",
  "seed": 123,
  "run_tag": "wp55-signal-audit",
  "job": "w55_audit",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "episode": {"n_steps": 8000},
  "audit": {
    "noise_std": "auto",
    "noise_std_rationale": "When 'auto', job computes noise_std = 0.5 * clean_sigma_std_post_warmup so the 'moderate estimation error' regime tracks the canonical signal scale.",
    "lag_k_steps": 5,
    "n_bins": 5,
    "fill_value": 0.0,
    "threshold_band_pct": 0.05
  }
}
END JSON

---
CONFIG FILE: config/w55_calibration.json
SHA256: ec77efdfdff00f969b314a01b09e13b10a9ab98ee9a020b798cad01c674f644d

BEGIN JSON
{
  "project": "thesis-hfmm",
  "seed": 42,
  "run_tag": "wp55-calibration",
  "job": "w55_calibration",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "episode": {"n_steps": 8000},
  "calibration": {
    "alpha_values": [0.0, 0.05, 0.10, 0.20, 0.40, 0.80, 1.60],
    "k_values": [0, 1, 2, 5, 10, 20, 50],
    "n_seeds": 5
  }
}
END JSON

---
CONFIG FILE: config/w55_runtime.json
SHA256: 1c348b5fbd310e930b3dc72cc30c10b97e0610a815655be9daefd39b7dfe13f3

BEGIN JSON
{
  "project": "thesis-hfmm",
  "seed": 42,
  "run_tag": "wp55-runtime-benchmark",
  "job": "w55_runtime",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 1.0, "sigma_mid_ticks": 0.5},
  "regime": {"rv_window": 50, "warmup_steps": 1000},
  "episode": {"n_steps": 8000},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.1, "latency_steps": 0},
  "ppo": {
    "total_timesteps": 100000,
    "n_steps": 2048,
    "batch_size": 64,
    "n_epochs": 10,
    "learning_rate": 3e-4,
    "gamma": 0.99,
    "policy": "MlpPolicy"
  },
  "env": {"use_regime": false, "eta": 1e-3},
  "benchmark": {"devices": ["cpu", "cuda"], "seeds": [42, 123]}
}
END JSON

---
CONFIG FILE: config/w6_sweep_full.json
SHA256: eef4944807e9fde14bfaa59756fee870930aa0215550f5ad651b377c2211a878

BEGIN JSON
{
  "project": "thesis-hfmm",
  "seed": 42,
  "run_tag": "wp6-sweep-full",
  "job": "w6_sweep_full",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp3": {"eta": 0.001, "use_sigma": true, "regime_source": "hat"},
  "wp4": {
    "total_timesteps": 1000000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "device": "cpu"
  },
  "sweep": {
    "conditions": ["full", "noisy", "lagged", "coarsened", "none"],
    "variants": ["sigma_only", "regime_only", "combined", "oracle_pure", "oracle_full"],
    "omit_cells": [["none", "sigma_only"]],
    "seeds": [42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61],
    "timesteps": 1000000,
    "noisy_alpha": 0.40,
    "lagged_k": 20,
    "coarsened_n_bins": 5
  }
}
END JSON

---
CONFIG FILE: config/w6_sweep_pilot.json
SHA256: 8efbe04d11ed69d5f18c75340479c6902c2b4c678faa13193b36e6e82d04451c

BEGIN JSON
{
  "project": "thesis-hfmm",
  "seed": 42,
  "run_tag": "wp6-sweep-pilot",
  "job": "w6_sweep_pilot",
  "market": {"mid0": 100.0, "tick_size": 0.01, "dt": 0.2, "sigma_mid_ticks": 0.8},
  "exec": {"A": 5.0, "k": 1.5, "fee_bps": 0.2, "latency_steps": 1},
  "episode": {"n_steps": 8000, "inv_max_clip": 50},
  "regime": {
    "rv_window": 50,
    "warmup_steps": 1000,
    "sigma_mid_ticks_base": 0.8,
    "sigma_mult": [0.6, 1.0, 1.8],
    "trans_matrix": [
      [0.9967, 0.0023, 0.0010],
      [0.0042, 0.9917, 0.0041],
      [0.0010, 0.0030, 0.9960]
    ]
  },
  "wp3": {"eta": 0.001, "use_sigma": true, "regime_source": "hat"},
  "wp4": {
    "total_timesteps": 200000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 256,
    "n_epochs": 10,
    "gamma": 0.999,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "device": "cpu"
  },
  "sweep": {
    "conditions": ["full", "noisy", "lagged", "coarsened", "none"],
    "variants": ["sigma_only", "regime_only", "combined", "oracle_pure", "oracle_full"],
    "omit_cells": [["none", "sigma_only"]],
    "seeds": [42, 43, 44],
    "timesteps": 200000,
    "noisy_alpha": 0.40,
    "lagged_k": 20,
    "coarsened_n_bins": 5
  }
}
END JSON

