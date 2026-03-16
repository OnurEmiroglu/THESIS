# WP5: Out-of-Sample Evaluation Notes

## 1. Setup

- 20 seeds, 4 strategies: naive, AS, ppo_aware, ppo_blind
- Train/test split: 70/30 on exogenous series (n_train=5600, n_test=2400 steps)
- Each seed: separate PPO model trained on train split, evaluated on test split
- Exogenous series: WP2 synthetic mid + sigma_hat + regime_hat

## 2. Main OOS Results (rv_baseline detector, 20 seeds)

| Strategy | Mean Sharpe | Std Sharpe | Mean Equity | Std Equity |
|---|---|---|---|---|
| ppo_aware | ~0.85 | high | ~4.5 | high |
| ppo_blind | ~0.81 | medium | ~4.8 | medium |
| AS | ~0.85 | low | ~5.5 | low |
| naive | ~0.75 | low | ~3.5 | low |

Statistical tests (ppo_aware vs ppo_blind):
- Sharpe-based paired t-test: p=0.261 (inconclusive)
- Equity-based paired t-test: p=0.023 (ppo_blind lehine)
- Conclusion: null result — no consistent advantage for regime-aware agent

## 3. Eta Ablation (WP5.1)

Sweep: eta in [1e-4, 1e-3, 1e-2]
Result: eta=0.001 optimal
- Too low (1e-4): inventory explodes, high variance
- Optimal (1e-3): good balance of PnL and inventory control
- Too high (1e-2): agent becomes too passive, fill rate drops

## 4. Action Analysis (WP5.2)

ppo_aware regime-aware davranış öğrendi:
- L rejiminde: h=3.30, m=-0.61 (geniş spread, bid tarafına lean)
- H rejiminde: h=3.00, m=+0.34 (biraz daha dar, ask tarafına lean)

ppo_blind rejim ayrımı yapmıyor:
- Tüm rejimlerde m ≈ -0.2 ile -0.4 arası, tutarlı ama rejimsiz

P(h=5) — Undertrading Indicator:
- ppo_aware M ve H'de %33, L'de %20 oranında max spread açıyor
- ppo_blind hiç h=5 kullanmıyor
- ppo_aware yüksek variance'ının kaynağı: bazı seed'lerde çok pasif kalıyor

## 5. Null Result Interpretation

Neden aware ≠ blind değil?
- sigma_hat zaten observation'da var (6-dim obs'un 2. elemanı)
- Blind agent sigma_hat'ten rejimi implicitly öğrenebilir
- Explicit regime one-hot label redundant bilgi taşıyor
- Bu redundancy yüzünden aware agent extra signal'dan fayda sağlayamıyor

Bu zayıf değil, güçlü bir bulgu:
"Explicit regime labels are beneficial only when the regime signal is not already
implicitly available in the observation space."

## 6. Detector Robustness (WP5.3)

Bkz. docs/wp2/wp2_notes.md Section 7 ve project_full_notes.md Section 13.

Pilot (3 seeds):
- rv_baseline: aware=0.850, blind=0.814
- rv_dwell:    aware=0.804, blind=0.814
- hmm:         aware=0.713, blind=0.814

Full experiment (20 seeds, şu an çalışıyor):
- Config: w5_detector_full.json
- 3 detectors x 20 seeds x 2 strategies = 120 models
- Tahmini süre: ~70-80 saat (CPU)

## 7. Sıradaki Adımlar

1. Full detector experiment tamamlanınca:
   - Her detector için paired t-test
   - Sonuçları karşılaştır
2. Null result tutarlıysa → tez yazımına geç
3. Değilse → hyperparameter tuning:
   - total_timesteps artır (2M-5M)
   - sigma_mult sensitivity analysis
   - eta sweep genişlet
