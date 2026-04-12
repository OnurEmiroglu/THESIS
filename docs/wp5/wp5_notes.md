# WP5: Out-of-Sample Evaluation Notes

## 1. Setup

- 20 seeds, 4 strategies: naive, AS, ppo_aware, ppo_blind
- Train/test split: 70/30 on exogenous series (n_train=5600, n_test=2400 steps)
- Each seed: separate PPO model trained on train split, evaluated on test split
- Exogenous series: WP2 synthetic mid + sigma_hat + regime_hat

## 2. Main OOS Results (rv_baseline detector, 20 seeds)

| Strategy | Mean Sharpe | Std Sharpe | Mean Equity | Std Equity |
|---|---|---|---|---|
| ppo_aware | 0.715 | high | ~4.5 | high |
| ppo_blind | 0.740 | medium | ~4.8 | medium |
| AS | 0.752 | low | ~5.5 | low |
| naive | 0.105 | low | ~3.5 | low |

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

ppo_aware ve ppo_blind sınırlı davranışsal farklılık gösterdi.
Her iki ajanda h yaklaşık 1.4-1.8 bandında kaldı.
Thesis_16 final değerleri kanonik referanstır.

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

Full experiment (20 seeds) — TAMAMLANDI:
- rv_baseline: aware=0.740 vs blind=0.753, p=0.114 (anlamlı değil)
- rv_dwell: p=0.110 (anlamlı değil)
- HMM: p=0.082 (anlamlı değil, %81.8 accuracy'ye rağmen)
- ANOVA detector faktörü: F=0.003, p=0.997 (detector seçimi performansı etkilemiyor)
- Sonuç: null result 3 bağımsız detector'da tutarlı → signal redundancy argümanı sağlamlaştı

## 8. 5-Varyant Ablasyon (WP5.4)

Tasarım: Danışmanın "sigma_hat confounding yaratıyor" eleştirisine yanıt.

| Varyant | Obs İçeriği | Mean Sharpe |
|---|---|---|
| ppo_sigma_only | sadece sigma_hat | 0.753 |
| ppo_combined | sigma_hat + regime one-hot | ~0.74 |
| ppo_oracle_full | sigma_hat + gerçek rejim one-hot | 0.722 |
| ppo_oracle_pure | sadece gerçek rejim one-hot | ~0.68 |
| ppo_regime_only | sadece tahmini rejim one-hot | en düşük |

Oracle paradoksu:
- oracle_full mükemmel rejim bilgisine sahip ama sigma_only'yi geçemedi
- Paired t-test: p=0.301 (Sharpe), p=0.360 (equity) — anlamlı fark yok
- Yorum: sigma_hat tek başına yeterli; rejim etiketi ne kadar mükemmel olursa olsun ek sinyal taşımıyor

## 7. Durum (8 Nisan 2026)

WP5 tüm deneyleriyle tamamlandı:
- Ana OOS (20 seed): ✓
- Eta ablasyon: ✓
- Action analizi: ✓
- Detector robustness full run (120 model): ✓
- 5-varyant ablasyon + oracle paradoksu: ✓
- Regime-conditional eta full run (20 seed): ✓ — tamamlandı (p=0.0016, sigma_only kazandı)

Tez yazımı devam ediyor (thesis_17.pdf). Danışman toplantısı yaklaşıyor. decisions_log_4.pdf (32 karar).

## 8. Danışman Deneyleri Tamamlanma Durumu (12 Nisan 2026)

| # | Deney | Durum |
|---|-------|-------|
| 1 | Pure Ablation (5 varyant, 20 seed) | Tamamlandı — thesis_18 Section 4.2-4.3 |
| 2 | Regime-Conditional Reward Shaping (etaH=5xetaL) | Tamamlandı — thesis_18 Section 4.7 |
| 3 | Oracle + High-Accuracy Detector (hedef >=90%) | Tamamlandı — Oracle = %100 doğruluk; p=0.301 (thesis_18 Section 4.3) |
| 4 | Model Misspecification Robustness (A,k rejime bağlı) | Tamamlandı — thesis_18 Section 4.8 |

## 9. Model Misspecification Sonuçları (12 Nisan 2026)

Mild parametreler: L(A=4.0, k=1.8), M(A=5.0, k=1.5), H(A=6.0, k=1.2)
Run: 20260408-160248_seed1_w5-misspec-mild_5d9dc23
Süre: ~3.5 gün (CPU)

| Varyant | Ort. Sharpe |
|---------|-------------|
| ppo_sigma_only | 0.685 |
| ppo_oracle_full | 0.682 |
| ppo_combined | 0.651 |
| ppo_regime_only | 0.634 |
| ppo_oracle_pure | 0.602 |

t-test sonuçları:
- sigma_only vs oracle_full: p=0.881 (anlamlı degil)
- sigma_only vs combined: p=0.217 (anlamlı degil)
- sigma_only vs oracle_pure: p=0.098 (anlamlı degil)

Yorum: Signal redundancy argumani misspec ortamda da gecerli. Strong variant calistirilmadi (p=0.88 yeterli guclu null result).

Tum danishman deneyleri tamamlandi. Thesis_18 + decisions_log_5 hazir.
