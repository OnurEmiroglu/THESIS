# WP2: Synthetic Regime Detection Notes

## 1. Amaç

Sentetik 3-rejimli (L/M/H) volatilite serisi üretmek, rolling realized volatility (RV) ile rejim tespiti yapmak ve sonuçları raporlamak:

- Rejim etiketleme: sigma_hat thresholdlarıyla L/M/H sınıflandırma
- Empirical transition matrix: gözlemlenen rejim geçiş olasılıkları
- Expected duration per regime: `1 / (1 - p_ii)` adım cinsinden

## 2. İlk Sorun: Accuracy ~%33 (Rastgele Seviye)

İlk denemede detection accuracy %32.6 çıktı — rastgele 3-sınıf tahmini seviyesinde.

**Kök neden: Timescale mismatch**

- RV window = 100 adım, ama M rejimi ortalama süresi sadece ~10 adım
- Pencere birden fazla rejimi kapsıyor, RV tahmini bulanıklaşıyor
- Sonuç: thresholdlar birbirine yapışık
  - `thresh_LM = 0.1727`
  - `thresh_MH = 0.1791`
  - Aralık sadece **0.0064** — rejimleri ayırt edemeyecek kadar dar

## 3. Fix: Sticky Transition Matrix + Küçük Window + Uzun Warmup

Üç değişiklik uygulandı:

| Parametre | Önce | Sonra |
|---|---|---|
| `rv_window` | 100 | **50** |
| `warmup_steps` | 200 | **1000** |
| Transition matrix | Hızlı geçişli | **Sticky** |

Yeni transition matrix self-transition olasılıkları:

| Rejim | p_ii | Expected Duration |
|---|---|---|
| L | 0.9967 | ~300 adım |
| M | 0.9917 | ~120 adım |
| H | 0.9960 | ~250 adım |

Tüm expected duration'lar rv_window=50'nin çok üzerinde — pencere artık rejim içinde kalabiliyor.

## 4. Sonuç

| Metrik | Önce | Sonra |
|---|---|---|
| Accuracy | 32.62% | **60.70%** |
| thresh_LM | 0.1727 | 0.1771 |
| thresh_MH | 0.1791 | **0.2091** |
| Threshold gap | 0.0064 | **0.0320** (5x) |

Gözlemlenen expected durations (empirical):

- L: 406 adım
- M: 79 adım
- H: 242 adım

## 5. WP3 Implikasyonları

- **regime_hat kullanılacak, regime_true değil.** Agent'ın state'ine regime_true koymak look-ahead bias yaratır. Gerçek zamanlı tespite dayanan regime_hat kullanılmalı.
- **Smoothing opsiyonları değerlendirilebilir.** regime_hat'te gürültülü geçişler var; median filter veya minimum-duration-in-regime gibi post-processing adımları denenebilir.
- **Ablation zorunlu.** State vektöründe regime_hat var vs yok karşılaştırması yapılmalı — rejim bilgisinin agent performansına gerçek katkısını ölçmek için.

## 6. Three Detector Variants

### Detector 1: Rolling RV Baseline (existing)
- Function: assign_regime_hat
- Method: rolling std of mid returns over 50-step window, threshold at 33rd/66th percentile of warmup
- Accuracy: 60.7% (post-warmup, seed=123)

### Detector 2: RV + Dwell Filter
- Function: assign_regime_hat_dwell
- Method: rolling RV baseline + post-processing dwell filter (min_dwell=5 steps)
- Any regime transition shorter than min_dwell steps is suppressed
- Accuracy: 60.4% — minimal change because regimes are already sticky
- Key insight: dwell filter has little effect when transition matrix is already strongly diagonal

### Detector 3: HMM (GaussianHMM)
- Function: assign_regime_hat_hmm
- Method: GaussianHMM with 3 states, fit on sigma_hat series during warmup only (no look-ahead)
- State mapping: sort states by emission variance → lowest=L, middle=M, highest=H
- Causal prediction: at each step t >= warmup_end, predict on sigma_hat[warmup_end:t+1]
- Accuracy: 81.8% — significant improvement over rolling RV
- Key insight: fitting on sigma_hat (smoothed signal) rather than raw returns is critical; raw returns gave only 45.8%

## 7. Detector Robustness Rationale

Goal: show that aware vs blind result is robust to detector choice.
If null result holds across all three detectors (including HMM at 81.8%), the argument becomes:
"The performance gap is not attributable to detector quality, but to a fundamental redundancy:
sigma_hat is already in the observation space, so the explicit regime label adds no learnable signal."

Pilot results (3 seeds, mean sharpe_like):
- rv_baseline: aware=0.850, blind=0.814
- rv_dwell:    aware=0.804, blind=0.814
- hmm:         aware=0.713, blind=0.814

Full experiment: 3 detectors x 20 seeds currently running (w5_detector_full.json)
