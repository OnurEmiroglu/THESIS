# Proje Tam Notlar

## 1. Proje Genel Bakış

**Konu:** Yüksek frekanslı piyasa yapıcılık (HFMM) — PPO tabanlı RL agent'ın farklı volatilite rejimlerinde (L/M/H) bid/ask kotasyonu öğrenmesi.

**Araştırma sorusu:** Rejim-farkında (aware) PPO agent, rejim-kör (blind) PPO agent'tan anlamlı şekilde daha iyi performans gösterir mi?

**Mevcut bulgu:** Null result — istatistiksel olarak anlamlı fark yok. Ana OOS: Sharpe p=0.261 (inconclusive), equity p=0.023 (ppo_blind lehine, 20 seed, rv_baseline). Detector robustness full run tamamlandı (3 detector × 20 seed × 2 strateji = 120 model): rv_baseline p=0.114, rv_dwell p=0.110, HMM p=0.082, ANOVA F=0.003 p=0.997. 5-varyant ablasyon tamamlandı: ppo_sigma_only en yüksek Sharpe (0.753); oracle_full (0.722) sigma_only'yi geçemedi (oracle paradoksu, p=0.301). PPO varyantları Sharpe bazında naive'i geçiyor (~0.85 vs ~0.75) ve AS ile yakın performans gösteriyor (~0.85); ancak equity bazında AS, PPO'lardan daha yüksek mutlak equity üretiyor. Rejime koşullu η deneyi (ηH=5×ηL, 20 seed): combined vs sigma_only Sharpe p=0.0016 — sigma_only lehine anlamlı fark, signal redundancy ödül tasarımı boyutunda da teyit edildi.

**Üniversite:** KIT (Karlsruhe Institute of Technology), Financial Engineering MSc Thesis.

## 2. Değiştirilemez Kurallar

1. **Look-ahead bias yasak.** Agent'ın state'ine `regime_true` koymak yasak. Sadece `regime_hat` (gerçek zamanlı tespit) kullanılır. Tüm detektorler yalnızca geçmiş veriyi kullanır.
2. **Fee double-count yasak.** Simülatör (`sim.py`) fee'yi cash update'inde zaten düşüyor. Reward hesabında fee tekrar çıkarılmamalı.
3. **Exogenous mid kullanılır.** WP2+ deneylerde mid-price serisi `run_wp2()` ile üretilip env'e `reset(options={"exog": df})` ile enjekte edilir. Simülatörün kendi BM'si override edilir.
4. **Seed disiplini.** Her run `PYTHONHASHSEED`, `random.seed()`, `np.random.seed()` ile sabitlenir. Run ID'de seed ve git commit hash bulunur.
5. **Config snapshot zorunlu.** Her run başında `config_snapshot.json` kaydedilir — sonradan hangi parametrelerle çalışıldığı kesin bilinir.

## 3. Teknik Altyapı

| Bileşen | Versiyon/Detay |
|---|---|
| Python | 3.x (Windows 11) |
| RL Framework | Stable-Baselines3 2.7.1 |
| RL Algorithm | PPO (MlpPolicy) |
| Gym | Gymnasium 1.2.3 |
| Deep Learning | PyTorch >=2.3 |
| HMM | hmmlearn >=0.3 |
| Veri/Plot | numpy, pandas, matplotlib, scipy, seaborn |
| Lint | ruff |
| Manuscript | Markdown + pandoc (DOCX çıktı) |

**Entry point:** `run.py --config config/<dosya>.json`
- `cfg["job"]` alanına göre ilgili modülün `job_entry(cfg, ctx)` fonksiyonu çağrılır.
- Her run `results/runs/<run_id>/` altında izole dizin oluşturur.

## 4. Simülasyon Modeli (`src/wp1/sim.py`)

### Fill modeli
- Fill intensity: `lambda(delta) = A * exp(-k * delta)` (Avellaneda-Stoikov Poisson arrivals)
- Fill olasılığı: `P = 1 - exp(-lambda * dt)`
- Parametreler: `A=5.0`, `k=1.5` (default config)

### Mid-price dinamiği
- Arithmetic Brownian Motion: `dMid = sigma_mid_ticks * sqrt(dt) * z * tick_size`
- Exogenous mid override: WP2+ deneylerde rejim-bağlı sentetik seri kullanılır

### Quote latency
- `latency_steps=1`: kotasyon fiyatı 1 adım eski mid'e göre hesaplanır
- Effective delta = (current_mid - quote_price) / tick_size → adverse selection etkisi

### Veri yapıları
- `MarketParams` (frozen): `mid0`, `tick_size`, `dt`, `sigma_mid_ticks`
- `ExecParams` (frozen): `A`, `k`, `fee_bps`, `latency_steps`
- `MMState` (mutable): `t`, `mid`, `cash`, `inv`; `equity = cash + inv * mid`

### Fee yapısı
- `fee_bps=0.2` (0.2 bps)
- `fee = |notional| * fee_bps * 1e-4`
- Bid fill: `cash -= (bid_px + fee)`, `inv += 1`
- Ask fill: `cash += (ask_px - fee)`, `inv -= 1`

## 5. WP0: Proje İskeleti

**Durum:** Tamamlandı.

`src/run_context.py` modülü:
- `setup_run(config_path)`: Run ID oluşturur, dizin yaratır, seed sabitler, logger kurar, config snapshot kaydeder, meta.json yazar.
- `finalize_run(ctx, status)`: `status.json` yazar (success/failed).
- `RunContext` dataclass: `run_id`, `run_dir`, `plots_dir`, `config`, `logger`, `metrics`.
- `CSVMetricLogger`: Satır satır CSV metrik kaydı.

**Run ID formatı:** `YYYYMMDD-HHMMSS_seed<S>_<TAG>_<COMMIT>`

Her run dizini içerir:
- `config_snapshot.json` — kullanılan parametreler
- `meta.json` — run_id, git commit, python version, platform
- `run.log` — tam log çıktısı
- `metrics.csv` — sayısal metrikler
- `plots/` — grafikler
- `status.json` — bitiş durumu

## 6. WP1: Baseline Stratejiler

**Durum:** Tamamlandı.

### Naive Fixed-Spread (`src/w1_naive_sweep.py`)
- Sabit simetrik half-spread ile kotasyon: `delta_bid = delta_ask = h` (tick cinsinden)
- Sweep: `h in [1, 2, 3, 4, 5]`
- Her h değeri için `MMSimulator` ile tam episode çalıştırılır
- Varsayılan: `h=2, m=0` (skew yok)

### Avellaneda-Stoikov (`src/w1_as_baseline.py`)
- Reservation price: `r = mid - q * gamma * sigma^2 * tau`
- Optimal half-spread: `d = 0.5 * gamma * sigma^2 * tau + (1/gamma) * ln(1 + gamma/k)`
- Delta'lar `[min_delta_ticks, max_delta_ticks]` aralığına clamp edilir
- Parametreler: `gamma=0.01`, `horizon_steps=8000`

### Karşılaştırma (`src/w1_compare.py`)
- Aynı seed ile naive ve AS yan yana çalıştırılır
- `compute_metrics()`: final_equity, sharpe_like, fill_rate, turnover, max_drawdown, inv_p99

## 7. WP2: Sentetik Rejim Üretimi ve Tespiti

**Durum:** Tamamlandı.

### Rejim üretimi (`src/wp2/synth_regime.py`)
- 3-state Markov chain: L (low vol), M (medium vol), H (high vol)
- Sticky transition matrix — expected duration: L~300, M~120, H~250 adım
- Volatilite çarpanları: `sigma_mult = [0.6, 1.0, 1.8]` (L/M/H sırasıyla)
- Mid-price: rejim-bağlı sigma ile arithmetic BM

### Rolling RV hesabı
- `compute_rolling_rv()`: 50-adımlık pencerede mid return'lerin standart sapması
- `sigma_hat = rv / tick_size` (tick-normalize)

### Threshold kalibrasyonu
- `calibrate_thresholds()`: warmup dönemindeki sigma_hat değerlerinin 33. ve 66. percentile'ı
- warmup_steps=1000

### Üç detector varyantı

| Detector | Fonksiyon | Yöntem | Accuracy |
|---|---|---|---|
| rv_baseline | `assign_regime_hat()` | Threshold bazlı sınıflandırma | 60.7% |
| rv_dwell | `assign_regime_hat_dwell()` | Threshold + dwell filtre (min_dwell=5) | 60.4% |
| hmm | `assign_regime_hat_hmm()` | GaussianHMM, warmup'ta fit, causal predict | 81.8% |

**Dwell filtre** (`apply_dwell_filter()`): min_dwell'den kısa rejim geçişlerini önceki rejimle değiştirir. Transition matrix zaten sticky olduğu için etkisi minimal.

**HMM detayları:**
- GaussianHMM (3 state, diag covariance), warmup verisinde fit
- State mapping: emission variance'a göre sırala → en düşük=L, orta=M, en yüksek=H
- Causal prediction: her t >= warmup_end adımında sadece sigma_hat[warmup_end:t+1] kullanılır
- Kritik: sigma_hat (smoothed) üzerinde fit → %81.8; ham return üzerinde fit → sadece %45.8

### Standalone karşılaştırma (`src/wp2/compare_detectors.py`)
- `python -m src.wp2.compare_detectors` ile çalıştırılır (run.py dışı)
- Aynı sentetik veri üzerinde 3 detector'ün accuracy'sini tablo olarak yazdırır
- Sonuçları `data/processed/detector_comparison.csv`'ye kaydeder

## 8. WP3: Gymnasium Ortamı (`src/wp3/env.py`)

**Durum:** Tamamlandı.

### MMEnv sınıfı
`gymnasium.Env` alt sınıfı, `MMSimulator` backend'ini sarmalıyor.

### Observation space (6-dim, float32)
| Index | Değişken | Formül |
|---|---|---|
| 0 | `q_norm` | `clip(inv, -50, 50) / 50` |
| 1 | `sigma_hat` | Rolling RV (exog serisinden), NaN → 0.0 |
| 2 | `tau` | `(n_steps - t) / n_steps` |
| 3 | `regime_L` | 1.0 if regime=="L" else 0.0 (use_regime=True iken) |
| 4 | `regime_M` | 1.0 if regime=="M" else 0.0 |
| 5 | `regime_H` | 1.0 if regime=="H" else 0.0 |

`use_regime=False` iken regime one-hot tamamen sıfır → PPO-blind.

### Action space: MultiDiscrete([5, 5])
- `h_idx in {0..4}` → `h = h_idx + 1` (half-spread: 1..5 tick)
- `m_idx in {0..4}` → `m = m_idx - 2` (skew: -2..+2 tick)
- `delta_bid = max(1, h + m)`, `delta_ask = max(1, h - m)`

### Reward
```
R_t = (equity_after - equity_before) - eta * inv_after^2 - skew_penalty_c * |m|
```
- `eta=0.001` (varsayılan): envanter cezası
- `skew_penalty_c=0.0` (varsayılan): skew cezası (ablasyon deneyi için)
- Fee zaten sim'de cash'ten düşülüyor — reward'da tekrar çıkarılmaz

### Exogenous series
- `reset(options={"exog": df})` ile enjekte edilir
- DataFrame kolonları: `mid`, `sigma_hat`, `regime_hat`
- Mid override: simülatörün `_evolve_mid` fonksiyonu geçici olarak exog mid döndürecek şekilde patch'lenir

## 9. WP4: PPO Eğitimi (`src/wp4/job_w4_ppo.py`)

**Durum:** Tamamlandı.

### Eğitim akışı
1. `run_wp2()` ile exogenous seri üret
2. İki aşama: `aware` (use_regime=True) ve `blind` (use_regime=False)
3. Her aşama için: `MMEnv` → `Monitor` → `DummyVecEnv` → `PPO.learn()`
4. Model kaydı: `models/ppo_aware.zip`, `models/ppo_blind.zip`
5. Deterministic eval: `model.predict(obs, deterministic=True)`

### PPO hiperparametreleri (varsayılan)
| Parametre | Değer |
|---|---|
| learning_rate | 3e-4 |
| n_steps | 2048 |
| batch_size | 256 |
| n_epochs | 10 |
| gamma | 0.999 |
| gae_lambda | 0.95 |
| clip_range | 0.2 |
| ent_coef | 0.01 |
| total_timesteps | 1,000,000 (full) / 200,000 (pilot) |

### Çıktılar
- `metrics_w4_eval_{stage}.csv` — eval metrikleri
- `plots/equity_{stage}.png`, `plots/inventory_{stage}.png`
- `plots/compare_final_equity_aware_vs_blind.png`
- `summary_w4.json` — hiperparametreler + her iki aşamanın sonuçları

## 10. WP5: OOS Değerlendirme ve Ablasyonlar

**Durum:** Tamamlandı.

### 10a. Ana OOS Değerlendirme (`src/wp5/job_w5_eval.py`)
- 4 strateji: naive, AS, ppo_aware, ppo_blind
- N seed ile tekrarlanır (20 seed ana deneyde)
- Train/test split: %70/%30 exogenous seri üzerinde
- Her seed için: aware+blind eğitim → 4 strateji OOS test
- Çıktılar: `metrics_wp5_oos.csv`, `metrics_wp5_oos_by_regime.csv`, equity curve CSV'leri, bar plot'lar

**Ana sonuçlar (20 seed):**
- Naive ve AS: düşük Sharpe
- PPO-aware (~0.85) ve PPO-blind (~0.81): naive'i geçiyor, AS ile yakın
- Aware vs blind farkı: p=0.261 (Sharpe), p=0.023 (equity, blind lehine)

### 10b. Eta Ablasyonu (`src/wp5/job_w5_ablation_eta.py`)
- Config: `w5_ablation_eta.json`
- Eta değerleri: {1e-4, 1e-3, 1e-2}
- Yalnızca PPO-aware, OOS test
- Çıktılar: `metrics_wp5_ablation_eta.csv`, fill_rate ve equity plot'ları

### 10c. Skew Penalty Ablasyonu (`src/wp5/job_w5_ablation_skew.py`)
- Config: `w5_ablation_skew.json`
- `skew_penalty_c` değerleri: {1e-4}
- 20 seed, 1M timesteps
- Action histogram'ları ile skew dağılımı analizi

### 10d. Detector Robustness (`src/wp5/job_w5_detector_compare.py`)
- 3 detector (rv_baseline, rv_dwell, hmm) x N seed x 2 strateji (aware, blind)
- Her detector için exog serisindeki `regime_hat` ilgili detector ile değiştirilir
- ppo_blind detector'den etkilenmez (regime one-hot sıfır)
- Pilot: 3 seed (`w5_detector_pilot.json`), Full: 20 seed (`w5_detector_full.json`)

Full run sonuçları (20 seed):
- rv_baseline: aware mean=0.740 vs blind mean=0.753, p=0.114 (anlamlı değil)
- rv_dwell: p=0.110 (anlamlı değil)
- HMM: p=0.082 (anlamlı değil, %81.8 accuracy'ye rağmen)
- ANOVA detector faktörü: F=0.003, p=0.997 (detector seçimi etkisiz)

### 10e. Action Analizi (`src/wp5/analyze_actions.py`)
- Standalone script: `python -m src.wp5.analyze_actions`
- En son `wp5-eval` run dizinini bulur, curve CSV'lerini okur
- h ve m dağılımlarını rejim bazında karşılaştırır
- Çıktılar: `action_h_by_regime.png`, `action_m_by_regime.png`, `ph5_by_regime.png`
- P(h=5) = undertrading göstergesi (agent spreadi çok açıyor mu?)

### 10f. 5-Varyant Ablasyon (`src/wp5/job_w5_ablation.py`)
- 5 varyant: sigma_only (sadece sigma_hat), regime_only (sadece one-hot), combined (her ikisi), oracle_pure (gerçek rejim, sigma_hat yok), oracle_full (gerçek rejim + sigma_hat)
- 20 seed, 1M timesteps
- Sonuçlar:
  | Varyant | Sharpe |
  |---|---|
  | ppo_sigma_only | 0.753 |
  | ppo_combined | ~0.74 |
  | ppo_oracle_full | 0.722 |
  | ppo_oracle_pure | ~0.68 |
  | ppo_regime_only | en düşük |
- Oracle paradoksu: Mükemmel rejim bilgisi bile sigma_only'yi geçemedi (p=0.301)
- Temel çıkarım: sigma_hat sinyal redundancy'nin doğrudan kanıtı

### 10g. Rejime Koşullu Envanter Cezası (`config/w5_eta_regime.json`)
- Danışmanın önerisi: η rejime bağlı kılınsın (ηH = 5×ηL)
- Konfigürasyon: ηL=0.0005, ηM=0.001, ηH=0.0025
- 20 seed, 1M timesteps, 5 varyant (sigma_only, combined, oracle_full, oracle_pure, regime_only)
- Pilot (3 seed): null result korundu, combined std dramatik düştü (0.041 vs 0.140)
- Full run (20 seed) sonuçları:
  | Varyant | Sharpe | Std |
  |---|---|---|
  | ppo_sigma_only | 0.714 | 0.119 |
  | ppo_combined | 0.629 | 0.147 |
  | ppo_oracle_full | 0.638 | 0.158 |
  | ppo_oracle_pure | 0.578 | 0.247 |
  | ppo_regime_only | 0.513 | 0.238 |
- Paired t-test (combined vs sigma_only): Sharpe p=0.0016, Equity p=0.008
- Yorum: Rejime koşullu η performansı artırmak yerine düşürdü.
  Signal redundancy argümanı ödül tasarımı boyutunda da teyit edildi.
- thesis_17'ye Section 4.7 olarak eklendi.

## 11. Mevcut Bulgular ve Tartışma

### Ana bulgu: Null result
- PPO-aware ve PPO-blind arasında istatistiksel olarak anlamlı fark yok
- Sharpe paired t-test: p=0.261 (inconclusive)
- Equity paired t-test: p=0.023 (blind lehine, ama pratik fark küçük)

### Yorumlama
Her iki PPO varyantı da `sigma_hat`'ı observation'da alıyor (index 1). Rejim one-hot'ı (index 3-5) sadece sigma_hat'ın kaba bir ayrıklaştırılmış hali. Agent zaten sigma_hat'tan volatilite bilgisini öğreniyor — discrete rejim etiketi ek sinyal taşımıyor.

### Sharpe vs Equity ayrımı
- Sharpe bazında PPO varyantları naive'i geçiyor (~0.85 vs ~0.75), AS ile yakın (~0.85)
- Ancak equity bazında AS daha yüksek mutlak equity üretiyor — PPO'lar risk-adjusted performansta üstün ama toplam PnL'de AS'nin gerisinde kalabiliyor
- Bu fark, PPO'nun inventory penalty (eta) nedeniyle daha konservatif pozisyon almasından kaynaklanıyor

### Olası eleştiri ve cevap
- "Detector kötü olduğu için aware çalışmıyor" → Full run'da HMM ile %81.8 accuracy'de bile null result doğrulandı (p=0.082); 3 detector'de tutarlı
- "Daha çok eğitim lazım" → 1M timesteps, 20 seed, tutarlı sonuç
- "Eta yanlış" → Ablasyon yapıldı, 3 farklı eta değeri denendi
- "sigma_hat'ın varlığı confounding yaratıyor" → 5-varyant ablasyon ile test edildi; sigma_hat çıkarıldığında (regime_only, oracle_pure) performans düşüyor — sigma_hat'ın kritik sinyal olduğu doğrulandı
- "Oracle ile dene" → oracle_full bile sigma_only'yi geçemedi (p=0.301) — signal redundancy kesin olarak teyit edildi
- "Ödül fonksiyonu rejime özgü davranışı teşvik etmiyor" → Rejime koşullu η denendi (ηH=5×ηL, 20 seed); sigma_only istatistiksel olarak anlamlı biçimde güçlü kaldı (p=0.0016). Signal redundancy ödül kanalında da teyit edildi.

## 12. Dosya Referans Tablosu

### Kaynak kod

| Dosya | Rol |
|---|---|
| `run.py` | Ana entry point; config'e göre job dispatcher |
| `src/run_context.py` | RunContext, setup_run, finalize_run, CSVMetricLogger, seeding |
| `src/w0_smoke.py` | WP0 smoke test |
| `src/wp1/sim.py` | MMSimulator — tick-by-tick simülasyon motoru |
| `src/w1_naive_sweep.py` | Naive half-spread sweep |
| `src/w1_as_baseline.py` | Avellaneda-Stoikov baseline; compute_metrics() |
| `src/w1_compare.py` | Naive vs AS karşılaştırma |
| `src/wp2/synth_regime.py` | Rejim üretimi, rolling RV, 3 detector (baseline, dwell, hmm) |
| `src/wp2/job_w2_synth.py` | WP2 job entry |
| `src/wp2/compare_detectors.py` | Standalone detector karşılaştırma scripti |
| `src/wp3/env.py` | MMEnv — Gymnasium ortamı |
| `src/w3_sanity.py` | WP3 sanity check (naive, AS, random; rejim ablasyonu) |
| `src/wp4/job_w4_ppo.py` | PPO eğitimi (aware + blind) |
| `src/wp5/job_w5_eval.py` | OOS değerlendirme (4 strateji x N seed) |
| `src/wp5/job_w5_ablation_eta.py` | Eta ablasyon sweep |
| `src/wp5/job_w5_ablation_skew.py` | Skew penalty ablasyonu |
| `src/wp5/job_w5_detector_compare.py` | Detector robustness deneyi |
| `src/wp5/analyze_actions.py` | Action dağılım analizi ve plot'ları |

### Config dosyaları

| Config | Job | Açıklama |
|---|---|---|
| `w1_naive_sweep.json` | `w1_naive_sweep` | Half-spread sweep |
| `w1_as_baseline.json` | `w1_as_baseline` | AS tek episode |
| `w1_compare.json` | `w1_compare` | Naive vs AS |
| `w2_synth.json` | `w2_synth` | Sentetik rejim üretimi |
| `w3_sanity.json` | `w3_sanity` | Sanity check (aware) |
| `w3_sanity_both.json` | `w3_sanity` | Sanity check (runs both aware + blind via job_entry) |
| `w4_ppo.json` | `w4_ppo` | PPO eğitimi |
| `w5_main.json` | `w5_eval` | Ana OOS eval (20 seed, 1M ts) |
| `w5_eval.json` | `w5_eval` | OOS eval (3 seed, 200k ts) |
| `w5_ablation_eta.json` | `w5_ablation_eta` | Eta ablasyonu |
| `w5_ablation_skew.json` | `w5_ablation_skew` | Skew penalty ablasyonu |
| `w5_detector_pilot.json` | `w5_detector_compare` | Detector pilot (3 seed) |
| `w5_detector_full.json` | `w5_detector_compare` | Detector full (20 seed) |

### Diğer

| Dosya/Dizin | Açıklama |
|---|---|
| `CLAUDE.md` | Claude Code talimatları (proje ve mimari rehber) |
| `docs/wp2/wp2_notes.md` | WP2 teknik notlar (sorunlar, çözümler, detector varyantları) |
| `manuscript/thesis.md` | Tez metni (Markdown kaynak) |
| `results/runs/` | Deney çıktıları (git ignored) |
| `data/processed/` | Ara veri dosyaları (git ignored) |
| `requirements.txt` | Python bağımlılıkları |

---

## 13. WP5 Detector Robustness Experiment

### Motivasyon
Mevcut 20 seed OOS sonuçları (rv_baseline detector) null result verdi:
- Sharpe-based paired t-test: p=0.261 (inconclusive)
- Equity-based t-test: p=0.023 (ppo_blind lehine)

Null result'ı güçlendirmek için detector robustness yaklaşımı benimsendi:
"Aware vs blind sonucu detector seçimine duyarlı mı?"

Eğer 3 farklı detector ile de null result çıkarsa:
- "Sinyal gürültülüydü" eleştirisi kapanır
- "Sinyal net verildi, fark yine de yok" → güçlü null result

### Üç Detector

| Detector | Fonksiyon | Accuracy |
|---|---|---|
| rv_baseline | assign_regime_hat | 60.7% |
| rv_dwell | assign_regime_hat_dwell (min_dwell=5) | 60.4% |
| hmm | assign_regime_hat_hmm (GaussianHMM) | 81.8% |

HMM'in accuracy'si yüksek çıktı çünkü:
- Ham return yerine sigma_hat serisine fit edildi (smoothed signal)
- Ham return ile: 45.8%, sigma_hat ile: 81.8%

### Pilot Sonuçları (3 seed)

| Detector | ppo_aware mean sharpe | ppo_blind mean sharpe |
|---|---|---|
| rv_baseline | 0.850 | 0.814 |
| rv_dwell | 0.804 | 0.814 |
| hmm | 0.713 | 0.814 |

Gözlemler:
- ppo_blind tüm detector'larda aynı (0.814) — beklenen, detector blind'ı etkilemiyor
- rv_baseline'da aware > blind (0.850 > 0.814) ama fark küçük ve 3 seed yetersiz
- hmm'de aware < blind — HMM'in farklı labeling'i agent'ı zorlaştırıyor

### Full Experiment
Config: w5_detector_full.json
- 3 detector x 20 seed x 2 strateji = 120 model
- CPU training, ~70-80 saat
- Su an calisiyor

### Tamamlanma Durumu
Full experiment tamamlandı. Null result 3 bağımsız detector'da tutarlı şekilde doğrulandı.

### Mevcut Durum (12 Nisan 2026)
- thesis_18.pdf: Final tez taslagi (Section 4.8 + Bulgu 6 dahil, 6 bulgu)
- decisions_log_5.pdf: Guncel karar logu (35 karar)
- Danishman toplantisi: hazirlaniliyor
- Tum danishman deneyleri tamamlandi (4/4)
- Sonraki adim: Hocaya gorusme maili + toplanti sunumu
