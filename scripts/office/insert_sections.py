"""
Insert SEMBOLLER VE KISALTMALAR and TERİMLER SÖZLÜĞÜ sections
before the GİRİŞ heading in unpacked_thesis/word/document.xml.
"""
import sys, os

FONT_RPR = (
    '<w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman" '
    'w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"/>'
)

def heading1(text):
    return (
        f'<w:p><w:pPr><w:pStyle w:val="Heading1"/>'
        f'<w:spacing w:after="120" w:before="240" w:line="360"/>'
        f'<w:jc w:val="left"/></w:pPr>'
        f'<w:r><w:rPr>{FONT_RPR}<w:b/><w:bCs/>'
        f'<w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>'
        f'<w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
    )

def heading2(text):
    return (
        f'<w:p><w:pPr><w:pStyle w:val="Heading2"/>'
        f'<w:spacing w:after="90" w:before="180" w:line="360"/>'
        f'<w:jc w:val="left"/></w:pPr>'
        f'<w:r><w:rPr>{FONT_RPR}<w:b/><w:bCs/>'
        f'<w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr>'
        f'<w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
    )

def normal_para(text):
    return (
        f'<w:p><w:pPr>'
        f'<w:spacing w:after="120" w:before="0" w:line="360"/>'
        f'<w:jc w:val="both"/></w:pPr>'
        f'<w:r><w:rPr>{FONT_RPR}'
        f'<w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>'
        f'<w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
    )

def empty_para():
    return (
        '<w:p><w:pPr>'
        '<w:spacing w:after="0" w:before="0" w:line="360"/>'
        '<w:jc w:val="both"/></w:pPr></w:p>'
    )

def cell_xml(text, width, is_header=False, italic=False, shading=None):
    """Generate a table cell."""
    shd = ""
    if shading:
        shd = f'<w:shd w:fill="{shading}" w:color="auto" w:val="clear"/>'

    bold = "<w:b/><w:bCs/>" if is_header else ""
    ital = '<w:i/><w:iCs/>' if italic else '<w:i w:val="false"/><w:iCs w:val="false"/>'
    align = "center" if is_header else "left"

    return (
        f'<w:tc><w:tcPr>'
        f'<w:tcW w:type="dxa" w:w="{width}"/>'
        f'{shd}'
        f'<w:tcMar>'
        f'<w:top w:w="80" w:type="dxa"/>'
        f'<w:bottom w:w="80" w:type="dxa"/>'
        f'<w:left w:w="120" w:type="dxa"/>'
        f'<w:right w:w="120" w:type="dxa"/>'
        f'</w:tcMar>'
        f'</w:tcPr>'
        f'<w:p><w:pPr>'
        f'<w:spacing w:after="20" w:before="20" w:line="276"/>'
        f'<w:jc w:val="{align}"/></w:pPr>'
        f'<w:r><w:rPr>{FONT_RPR}{bold}{ital}'
        f'<w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
        f'<w:t xml:space="preserve">{text}</w:t></w:r></w:p></w:tc>'
    )

def make_table(headers, rows, col_widths, header_bg="#D5E8F0"):
    """Build a complete table XML string."""
    total_w = sum(col_widths)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in col_widths)

    # Header row
    hdr_cells = ""
    for i, h in enumerate(headers):
        hdr_cells += cell_xml(h, col_widths[i], is_header=True, shading=header_bg.replace("#", ""))

    header_row = f'<w:tr><w:trPr><w:tblHeader/></w:trPr>{hdr_cells}</w:tr>'

    # Data rows
    data_rows = ""
    for row in rows:
        cells = ""
        for i, val in enumerate(row):
            # First column in symbol tables: italic
            italic = (i == 0) and len(col_widths) == 2
            cells += cell_xml(val, col_widths[i], italic=italic)
        data_rows += f'<w:tr>{cells}</w:tr>'

    return (
        f'<w:tbl><w:tblPr>'
        f'<w:tblW w:type="dxa" w:w="{total_w}"/>'
        f'<w:tblBorders>'
        f'<w:top w:val="single" w:color="000000" w:sz="1"/>'
        f'<w:left w:val="single" w:color="000000" w:sz="1"/>'
        f'<w:bottom w:val="single" w:color="000000" w:sz="1"/>'
        f'<w:right w:val="single" w:color="000000" w:sz="1"/>'
        f'<w:insideH w:val="single" w:color="000000" w:sz="1"/>'
        f'<w:insideV w:val="single" w:color="000000" w:sz="1"/>'
        f'</w:tblBorders>'
        f'<w:tblLayout w:type="fixed"/></w:tblPr>'
        f'<w:tblGrid>{grid}</w:tblGrid>'
        f'{header_row}{data_rows}</w:tbl>'
    )

def page_break():
    return (
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
    )

# ── DATA ──────────────────────────────────────────────────────────

MATH_SYMBOLS = [
    ("M_t", "t anındaki mid-price (orta fiyat) [para birimi]"),
    ("σ", "Volatilite parametresi — mid-price'ın birim zamandaki standart sapması [tick/√saniye]"),
    ("σ_base", "Temel volatilite parametresi; Orta (M) rejim için referans değer (0.8 tick/√saniye)"),
    ("σ_L, σ_M, σ_H", "Düşük, Orta ve Yüksek rejimlere karşılık gelen volatilite değerleri"),
    ("Δt", "Simülasyon zaman adımı büyüklüğü (0.2 saniye)"),
    ("z", "Standart normal rassal değişken; z ~ N(0,1)"),
    ("λ(δ)", "δ tick uzaklığındaki kotasyon için Poisson dolum yoğunluğu [dolum/saniye]"),
    ("A", "Sıfır uzaklıkta (δ=0) temel dolum yoğunluğu (5.0 dolum/saniye)"),
    ("k", "Dolum yoğunluğunun uzaklıkla üstel azalma hızı (1.5 tick başına)"),
    ("δ", "Kotasyon uzaklığı — bid veya ask fiyatının mid-price'tan tick cinsinden sapması"),
    ("δ_bid", "Bid (alış) kotasyonunun mid-price'tan uzaklığı [tick]"),
    ("δ_ask", "Ask (satış) kotasyonunun mid-price'tan uzaklığı [tick]"),
    ("P_fill", "Bir zaman adımında en az bir dolumun gerçekleşme olasılığı"),
    ("h", "Half-spread — kotasyon yarı-aralığı [tick]; h ∈ {1, 2, 3, 4, 5}"),
    ("m", "Skew — asimetrik kotasyon kayması [tick]; m ∈ {-2, -1, 0, +1, +2}"),
    ("q", "Envanter (inventory) — anda tutulan net pozisyon miktarı [lot]"),
    ("q_norm", "Normalize edilmiş envanter; q_norm = q / inv_max_clip ∈ [-1, +1]"),
    ("inv_max_clip", "Envanter kırpma sınırı (50 lot)"),
    ("τ", "Kalan zaman fraksiyonu; τ = (T - t) / T ∈ [0, 1]"),
    ("T", "Episode toplam adım sayısı (8000 adım)"),
    ("R_t", "t adımındaki ödül (reward)"),
    ("η", "Envanter ceza katsayısı; η = 0.001"),
    ("γ", "Avellaneda-Stoikov risk aversion (riskten kaçınma) parametresi; γ = 0.01"),
    ("r", "Avellaneda-Stoikov rezervasyon fiyatı"),
    ("d", "Avellaneda-Stoikov optimal yarı-spread"),
    ("k_price", "Fiyat cinsinden ifade edilen yoğunluk azalma parametresi; k_price = k / tick_size"),
    ("P", "Markov zinciri geçiş matrisi (3×3)"),
    ("p_ii", "i. rejimin kendi kendine geçiş olasılığı (köşegen eleman)"),
    ("K_T", "Clearness index — atmosfer geçirgenlik oranı (güneş enerjisi modellerinde)"),
    ("Sharpe", "Sharpe oranı — risk-düzeltmeli getiri ölçütü; Sharpe = (μ/σ) × √(1/Δt)"),
    ("inv_p99", "Mutlak envanter değerinin 99. persantili [lot]"),
    ("equity", "Toplam varlık değeri; equity = cash + q × M_t"),
]

GREEK_LETTERS = [
    ("γ (gamma)", "Risk aversion parametresi (Avellaneda-Stoikov modelinde)"),
    ("η (eta)", "Envanter ceza katsayısı (ödül fonksiyonunda)"),
    ("σ (sigma)", "Volatilite — fiyat değişiminin standart sapması"),
    ("τ (tau)", "Kalan zaman fraksiyonu"),
    ("λ (lambda)", "Poisson dolum yoğunluğu"),
    ("δ (delta)", "Kotasyon uzaklığı (mid-price'tan tick cinsinden sapma)"),
    ("μ (mu)", "Ortalama adım başına PnL (Sharpe hesabında)"),
]

ABBREVIATIONS = [
    ("PPO", "Proximal Policy Optimization — yakınsak politika optimizasyonu algoritması"),
    ("RL", "Reinforcement Learning — pekiştirmeli öğrenme"),
    ("AS", "Avellaneda-Stoikov — klasik stokastik kontrol tabanlı piyasa yapıcılığı modeli"),
    ("HFT", "High-Frequency Trading — yüksek frekanslı alım-satım"),
    ("OOS", "Out-of-Sample — modelin eğitilmediği veri üzerinde değerlendirme"),
    ("WP", "Work Package — iş paketi (proje aşaması)"),
    ("ABM", "Arithmetic Brownian Motion — aritmetik Brownian hareketi"),
    ("RV", "Realized Volatility — gerçekleşmiş volatilite (kayan pencere ile hesaplanan)"),
    ("PnL", "Profit and Loss — kar ve zarar"),
    ("CUDA", "Compute Unified Device Architecture — NVIDIA GPU hesaplama mimarisi"),
    ("SB3", "Stable-Baselines3 — PPO implementasyonu için kullanılan Python kütüphanesi"),
    ("MlpPolicy", "Multi-Layer Perceptron Policy — çok katmanlı algılayıcı politika ağı"),
    ("GAE", "Generalized Advantage Estimation — genelleştirilmiş avantaj tahmini (PPO bileşeni)"),
    ("L / M / H", "Low / Medium / High — Düşük / Orta / Yüksek volatilite rejimleri"),
]

GLOSSARY = [
    ("Ablation (Ablasyon)", "Bir modelin belirli bir bileşeninin çıkarılarak ya da devre dışı bırakılarak etkisinin ölçülmesi amacıyla yapılan kontrollü deney. Bu çalışmada, rejim bilgisinin (use_regime=False) ve envanter ceza katsayısının (η) etkisi ablasyon deneyleriyle ölçülmüştür."),
    ("Action Space (Eylem Uzayı)", "Bir pekiştirmeli öğrenme ajanının her adımda seçebileceği tüm olası eylemlerin kümesi. Bu çalışmada eylem uzayı, half-spread (h) ve skew (m) değerlerinden oluşan ayrık bir yapıdadır."),
    ("Adverse Selection (Ters Seçim)", "Piyasa yapıcının bilgili yatırımcılara karşı dezavantajlı konuma düşmesi durumu. Örneğin, fiyat hızla değişirken eski kotasyon fiyatından doldurulma riski."),
    ("Agent (Ajan)", "Pekiştirmeli öğrenmede, bir ortamda gözlem yaparak karar veren ve ödül sinyaline göre davranışını güncelleyen öğrenen sistem."),
    ("Ask (Satış Fiyatı)", "Piyasa yapıcının satmaya hazır olduğu fiyat. Her zaman bid fiyatının üzerindedir."),
    ("Bid (Alış Fiyatı)", "Piyasa yapıcının almaya hazır olduğu fiyat. Her zaman ask fiyatının altındadır."),
    ("Bid-Ask Spread", "Alış ve satış fiyatı arasındaki fark. Piyasa yapıcının temel gelir kaynağıdır. Bu çalışmada tick cinsinden ifade edilmektedir."),
    ("Brownian Motion (Brownian Hareketi)", "Rastlantısal yürüyüş modellerinin sürekli-zaman limiti. Aritmetik Brownian Hareketi'nde (ABM) fiyat değişimleri sabit ortalama ve volatilite parametrelerine sahip normal dağılımdan çekilmektedir."),
    ("Clip (Kırpma)", "Bir değerin belirli bir aralıkla sınırlandırılması işlemi. Bu çalışmada envanter ±50 lot ile kırpılmaktadır."),
    ("Convergence (Yakınsama)", "Pekiştirmeli öğrenme eğitiminde politikanın optimal ya da kararlı bir çözüme ulaşması süreci."),
    ("Entropy Coefficient (Entropi Katsayısı)", "PPO'da keşif-sömürü dengesini ayarlayan hiperparametre. Yüksek değer daha fazla rassal eylem anlamına gelir. Bu çalışmada ent_coef=0.01 kullanılmıştır."),
    ("Episode", "Pekiştirmeli öğrenmede başlangıçtan bitiş koşuluna kadar süren bir tam simülasyon koşusu. Bu çalışmada bir episode 8000 zaman adımından oluşmaktadır."),
    ("Exogenous Series (Dışsal Seri)", "Modelin dışında önceden üretilmiş ve tüm stratejilere aynı biçimde sunulan fiyat/volatilite serisi. Adil karşılaştırma için kullanılır."),
    ("Fill (Dolum)", "Piyasa yapıcının kotasyon verdiği fiyattan gerçekleşen emir eşleşmesi. Bid tarafından dolum, piyasa yapıcının envanterini artırır; ask tarafından dolum azaltır."),
    ("Fill Rate (Dolum Oranı)", "Toplam adım sayısına bölünen dolum sayısı. Piyasa yapıcının ne kadar aktif işlem yaptığının göstergesi."),
    ("Gymnasium", "OpenAI tarafından geliştirilen, pekiştirmeli öğrenme ortamları için standart Python arayüzü. reset() ve step() metodlarını tanımlar."),
    ("Half-Spread (Yarı-Aralık)", "Bid veya ask fiyatının mid-price'tan uzaklığı. Tam spread'in yarısı. Bu çalışmada h sembolüyle gösterilir."),
    ("Hyperparameter (Hiperparametre)", "Eğitim sürecinden önce kullanıcı tarafından belirlenen ve modelin nasıl öğreneceğini kontrol eden parametre. Örnek: learning rate, batch size, γ."),
    ("Inventory (Envanter)", "Piyasa yapıcının anda elinde bulundurduğu net pozisyon miktarı. Pozitif değer net uzun (long), negatif değer net kısa (short) pozisyonu ifade eder."),
    ("Inventory Risk (Envanter Riski)", "Piyasa yapıcının büyük envanter pozisyonu tutarken fiyat hareketleri nedeniyle maruz kaldığı zarar riski."),
    ("Latency (Gecikme)", "Piyasa yapıcının kotasyon güncellemesi ile piyasanın bu güncellemeyi işlemesi arasındaki zaman farkı. Bu çalışmada latency_steps=1 ile modellenmektedir."),
    ("Limit Order Book", "Bekleme sırasındaki tüm alış ve satış emirlerinin fiyat-miktar listesi. Piyasa yapıcılar bu kitaba likidite sağlar."),
    ("Lot", "Alım-satım işlemlerinde standart birim miktar. Bu çalışmada envanter lot cinsinden ifade edilmektedir."),
    ("Markov Chain (Markov Zinciri)", "Gelecekteki durumun yalnızca mevcut duruma bağlı olduğu (geçmişten bağımsız) olasılıksal süreç. Bu çalışmada rejim geçişleri için kullanılmaktadır."),
    ("Market Making (Piyasa Yapıcılığı)", "Finansal piyasalarda sürekli alış ve satış kotasyonu vererek likidite sağlama faaliyeti. Piyasa yapıcı, spread geliri karşılığında envanter ve adverse selection riskini üstlenir."),
    ("Mid-Price", "Anlık alış (bid) ve satış (ask) fiyatlarının ortalaması. Piyasanın gerçek değerine en yakın fiyat tahmini."),
    ("Model Misspecification (Model Yanlış Belirleme)", "Kullanılan modelin gerçek veri üretim sürecini tam olarak yansıtmaması durumu. Örneğin, AS modelinin sabit volatilite varsayması."),
    ("Null Result", "Araştırma hipotezinin verilerce desteklenmediği bulgu. İstatistiksel olarak anlamlı bir fark gözlemlenmemesi durumu. Bu çalışmada rejim farkındalığı hipotezi null result ile sonuçlanmıştır."),
    ("Observation Space (Gözlem Uzayı)", "Ajanın her adımda çevreden aldığı bilginin vektör temsili. Bu çalışmada 6 boyutludur: [q_norm, σ̂, τ, r_L, r_M, r_H]."),
    ("One-Hot Encoding", "Kategorik bir değişkeni ikili vektörle temsil etme yöntemi. Örneğin, H rejimi için [0, 0, 1] vektörü kullanılır."),
    ("Out-of-Sample (OOS)", "Modelin eğitilmediği, bağımsız bir veri kümesi üzerinde yapılan değerlendirme. Overfitting'i önlemek için kullanılır."),
    ("Overfitting", "Modelin eğitim verisine aşırı uyum sağlayarak yeni veride düşük performans göstermesi."),
    ("Percentile (Persantil)", "Veri setinin belirli bir yüzdesinin altında kaldığı değer. Örneğin inv_p99, envanterin %99'unun bu değerin altında olduğunu ifade eder."),
    ("Policy (Politika)", "Pekiştirmeli öğrenmede ajanın gözleme göre eylem seçme stratejisi. PPO, politikayı sinir ağı parametreleri ile temsil eder."),
    ("Poisson Process (Poisson Süreci)", "Olayların bağımsız ve sabit ortalama hızda rastlantısal gerçekleştiği olasılıksal süreç. Bu çalışmada emir dolumları Poisson süreci ile modellenmektedir."),
    ("PPO (Proximal Policy Optimization)", "John Schulman ve ark. (2017) tarafından geliştirilen politika gradyanı tabanlı RL algoritması. Politika güncellemelerini sınırlı adımlarla kısıtlayarak kararlı eğitim sağlar."),
    ("Regime (Rejim)", "Piyasanın belirli bir volatilite seviyesinde bulunduğu dönem. Bu çalışmada L (Düşük), M (Orta) ve H (Yüksek) olmak üzere üç rejim tanımlanmıştır."),
    ("Reservation Price (Rezervasyon Fiyatı)", "Avellaneda-Stoikov modelinde envanter riskini içselleştiren düzeltilmiş mid-price tahmini."),
    ("Reward (Ödül)", "Pekiştirmeli öğrenmede ajanın her adımda çevreden aldığı sayısal sinyal. Bu çalışmada R_t = ΔEquity − η·q² formülü kullanılmaktadır."),
    ("Risk-Adjusted Return (Risk-Düzeltmeli Getiri)", "Getirinin, üstlenilen risk miktarına bölünmesiyle elde edilen performans ölçütü. Sharpe oranı en yaygın örnektir."),
    ("Seed (Tohum)", "Rastlantısal sayı üretecinin başlangıç değeri. Aynı seed ile aynı sonuçlar elde edilir; tekrarlanabilirlik için kullanılır."),
    ("Sharpe Ratio (Sharpe Oranı)", "Birim risk başına elde edilen fazla getiriyi ölçen performans metriği. Sharpe = (μ/σ) × √(1/Δt) formülüyle hesaplanır."),
    ("Skew (Asimetrik Kotasyon)", "Bid ve ask kotasyonlarının mid-price'a göre eşit olmayan biçimde kaydırılması. Pozitif skew, ask tarafını yaklaştırır; negatif skew bid tarafını yaklaştırır."),
    ("Stable-Baselines3 (SB3)", "PPO dahil çeşitli RL algoritmalarının güvenilir PyTorch implementasyonlarını içeren Python kütüphanesi."),
    ("State (Durum)", "Pekiştirmeli öğrenmede çevrenin belirli bir andaki tam gözlemlenebilir temsili. Observation space ile eşanlamlı kullanılmaktadır."),
    ("Sticky Transition Matrix", "Köşegen elemanları yüksek (öz-geçiş olasılığı büyük) Markov geçiş matrisi. Rejimlerin uzun süre devam etmesini sağlar."),
    ("Stochastic Control (Stokastik Kontrol)", "Rassal süreçler içeren sistemlerde optimal karar verme teorisi. Avellaneda-Stoikov modeli bu çerçeveye dayanmaktadır."),
    ("Tick", "Finansal piyasalarda fiyatın alabileceği en küçük artış birimi. Bu çalışmada tick_size = 0.01 para birimi olarak tanımlanmıştır."),
    ("Timestep (Zaman Adımı)", "Simülasyonun bir sonraki duruma geçtiği en küçük zaman birimi. Bu çalışmada Δt = 0.2 saniyedir."),
    ("Training (Eğitim)", "Pekiştirmeli öğrenmede ajanın politikasını ödül sinyallerine göre iteratif biçimde güncellemesi süreci."),
    ("Variance (Varyans)", "Bir değişkenin ortalama etrafındaki yayılımının karesi. Yüksek varyans, sonuçların tutarsız olduğuna işaret eder."),
    ("Walk-Forward Validation", "Zaman serisi verisini geçmişten geleceğe doğru bölerek eğitim ve test kümelerini oluşturan değerlendirme yöntemi. Look-ahead bias'ı önler."),
]


def build_symbols_section():
    parts = []
    # Heading1
    parts.append(heading1("SEMBOLLER VE KISALTMALAR"))
    # Intro paragraph
    parts.append(normal_para(
        "Bu bölümde çalışma boyunca kullanılan matematiksel semboller, "
        "Yunan harfleri ve kısaltmalar tanımlanmaktadır."
    ))
    # Heading2: Matematiksel Semboller
    parts.append(heading2("Matematiksel Semboller"))
    # Table
    parts.append(make_table(
        ["Sembol", "Açıklama"],
        MATH_SYMBOLS,
        [2000, 7026],
    ))
    parts.append(empty_para())
    # Heading2: Yunan Harfleri
    parts.append(heading2("Yunan Harfleri"))
    parts.append(make_table(
        ["Sembol", "Açıklama"],
        GREEK_LETTERS,
        [2000, 7026],
    ))
    parts.append(empty_para())
    # Heading2: Kısaltmalar
    parts.append(heading2("Kısaltmalar"))
    parts.append(make_table(
        ["Kısaltma", "Açıklama"],
        ABBREVIATIONS,
        [2000, 7026],
    ))
    # Page break
    parts.append(page_break())
    return "".join(parts)


def build_glossary_section():
    parts = []
    parts.append(heading1("TERİMLER SÖZLÜĞÜ"))
    parts.append(normal_para(
        "Bu sözlük, çalışmada kullanılan teknik terimleri konuya aşina "
        "olmayan okuyucular için tanımlamaktadır. Terimler alfabetik sıraya "
        "göre düzenlenmiştir."
    ))
    parts.append(make_table(
        ["Terim", "Tanım"],
        GLOSSARY,
        [2500, 6526],
    ))
    # Page break
    parts.append(page_break())
    return "".join(parts)


def main():
    xml_path = sys.argv[1] if len(sys.argv) > 1 else "unpacked_thesis/word/document.xml"

    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the GİRİŞ heading paragraph
    giris_marker = "2. GİRİŞ"
    idx = content.find(giris_marker)
    if idx < 0:
        print("ERROR: Could not find GİRİŞ heading"); sys.exit(1)

    # Find the <w:p> that contains it
    p_start = content.rfind("<w:p>", 0, idx)
    if p_start < 0:
        # Try <w:p > with attributes
        p_start = content.rfind("<w:p ", 0, idx)
    if p_start < 0:
        print("ERROR: Could not find paragraph start for GİRİŞ"); sys.exit(1)

    # Build new content to insert
    new_xml = build_symbols_section() + build_glossary_section()

    # Insert before the GİRİŞ paragraph
    updated = content[:p_start] + new_xml + content[p_start:]

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"OK: Inserted {len(new_xml)} chars before GİRİŞ in {xml_path}")
    print(f"  File size: {os.path.getsize(xml_path)} bytes")


if __name__ == "__main__":
    main()
