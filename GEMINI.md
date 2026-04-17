# 🎓 GEMINI.md: HFMM Thesis Research & Context Reference

Bu dosya, Gemini CLI ve araştırmacı Gem için ana referans kaynağıdır. Proje, Karlsruhe Institute of Technology (KIT) Finans Mühendisliği Yüksek Lisans tezi kapsamında yürütülmektedir.

## 🧠 Araştırma Özeti ve Temel Bulgular
Pekiştirmeli öğrenme (PPO) tabanlı piyasa yapıcılığı ajanlarının, farklı volatilite rejimleri (L/M/H) altındaki performansını inceler.
* **Null Result (Ana Bulgu):** Rejim farkındalığının (aware), performansı istatistiksel olarak anlamlı düzeyde artırmadığı saptanmıştır (Sharpe p=0.261).
* **Signal Redundancy:** `sigma_hat` verisi rejim bilgisini örtük olarak taşımaktadır.
* **Oracle Paradox:** Mükemmel rejim bilgisine (oracle_full) sahip ajan bile `sigma_only` modelini geçememiştir.

## 📍 MEVCUT AKTİF ODAK: Model Misspecification
Şu anki çalışma aşaması, analitik modellerin (AS) parametrelerinin yanlış belirlendiği durumlarda PPO'nun dayanıklılığını (robustness) test etmektir.
* **Deney Tasarımı:** Avellaneda-Stoikov (AS) parametreleri olan $A$ ve $k$ değerleri rejimlere bağlanarak (regime-dependent) sabit modellerin performansı düşürülmekte ve PPO ile kıyaslanmaktadır.
* **Hedef:** PPO'nun, parametreleri yanlış ayarlanmış klasik modellere karşı esneklik avantajını kanıtlamak.

## 🏗️ Teknik Mimari ve Çalıştırma
* **Dispatcher:** İşlemler `python run.py --config config/<dosya>.json` üzerinden yürütülür.
* **WP Yapısı:** Proje WP0'dan WP5'e kadar modüler iş paketlerinden oluşur.
* **Seeding:** `PYTHONHASHSEED`, `random.seed()` ve `np.random.seed()` her zaman sabitlenir.

## 🛠️ Değiştirilemez Kurallar (Hard Constraints)
1. **Look-ahead Bias Yasak:** Ajanın state'ine asla `regime_true` konulamaz; sadece geçmiş veriye dayalı `regime_hat` kullanılır.
2. **Fee Double-count Yasak:** İşlem ücretleri `sim.py` içinde nakit güncellemesinde düşülür; ödül (reward) hesabında tekrar çıkarılmamalıdır.
3. **Exogenous Mid:** WP2 sonrası tüm deneylerde `run_wp2()` ile üretilen fiyat serileri `reset(options={"exog": df})` ile enjekte edilmelidir.
4. **Config Snapshot:** Her run başında `config_snapshot.json` kaydedilmesi zorunludur.

## 🔬 Simülasyon ve Ortam Parametreleri
* **Fill Modeli:** Poisson varış süreci; $\lambda(\delta) = A \cdot e^{-k\delta}$.
* **Gecikme:** `latency_steps=1` ile adverse selection simüle edilir.
* **Ödül Fonksiyonu:** $R_t = \Delta Equity - \eta \cdot inv^2 - skew\_penalty\_c \cdot |m|$.

## 📊 Önemli Metrikler
* **Sharpe Oranı:** Risk-düzeltmeli performans ölçütü.
* **inv_p99:** Envanter riski (PPO'da ~2 lot, Baseline'larda 20-30 lot).
* **Max Drawdown:** Maksimum sermaye kaybı.