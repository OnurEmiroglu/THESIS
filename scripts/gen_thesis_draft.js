/**
 * Generate thesis_draft.docx — METU-style 2-column academic format
 * Usage: node scripts/gen_thesis_draft.js
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, HeadingLevel, BorderStyle, SectionType,
  ShadingType, PageBreak, TableLayoutType
} = require("docx");

// ── constants ──────────────────────────────────────────────────────
const PAGE_W = 11906;
const PAGE_H = 16838;
const MARGIN = 851;           // ~0.6 inch all sides
const COL_SPACE = 278;
const COL_W = Math.floor((PAGE_W - 2 * MARGIN - COL_SPACE) / 2); // 4963
const FONT = "Times New Roman";
const SZ_BODY = 20;           // 10pt
const SZ_TABLE = 18;          // 9pt
const SZ_TITLE_UNI = 28;     // 14pt
const SZ_TITLE_SUB = 22;     // 11pt
const SZ_TITLE_MAIN = 26;    // 13pt
const LINE_SINGLE = 240;

// ── helpers ────────────────────────────────────────────────────────

function R(text, opts = {}) {
  return new TextRun({
    text,
    font: FONT,
    size: opts.size || SZ_BODY,
    bold: !!opts.bold,
    italics: !!opts.italics,
  });
}

function Ri(text, size) {
  return R(text, { size: size || SZ_BODY, italics: true });
}

function P(children, opts = {}) {
  if (typeof children === "string") children = [R(children, opts)];
  return new Paragraph({
    children,
    alignment: opts.alignment || AlignmentType.JUSTIFIED,
    spacing: {
      before: opts.before !== undefined ? opts.before : 0,
      after: opts.after !== undefined ? opts.after : 120,
      line: opts.line || LINE_SINGLE,
    },
    indent: opts.indent || (opts.noIndent ? undefined : { firstLine: 284 }),
    ...(opts.heading ? { heading: opts.heading } : {}),
  });
}

/** Body paragraph — first-line indent 284 DXA */
function body(children, opts = {}) {
  return P(children, opts);
}

/** Body paragraph — no indent (for lists, formulas, first after heading) */
function bodyNI(children, opts = {}) {
  return P(children, { ...opts, noIndent: true });
}

function heading1(text) {
  return new Paragraph({
    children: [R(text.toUpperCase(), { size: SZ_BODY, bold: true })],
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60, line: LINE_SINGLE },
    indent: { firstLine: 0 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: "000000", space: 2 } },
  });
}

function heading2(text) {
  return new Paragraph({
    children: [R(text, { size: SZ_BODY, bold: true, italics: true })],
    heading: HeadingLevel.HEADING_2,
    alignment: AlignmentType.LEFT,
    spacing: { before: 100, after: 40, line: LINE_SINGLE },
    indent: { firstLine: 0 },
  });
}

function heading3(text) {
  return new Paragraph({
    children: [R(text, { size: SZ_BODY, bold: true })],
    heading: HeadingLevel.HEADING_3,
    alignment: AlignmentType.LEFT,
    spacing: { before: 80, after: 30, line: LINE_SINGLE },
    indent: { firstLine: 0 },
  });
}

function emptyP(n = 1) {
  const a = [];
  for (let i = 0; i < n; i++) a.push(new Paragraph({ children: [], spacing: { after: 0, line: LINE_SINGLE } }));
  return a;
}

function centP(text, size, bold) {
  return new Paragraph({
    children: [R(text, { size, bold })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 60, line: LINE_SINGLE },
  });
}

// ── table helpers (single-column width) ────────────────────────────

const thinBdr = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
const tblBorders = {
  top: thinBdr, bottom: thinBdr, left: thinBdr, right: thinBdr,
  insideHorizontal: thinBdr, insideVertical: thinBdr,
};
const cellMargin = {
  marginUnitType: WidthType.DXA,
  top: 40,
  bottom: 40,
  left: 80,
  right: 80,
};

function tCell(text, w, opts = {}) {
  const shading = opts.header
    ? { type: ShadingType.CLEAR, color: "auto", fill: "CCCCCC" }
    : undefined;
  return new TableCell({
    children: [
      new Paragraph({
        children: [R(text, {
          bold: !!opts.header,
          italics: !!opts.italic,
          size: SZ_TABLE,
        })],
        alignment: opts.align || (opts.header ? AlignmentType.CENTER : AlignmentType.LEFT),
        spacing: { before: 0, after: 0, line: LINE_SINGLE },
        indent: { firstLine: 0 },
      }),
    ],
    width: { size: w, type: WidthType.DXA },
    shading,
    margins: cellMargin,
  });
}

function mkTable(headers, rows, widths, opts = {}) {
  const totalW = widths.reduce((a, b) => a + b, 0);
  const hRow = new TableRow({
    children: headers.map((h, i) => tCell(h, widths[i], { header: true })),
    tableHeader: true,
  });
  const dRows = rows.map(r =>
    new TableRow({
      children: r.map((v, i) => tCell(v, widths[i], {
        italic: opts.italicFirstCol && i === 0,
        align: opts.centerAll ? AlignmentType.CENTER : undefined,
      })),
    })
  );
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    borders: tblBorders,
    layout: TableLayoutType.FIXED,
    rows: [hRow, ...dRows],
  });
}

// ── nomenclature data ──────────────────────────────────────────────

const MATH_SYMBOLS = [
  ["M_t", "t anındaki mid-price (orta fiyat) [para birimi]"],
  ["\u03C3", "Volatilite parametresi \u2014 mid-price'\u0131n birim zamandaki standart sapmas\u0131 [tick/\u221Asaniye]"],
  ["\u03C3_base", "Temel volatilite parametresi; Orta (M) rejim i\u00E7in referans de\u011Fer (0.8 tick/\u221Asaniye)"],
  ["\u03C3_L, \u03C3_M, \u03C3_H", "D\u00FC\u015F\u00FCk, Orta ve Y\u00FCksek rejimlere kar\u015F\u0131l\u0131k gelen volatilite de\u011Ferleri"],
  ["\u0394t", "Sim\u00FClasyon zaman ad\u0131m\u0131 b\u00FCy\u00FCkl\u00FC\u011F\u00FC (0.2 saniye)"],
  ["z", "Standart normal rassal de\u011Fi\u015Fken; z ~ N(0,1)"],
  ["\u03BB(\u03B4)", "\u03B4 tick uzakl\u0131\u011F\u0131ndaki kotasyon i\u00E7in Poisson dolum yo\u011Funlu\u011Fu [dolum/saniye]"],
  ["A", "S\u0131f\u0131r uzakl\u0131kta (\u03B4=0) temel dolum yo\u011Funlu\u011Fu (5.0 dolum/saniye)"],
  ["k", "Dolum yo\u011Funlu\u011Funun uzakl\u0131kla \u00FCstel azalma h\u0131z\u0131 (1.5 tick ba\u015F\u0131na)"],
  ["\u03B4", "Kotasyon uzakl\u0131\u011F\u0131 \u2014 bid veya ask fiyat\u0131n\u0131n mid-price'tan tick cinsinden sapmas\u0131"],
  ["\u03B4_bid", "Bid (al\u0131\u015F) kotasyonunun mid-price'tan uzakl\u0131\u011F\u0131 [tick]"],
  ["\u03B4_ask", "Ask (sat\u0131\u015F) kotasyonunun mid-price'tan uzakl\u0131\u011F\u0131 [tick]"],
  ["P_fill", "Bir zaman ad\u0131m\u0131nda en az bir dolumun ger\u00E7ekle\u015Fme olas\u0131l\u0131\u011F\u0131"],
  ["h", "Half-spread \u2014 kotasyon yar\u0131-aral\u0131\u011F\u0131 [tick]; h \u2208 {1, 2, 3, 4, 5}"],
  ["m", "Skew \u2014 asimetrik kotasyon kaymas\u0131 [tick]; m \u2208 {-2, -1, 0, +1, +2}"],
  ["q", "Envanter (inventory) \u2014 anda tutulan net pozisyon miktar\u0131 [lot]"],
  ["q_norm", "Normalize edilmi\u015F envanter; q_norm = q / inv_max_clip \u2208 [-1, +1]"],
  ["inv_max_clip", "Envanter k\u0131rpma s\u0131n\u0131r\u0131 (50 lot)"],
  ["\u03C4", "Kalan zaman fraksiyonu; \u03C4 = (T - t) / T \u2208 [0, 1]"],
  ["T", "Episode toplam ad\u0131m say\u0131s\u0131 (8000 ad\u0131m)"],
  ["R_t", "t ad\u0131m\u0131ndaki \u00F6d\u00FCl (reward)"],
  ["\u03B7", "Envanter ceza katsay\u0131s\u0131; \u03B7 = 0.001"],
  ["\u03B3", "Avellaneda-Stoikov risk aversion (riskten ka\u00E7\u0131nma) parametresi; \u03B3 = 0.01"],
  ["r", "Avellaneda-Stoikov rezervasyon fiyat\u0131"],
  ["d", "Avellaneda-Stoikov optimal yar\u0131-spread"],
  ["k_price", "Fiyat cinsinden ifade edilen yo\u011Funluk azalma parametresi; k_price = k / tick_size"],
  ["P", "Markov zinciri ge\u00E7i\u015F matrisi (3\u00D73)"],
  ["p_ii", "i. rejimin kendi kendine ge\u00E7i\u015F olas\u0131l\u0131\u011F\u0131 (k\u00F6\u015Fegen eleman)"],
  ["Sharpe", "Sharpe oran\u0131 \u2014 risk-d\u00FCzeltmeli getiri \u00F6l\u00E7\u00FCt\u00FC; Sharpe = (\u03BC/\u03C3) \u00D7 \u221A(1/\u0394t)"],
  ["inv_p99", "Mutlak envanter de\u011Ferinin 99. persantili [lot]"],
  ["equity", "Toplam varl\u0131k de\u011Feri; equity = cash + q \u00D7 M_t"],
];

const GREEK_LETTERS = [
  ["\u03B3 (gamma)", "Risk aversion parametresi (Avellaneda-Stoikov modelinde)"],
  ["\u03B7 (eta)", "Envanter ceza katsay\u0131s\u0131 (\u00F6d\u00FCl fonksiyonunda)"],
  ["\u03C3 (sigma)", "Volatilite \u2014 fiyat de\u011Fi\u015Fiminin standart sapmas\u0131"],
  ["\u03C4 (tau)", "Kalan zaman fraksiyonu"],
  ["\u03BB (lambda)", "Poisson dolum yo\u011Funlu\u011Fu"],
  ["\u03B4 (delta)", "Kotasyon uzakl\u0131\u011F\u0131 (mid-price'tan tick cinsinden sapma)"],
  ["\u03BC (mu)", "Ortalama ad\u0131m ba\u015F\u0131na PnL (Sharpe hesab\u0131nda)"],
];

const ABBREVIATIONS = [
  ["PPO", "Proximal Policy Optimization \u2014 yak\u0131nsak politika optimizasyonu algoritmas\u0131"],
  ["RL", "Reinforcement Learning \u2014 peki\u015Ftirmeli \u00F6\u011Frenme"],
  ["AS", "Avellaneda-Stoikov \u2014 klasik stokastik kontrol tabanl\u0131 piyasa yap\u0131c\u0131l\u0131\u011F\u0131 modeli"],
  ["HFT", "High-Frequency Trading \u2014 y\u00FCksek frekansl\u0131 al\u0131m-sat\u0131m"],
  ["OOS", "Out-of-Sample \u2014 modelin e\u011Fitilmedi\u011Fi veri \u00FCzerinde de\u011Ferlendirme"],
  ["WP", "Work Package \u2014 i\u015F paketi (proje a\u015Famas\u0131)"],
  ["ABM", "Arithmetic Brownian Motion \u2014 aritmetik Brownian hareketi"],
  ["RV", "Realized Volatility \u2014 ger\u00E7ekle\u015Fmi\u015F volatilite (kayan pencere ile hesaplanan)"],
  ["PnL", "Profit and Loss \u2014 kar ve zarar"],
  ["CUDA", "Compute Unified Device Architecture \u2014 NVIDIA GPU hesaplama mimarisi"],
  ["SB3", "Stable-Baselines3 \u2014 PPO implementasyonu i\u00E7in kullan\u0131lan Python k\u00FCt\u00FCphanesi"],
  ["MlpPolicy", "Multi-Layer Perceptron Policy \u2014 \u00E7ok katmanl\u0131 alg\u0131lay\u0131c\u0131 politika a\u011F\u0131"],
  ["GAE", "Generalized Advantage Estimation \u2014 genelle\u015Ftirilmi\u015F avantaj tahmini (PPO bile\u015Feni)"],
  ["L / M / H", "Low / Medium / High \u2014 D\u00FC\u015F\u00FCk / Orta / Y\u00FCksek volatilite rejimleri"],
];

const GLOSSARY = [
  ["Ablation (Ablasyon)", "Bir modelin belirli bir bile\u015Feninin \u00E7\u0131kar\u0131larak ya da devre d\u0131\u015F\u0131 b\u0131rak\u0131larak etkisinin \u00F6l\u00E7\u00FClmesi amac\u0131yla yap\u0131lan kontroll\u00FC deney. Bu \u00E7al\u0131\u015Fmada, rejim bilgisinin (use_regime=False) ve envanter ceza katsay\u0131s\u0131n\u0131n (\u03B7) etkisi ablasyon deneyleriyle \u00F6l\u00E7\u00FClm\u00FC\u015Ft\u00FCr."],
  ["Action Space (Eylem Uzay\u0131)", "Bir peki\u015Ftirmeli \u00F6\u011Frenme ajan\u0131n\u0131n her ad\u0131mda se\u00E7ebilece\u011Fi t\u00FCm olas\u0131 eylemlerin k\u00FCmesi. Bu \u00E7al\u0131\u015Fmada eylem uzay\u0131, half-spread (h) ve skew (m) de\u011Ferlerinden olu\u015Fan ayr\u0131k bir yap\u0131dad\u0131r."],
  ["Adverse Selection (Ters Se\u00E7im)", "Piyasa yap\u0131c\u0131n\u0131n bilgili yat\u0131r\u0131mc\u0131lara kar\u015F\u0131 dezavantajl\u0131 konuma d\u00FC\u015Fmesi durumu. \u00D6rne\u011Fin, fiyat h\u0131zla de\u011Fi\u015Firken eski kotasyon fiyat\u0131ndan doldurulma riski."],
  ["Agent (Ajan)", "Peki\u015Ftirmeli \u00F6\u011Frenmede, bir ortamda g\u00F6zlem yaparak karar veren ve \u00F6d\u00FCl sinyaline g\u00F6re davran\u0131\u015F\u0131n\u0131 g\u00FCncelleyen \u00F6\u011Frenen sistem."],
  ["Ask (Sat\u0131\u015F Fiyat\u0131)", "Piyasa yap\u0131c\u0131n\u0131n satmaya haz\u0131r oldu\u011Fu fiyat. Her zaman bid fiyat\u0131n\u0131n \u00FCzerindedir."],
  ["Bid (Al\u0131\u015F Fiyat\u0131)", "Piyasa yap\u0131c\u0131n\u0131n almaya haz\u0131r oldu\u011Fu fiyat. Her zaman ask fiyat\u0131n\u0131n alt\u0131ndad\u0131r."],
  ["Bid-Ask Spread", "Al\u0131\u015F ve sat\u0131\u015F fiyat\u0131 aras\u0131ndaki fark. Piyasa yap\u0131c\u0131n\u0131n temel gelir kayna\u011F\u0131d\u0131r. Bu \u00E7al\u0131\u015Fmada tick cinsinden ifade edilmektedir."],
  ["Brownian Motion (Brownian Hareketi)", "Rastlant\u0131sal y\u00FCr\u00FCy\u00FC\u015F modellerinin s\u00FCrekli-zaman limiti. Aritmetik Brownian Hareketi'nde (ABM) fiyat de\u011Fi\u015Fimleri sabit ortalama ve volatilite parametrelerine sahip normal da\u011F\u0131l\u0131mdan \u00E7ekilmektedir."],
  ["Clip (K\u0131rpma)", "Bir de\u011Ferin belirli bir aral\u0131kla s\u0131n\u0131rland\u0131r\u0131lmas\u0131 i\u015Flemi. Bu \u00E7al\u0131\u015Fmada envanter \u00B150 lot ile k\u0131rp\u0131lmaktad\u0131r."],
  ["Convergence (Yak\u0131nsama)", "Peki\u015Ftirmeli \u00F6\u011Frenme e\u011Fitiminde politikan\u0131n optimal ya da kararl\u0131 bir \u00E7\u00F6z\u00FCme ula\u015Fmas\u0131 s\u00FCreci."],
  ["Entropy Coefficient (Entropi Katsay\u0131s\u0131)", "PPO'da ke\u015Fif-s\u00F6m\u00FCr\u00FC dengesini ayarlayan hiperparametre. Y\u00FCksek de\u011Fer daha fazla rassal eylem anlam\u0131na gelir. Bu \u00E7al\u0131\u015Fmada ent_coef=0.01 kullan\u0131lm\u0131\u015Ft\u0131r."],
  ["Episode", "Peki\u015Ftirmeli \u00F6\u011Frenmede ba\u015Flang\u0131\u00E7tan biti\u015F ko\u015Fuluna kadar s\u00FCren bir tam sim\u00FClasyon ko\u015Fusu. Bu \u00E7al\u0131\u015Fmada bir episode 8000 zaman ad\u0131m\u0131ndan olu\u015Fmaktad\u0131r."],
  ["Exogenous Series (D\u0131\u015Fsal Seri)", "Modelin d\u0131\u015F\u0131nda \u00F6nceden \u00FCretilmi\u015F ve t\u00FCm stratejilere ayn\u0131 bi\u00E7imde sunulan fiyat/volatilite serisi. Adil kar\u015F\u0131la\u015Ft\u0131rma i\u00E7in kullan\u0131l\u0131r."],
  ["Fill (Dolum)", "Piyasa yap\u0131c\u0131n\u0131n kotasyon verdi\u011Fi fiyattan ger\u00E7ekle\u015Fen emir e\u015Fle\u015Fmesi. Bid taraf\u0131ndan dolum, piyasa yap\u0131c\u0131n\u0131n envanterini art\u0131r\u0131r; ask taraf\u0131ndan dolum azalt\u0131r."],
  ["Fill Rate (Dolum Oran\u0131)", "Toplam ad\u0131m say\u0131s\u0131na b\u00F6l\u00FCnen dolum say\u0131s\u0131. Piyasa yap\u0131c\u0131n\u0131n ne kadar aktif i\u015Flem yapt\u0131\u011F\u0131n\u0131n g\u00F6stergesi."],
  ["Gymnasium", "OpenAI taraf\u0131ndan geli\u015Ftirilen, peki\u015Ftirmeli \u00F6\u011Frenme ortamlar\u0131 i\u00E7in standart Python aray\u00FCz\u00FC. reset() ve step() metodlar\u0131n\u0131 tan\u0131mlar."],
  ["Half-Spread (Yar\u0131-Aral\u0131k)", "Bid veya ask fiyat\u0131n\u0131n mid-price'tan uzakl\u0131\u011F\u0131. Tam spread'in yar\u0131s\u0131. Bu \u00E7al\u0131\u015Fmada h sembol\u00FCyle g\u00F6sterilir."],
  ["Hyperparameter (Hiperparametre)", "E\u011Fitim s\u00FCrecinden \u00F6nce kullan\u0131c\u0131 taraf\u0131ndan belirlenen ve modelin nas\u0131l \u00F6\u011Frenece\u011Fini kontrol eden parametre. \u00D6rnek: learning rate, batch size, \u03B3."],
  ["Inventory (Envanter)", "Piyasa yap\u0131c\u0131n\u0131n anda elinde bulundurdu\u011Fu net pozisyon miktar\u0131. Pozitif de\u011Fer net uzun (long), negatif de\u011Fer net k\u0131sa (short) pozisyonu ifade eder."],
  ["Inventory Risk (Envanter Riski)", "Piyasa yap\u0131c\u0131n\u0131n b\u00FCy\u00FCk envanter pozisyonu tutarken fiyat hareketleri nedeniyle maruz kald\u0131\u011F\u0131 zarar riski."],
  ["Latency (Gecikme)", "Piyasa yap\u0131c\u0131n\u0131n kotasyon g\u00FCncellemesi ile piyasan\u0131n bu g\u00FCncellemeyi i\u015Flemesi aras\u0131ndaki zaman fark\u0131. Bu \u00E7al\u0131\u015Fmada latency_steps=1 ile modellenmektedir."],
  ["Limit Order Book", "Bekleme s\u0131ras\u0131ndaki t\u00FCm al\u0131\u015F ve sat\u0131\u015F emirlerinin fiyat-miktar listesi. Piyasa yap\u0131c\u0131lar bu kitaba likidite sa\u011Flar."],
  ["Lot", "Al\u0131m-sat\u0131m i\u015Flemlerinde standart birim miktar. Bu \u00E7al\u0131\u015Fmada envanter lot cinsinden ifade edilmektedir."],
  ["Markov Chain (Markov Zinciri)", "Gelecekteki durumun yaln\u0131zca mevcut duruma ba\u011Fl\u0131 oldu\u011Fu (ge\u00E7mi\u015Ften ba\u011F\u0131ms\u0131z) olas\u0131l\u0131ksal s\u00FCrec. Bu \u00E7al\u0131\u015Fmada rejim ge\u00E7i\u015Fleri i\u00E7in kullan\u0131lmaktad\u0131r."],
  ["Market Making (Piyasa Yap\u0131c\u0131l\u0131\u011F\u0131)", "Finansal piyasalarda s\u00FCrekli al\u0131\u015F ve sat\u0131\u015F kotasyonu vererek likidite sa\u011Flama faaliyeti. Piyasa yap\u0131c\u0131, spread geliri kar\u015F\u0131l\u0131\u011F\u0131nda envanter ve adverse selection riskini \u00FCstlenir."],
  ["Mid-Price", "Anl\u0131k al\u0131\u015F (bid) ve sat\u0131\u015F (ask) fiyatlar\u0131n\u0131n ortalamas\u0131. Piyasan\u0131n ger\u00E7ek de\u011Ferine en yak\u0131n fiyat tahmini."],
  ["Model Misspecification (Model Yanl\u0131\u015F Belirleme)", "Kullan\u0131lan modelin ger\u00E7ek veri \u00FCretim s\u00FCrecini tam olarak yans\u0131tmamas\u0131 durumu. \u00D6rne\u011Fin, AS modelinin sabit volatilite varsaymas\u0131."],
  ["Null Result", "Ara\u015Ft\u0131rma hipotezinin verilerce desteklenmedi\u011Fi bulgu. \u0130statistiksel olarak anlaml\u0131 bir fark g\u00F6zlemlenmemesi durumu. Bu \u00E7al\u0131\u015Fmada rejim fark\u0131ndal\u0131\u011F\u0131 hipotezi null result ile sonu\u00E7lanm\u0131\u015Ft\u0131r."],
  ["Observation Space (G\u00F6zlem Uzay\u0131)", "Ajan\u0131n her ad\u0131mda \u00E7evreden ald\u0131\u011F\u0131 bilginin vekt\u00F6r temsili. Bu \u00E7al\u0131\u015Fmada 6 boyutludur: [q_norm, \u03C3\u0302, \u03C4, r_L, r_M, r_H]."],
  ["One-Hot Encoding", "Kategorik bir de\u011Fi\u015Fkeni ikili vekt\u00F6rle temsil etme y\u00F6ntemi. \u00D6rne\u011Fin, H rejimi i\u00E7in [0, 0, 1] vekt\u00F6r\u00FC kullan\u0131l\u0131r."],
  ["Out-of-Sample (OOS)", "Modelin e\u011Fitilmedi\u011Fi, ba\u011F\u0131ms\u0131z bir veri k\u00FCmesi \u00FCzerinde yap\u0131lan de\u011Ferlendirme. Overfitting'i \u00F6nlemek i\u00E7in kullan\u0131l\u0131r."],
  ["Overfitting", "Modelin e\u011Fitim verisine a\u015F\u0131r\u0131 uyum sa\u011Flayarak yeni veride d\u00FC\u015F\u00FCk performans g\u00F6stermesi."],
  ["Percentile (Persantil)", "Veri setinin belirli bir y\u00FCzdesinin alt\u0131nda kald\u0131\u011F\u0131 de\u011Fer. \u00D6rne\u011Fin inv_p99, envanterin %99'unun bu de\u011Ferin alt\u0131nda oldu\u011Funu ifade eder."],
  ["Policy (Politika)", "Peki\u015Ftirmeli \u00F6\u011Frenmede ajan\u0131n g\u00F6zleme g\u00F6re eylem se\u00E7me stratejisi. PPO, politikay\u0131 sinir a\u011F\u0131 parametreleri ile temsil eder."],
  ["Poisson Process (Poisson S\u00FCreci)", "Olaylar\u0131n ba\u011F\u0131ms\u0131z ve sabit ortalama h\u0131zda rastlant\u0131sal ger\u00E7ekle\u015Fti\u011Fi olas\u0131l\u0131ksal s\u00FCrec. Bu \u00E7al\u0131\u015Fmada emir dolumlar\u0131 Poisson s\u00FCreci ile modellenmektedir."],
  ["PPO (Proximal Policy Optimization)", "John Schulman ve ark. (2017) taraf\u0131ndan geli\u015Ftirilen politika gradyan\u0131 tabanl\u0131 RL algoritmas\u0131. Politika g\u00FCncellemelerini s\u0131n\u0131rl\u0131 ad\u0131mlarla k\u0131s\u0131tlayarak kararl\u0131 e\u011Fitim sa\u011Flar."],
  ["Regime (Rejim)", "Piyasan\u0131n belirli bir volatilite seviyesinde bulundu\u011Fu d\u00F6nem. Bu \u00E7al\u0131\u015Fmada L (D\u00FC\u015F\u00FCk), M (Orta) ve H (Y\u00FCksek) olmak \u00FCzere \u00FC\u00E7 rejim tan\u0131mlanm\u0131\u015Ft\u0131r."],
  ["Reservation Price (Rezervasyon Fiyat\u0131)", "Avellaneda-Stoikov modelinde envanter riskini i\u00E7selle\u015Ftiren d\u00FCzeltilmi\u015F mid-price tahmini."],
  ["Reward (\u00D6d\u00FCl)", "Peki\u015Ftirmeli \u00F6\u011Frenmede ajan\u0131n her ad\u0131mda \u00E7evreden ald\u0131\u011F\u0131 say\u0131sal sinyal. Bu \u00E7al\u0131\u015Fmada R_t = \u0394Equity \u2212 \u03B7\u00B7q\u00B2 form\u00FCl\u00FC kullan\u0131lmaktad\u0131r."],
  ["Risk-Adjusted Return (Risk-D\u00FCzeltmeli Getiri)", "Getirinin, \u00FCstlenilen risk miktar\u0131na b\u00F6l\u00FCnmesiyle elde edilen performans \u00F6l\u00E7\u00FCt\u00FC. Sharpe oran\u0131 en yayg\u0131n \u00F6rnektir."],
  ["Seed (Tohum)", "Rastlant\u0131sal say\u0131 \u00FCretecinin ba\u015Flang\u0131\u00E7 de\u011Feri. Ayn\u0131 seed ile ayn\u0131 sonu\u00E7lar elde edilir; tekrarlanabilirlik i\u00E7in kullan\u0131l\u0131r."],
  ["Sharpe Ratio (Sharpe Oran\u0131)", "Birim risk ba\u015F\u0131na elde edilen fazla getiriyi \u00F6l\u00E7en performans metri\u011Fi. Sharpe = (\u03BC/\u03C3) \u00D7 \u221A(1/\u0394t) form\u00FCl\u00FCyle hesaplan\u0131r."],
  ["Skew (Asimetrik Kotasyon)", "Bid ve ask kotasyonlar\u0131n\u0131n mid-price'a g\u00F6re e\u015Fit olmayan bi\u00E7imde kayd\u0131r\u0131lmas\u0131. Pozitif skew, ask taraf\u0131n\u0131 yakla\u015Ft\u0131r\u0131r; negatif skew bid taraf\u0131n\u0131 yakla\u015Ft\u0131r\u0131r."],
  ["Stable-Baselines3 (SB3)", "PPO dahil \u00E7e\u015Fitli RL algoritmalar\u0131n\u0131n g\u00FCvenilir PyTorch implementasyonlar\u0131n\u0131 i\u00E7eren Python k\u00FCt\u00FCphanesi."],
  ["State (Durum)", "Peki\u015Ftirmeli \u00F6\u011Frenmede \u00E7evrenin belirli bir andaki tam g\u00F6zlemlenebilir temsili. Observation space ile e\u015Fanlaml\u0131 kullan\u0131lmaktad\u0131r."],
  ["Sticky Transition Matrix", "K\u00F6\u015Fegen elemanlar\u0131 y\u00FCksek (\u00F6z-ge\u00E7i\u015F olas\u0131l\u0131\u011F\u0131 b\u00FCy\u00FCk) Markov ge\u00E7i\u015F matrisi. Rejimlerin uzun s\u00FCre devam etmesini sa\u011Flar."],
  ["Stochastic Control (Stokastik Kontrol)", "Rassal s\u00FCrec\u0308ler i\u00E7eren sistemlerde optimal karar verme teorisi. Avellaneda-Stoikov modeli bu \u00E7er\u00E7eveye dayanmaktad\u0131r."],
  ["Tick", "Finansal piyasalarda fiyat\u0131n alabilece\u011Fi en k\u00FC\u00E7\u00FCk art\u0131\u015F birimi. Bu \u00E7al\u0131\u015Fmada tick_size = 0.01 para birimi olarak tan\u0131mlanm\u0131\u015Ft\u0131r."],
  ["Timestep (Zaman Ad\u0131m\u0131)", "Sim\u00FClasyonun bir sonraki duruma ge\u00E7ti\u011Fi en k\u00FC\u00E7\u00FCk zaman birimi. Bu \u00E7al\u0131\u015Fmada \u0394t = 0.2 saniyedir."],
  ["Training (E\u011Fitim)", "Peki\u015Ftirmeli \u00F6\u011Frenmede ajan\u0131n politikas\u0131n\u0131 \u00F6d\u00FCl sinyallerine g\u00F6re iteratif bi\u00E7imde g\u00FCncellemesi s\u00FCreci."],
  ["Variance (Varyans)", "Bir de\u011Fi\u015Fkenin ortalama etraf\u0131ndaki yay\u0131l\u0131m\u0131n\u0131n karesi. Y\u00FCksek varyans, sonu\u00E7lar\u0131n tutars\u0131z oldu\u011Funa i\u015Faret eder."],
  ["Walk-Forward Validation", "Zaman serisi verisini ge\u00E7mi\u015Ften gelece\u011Fe do\u011Fru b\u00F6lerek e\u011Fitim ve test k\u00FCmelerini olu\u015Fturan de\u011Ferlendirme y\u00F6ntemi. Look-ahead bias'\u0131 \u00F6nler."],
];

// ── section builders ───────────────────────────────────────────────

function buildTitlePage() {
  return [
    ...emptyP(5),
    centP("Karlsruhe Institute of Technology", SZ_TITLE_UNI, true),
    centP("Financial Engineering MSc Program\u0131", SZ_TITLE_SUB, false),
    ...emptyP(3),
    centP("Y\u00FCksek Lisans Tez Tasla\u011F\u0131", SZ_TITLE_SUB, true),
    ...emptyP(2),
    centP("Farkl\u0131 Volatilite Rejimleri Alt\u0131nda Peki\u015Ftirmeli \u00D6\u011Frenme ile", SZ_TITLE_MAIN, true),
    centP("Y\u00FCksek Frekansl\u0131 Piyasa Yap\u0131c\u0131l\u0131\u011F\u0131", SZ_TITLE_MAIN, true),
    ...emptyP(4),
    centP("Onur Emiro\u011Flu", SZ_TITLE_SUB, false),
    centP("Financial Engineering MSc Program\u0131", SZ_BODY, false),
    ...emptyP(2),
    // page break at end of title page
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

function buildNomenclature() {
  return [
    heading1("SEMBOLLER VE KISALTMALAR"),
    bodyNI("Bu b\u00F6l\u00FCmde \u00E7al\u0131\u015Fma boyunca kullan\u0131lan matematiksel semboller, Yunan harfleri ve k\u0131saltmalar tan\u0131mlanmaktad\u0131r."),

    heading2("Matematiksel Semboller"),
    mkTable(["Sembol", "A\u00E7\u0131klama"], MATH_SYMBOLS, [1200, 3763], { italicFirstCol: true }),
    ...emptyP(1),

    heading2("Yunan Harfleri"),
    mkTable(["Sembol", "A\u00E7\u0131klama"], GREEK_LETTERS, [1200, 3763], { italicFirstCol: true }),
    ...emptyP(1),

    heading2("K\u0131saltmalar"),
    mkTable(["K\u0131saltma", "A\u00E7\u0131klama"], ABBREVIATIONS, [1200, 3763], { italicFirstCol: false }),
  ];
}

function buildGlossary() {
  return [
    heading1("TER\u0130MLER S\u00D6ZL\u00DC\u011E\u00DC"),
    bodyNI("Bu s\u00F6zl\u00FCk, \u00E7al\u0131\u015Fmada kullan\u0131lan teknik terimleri konuya a\u015Fina olmayan okuyucular i\u00E7in tan\u0131mlamaktad\u0131r. Terimler alfabetik s\u0131raya g\u00F6re d\u00FCzenlenmi\u015Ftir."),
    mkTable(["Terim", "Tan\u0131m"], GLOSSARY, [1500, 3463], { italicFirstCol: false }),
  ];
}

function buildAbstract() {
  return [
    heading1("1. \u00D6ZET"),
    bodyNI([
      R("Bu \u00E7al\u0131\u015Fmada, volatilite rejim bilgisinin (D\u00FC\u015F\u00FCk/Orta/Y\u00FCksek) peki\u015Ftirmeli \u00F6\u011Frenme tabanl\u0131 piyasa yap\u0131c\u0131 ajanlar\u0131n performans\u0131na katk\u0131s\u0131 ara\u015Ft\u0131r\u0131lmaktad\u0131r. Proximal Policy Optimization (PPO) algoritmas\u0131 kullan\u0131larak iki ajan e\u011Fitilmi\u015Ftir: rejim bilgisine sahip ("),
      R("ppo_aware", { italics: true }),
      R(") ve rejim bilgisinden yoksun ("),
      R("ppo_blind", { italics: true }),
      R("). Ajanlar, Poisson var\u0131\u015F s\u00FCreçli yo\u011Funluk tabanl\u0131 dolum modeli ve Markov zinciri rejim ge\u00E7i\u015Fleri i\u00E7eren tamamen sentetik bir piyasa ortam\u0131nda de\u011Ferlendirilmi\u015Ftir. Y\u00FCr\u00FCt\u00FClen out-of-sample deney (20 ba\u011F\u0131ms\u0131z tohum, 1 milyon zaman ad\u0131m\u0131 e\u011Fitim, %70/%30 walk-forward b\u00F6l\u00FCnmesi), her iki PPO varyant\u0131n\u0131n da Sharpe oran\u0131 a\u00E7\u0131s\u0131ndan klasik referans stratejilerini (Avellaneda-Stoikov ve naif sabit-spread) yakla\u015F\u0131k 6\u20137 kat ge\u00E7ti\u011Fini ortaya koymaktad\u0131r. Buna kar\u015F\u0131n, rejim bilgisinin PPO performans\u0131na net bir katk\u0131 sa\u011Flad\u0131\u011F\u0131 hipotezi istatistiksel olarak desteklenmemi\u015Ftir: "),
      R("ppo_aware", { italics: true }),
      R(", yaln\u0131zca 20 tohumun 9\u2019unda "),
      R("ppo_blind", { italics: true }),
      R("\u2019\u0131 geride b\u0131rakm\u0131\u015Ft\u0131r. Davran\u0131\u015Fsal analiz, "),
      R("ppo_aware", { italics: true }),
      R(" ajan\u0131n\u0131n rejime \u00F6zg\u00FC farkl\u0131 eylem da\u011F\u0131l\u0131mlar\u0131 geli\u015Ftirdi\u011Fini (\u00F6zellikle d\u00FC\u015F\u00FCk volatilite rejiminde daha geni\u015F spread ve farkl\u0131 skew \u00F6r\u00FCnt\u00FCleri) g\u00F6stermektedir; ancak bu davran\u0131\u015Fsal farkl\u0131la\u015Fma performans avantaj\u0131na d\u00F6n\u00FC\u015Fmemektedir. \u00C7al\u0131\u015Fma, sentetik veri ile kontroll\u00FC ortam tasar\u0131m\u0131n\u0131n de\u011Ferini, PPO\u2019nun envanter risk y\u00F6netimindeki \u00FCst\u00FCnl\u00FC\u011F\u00FCn\u00FC ve rejim fark\u0131ndal\u0131\u011F\u0131 hipotezi i\u00E7in \u201Cnull result\u201D\u0131n yay\u0131nlanabilir bir akademik bulgu olu\u015Fturdu\u011Funu g\u00F6stermektedir."),
    ]),
    ...emptyP(1),
    bodyNI([
      R("Anahtar kelimeler: ", { bold: true }),
      R("piyasa yap\u0131c\u0131l\u0131\u011F\u0131, peki\u015Ftirmeli \u00F6\u011Frenme, PPO, volatilite rejimleri, Avellaneda-Stoikov, Poisson dolum modeli, out-of-sample de\u011Ferlendirme"),
    ]),
  ];
}

function buildIntroduction() {
  return [
    heading1("2. G\u0130R\u0130\u015E"),
    bodyNI("Piyasa yap\u0131c\u0131l\u0131\u011F\u0131 (market making), finansal piyasalarda likidite sa\u011Flayan ve s\u00FCrekli olarak hem al\u0131\u015F (bid) hem de sat\u0131\u015F (ask) kotasyonu veren ajanlar\u0131n stratejik davran\u0131\u015F\u0131n\u0131 inceleyen bir aland\u0131r. Piyasa yap\u0131c\u0131lar, spread geliri elde etmeye \u00E7al\u0131\u015F\u0131rken olumsuz fiyat hareketlerine maruz kalan envanter riskini de y\u00F6netmek zorundad\u0131r. Bu denge, \u00F6zellikle volatilitenin de\u011Fi\u015Fken oldu\u011Fu y\u00FCksek frekansl\u0131 piyasalarda kritik \u00F6nem ta\u015F\u0131maktad\u0131r."),
    body("Klasik yakla\u015F\u0131mlar aras\u0131nda Avellaneda ve Stoikov (2008) taraf\u0131ndan geli\u015Ftirilen stokastik kontrol \u00E7er\u00E7evesi \u00F6ne \u00E7\u0131kmaktad\u0131r. Bu model, envanter riskini rezervasyon fiyat\u0131 kavram\u0131yla i\u00E7selle\u015Ftirerek optimal bid-ask spread\u2019ini analitik olarak t\u00FCretmektedir. Ancak bu yakla\u015F\u0131m, sabit bir volatilite varsay\u0131m\u0131na dayanmakta ve piyasa rejimlerindeki de\u011Fi\u015Fimlere uyum sa\u011Flayamamaktad\u0131r."),
    body("Son y\u0131llarda peki\u015Ftirmeli \u00F6\u011Frenme (RL) y\u00F6ntemleri, dinamik piyasa ko\u015Fullar\u0131na uyum sa\u011Flayabilen ajan tasar\u0131m\u0131 i\u00E7in umut verici bir alternatif olarak \u00F6ne \u00E7\u0131km\u0131\u015Ft\u0131r. PPO gibi politika gradyan\u0131 algoritmalar\u0131, \u00F6zellikle s\u00FCrekli durum uzaylar\u0131 ve karma\u015F\u0131k \u00F6d\u00FCl yap\u0131lar\u0131na sahip finansal ortamlarda ba\u015Far\u0131yla uygulanm\u0131\u015Ft\u0131r."),
    body([
      R("Bu \u00E7al\u0131\u015Fman\u0131n temel ara\u015Ft\u0131rma sorusu \u015Fudur: "),
      R("Volatilite rejim bilgisine (D\u00FC\u015F\u00FCk/Orta/Y\u00FCksek) eri\u015Fimi olan bir PPO ajan\u0131, bu bilgiden yoksun olan e\u015Fde\u011Ferine k\u0131yasla daha iyi performans sergiler mi?", { italics: true }),
    ]),
    body("Bu soruyu yan\u0131tlamak i\u00E7in a\u015Fa\u011F\u0131daki katk\u0131lar sunulmaktad\u0131r:"),
    bodyNI("(1) Markov zinciri rejim ge\u00E7i\u015Fleri ve Poisson tabanl\u0131 dolum modeli i\u00E7eren kontroll\u00FC bir sentetik piyasa ortam\u0131 tasarlanm\u0131\u015Ft\u0131r.", { before: 40, indent: { left: 284 } }),
    bodyNI("(2) Rejim fark\u0131ndal\u0131\u011F\u0131 ablasyonu ger\u00E7ekle\u015Ftirilmi\u015F; ppo_aware ve ppo_blind ajanlar\u0131 20 ba\u011F\u0131ms\u0131z tohum ve walk-forward out-of-sample protokol\u00FC ile kar\u015F\u0131la\u015Ft\u0131r\u0131lm\u0131\u015Ft\u0131r.", { before: 0, indent: { left: 284 } }),
    bodyNI("(3) Eylem da\u011F\u0131l\u0131m\u0131 analizi ile ajanlar\u0131n rejime \u00F6zg\u00FC davran\u0131\u015Fsal farkl\u0131la\u015Fmas\u0131 incelenmi\u015Ftir.", { before: 0, indent: { left: 284 } }),
  ];
}

function buildTheory() {
  return [
    heading1("3. TEOR\u0130 VE METODOLOJ\u0130"),

    // 3.1
    heading2("3.1 Piyasa Modeli"),
    bodyNI("Piyasa fiyat\u0131, ayr\u0131k zamanl\u0131 aritmetik Brownian hareketi (ABM) ile modellenmektedir:"),
    bodyNI([Ri("M"), R("_{t+1} = "), Ri("M"), R("_t + \u03C3_r \u00B7 \u221A(\u0394t) \u00B7 "), Ri("z"), R(",    "), Ri("z"), R(" ~ N(0,1)")], { alignment: AlignmentType.CENTER, before: 40, after: 40 }),
    bodyNI([
      R("Burada "), Ri("M"), R("_t mid-price, "), Ri("\u03C3"), R("_r rejime ba\u011Fl\u0131 volatilite parametresi (ticks/\u221Asaniye cinsinden), \u0394t = 0.2 saniye zaman ad\u0131m\u0131 b\u00FCy\u00FCkl\u00FC\u011F\u00FCd\u00FCr. Ba\u015Flang\u0131\u00E7 fiyat\u0131 "),
      Ri("M"), R("_0 = 100.0, tick b\u00FCy\u00FCkl\u00FC\u011F\u00FC 0.01\u2019dir."),
    ]),
    body([
      R("Temel volatilite parametresi \u03C3_base = 0.8 tick olarak belirlenmi\u015F; \u00FC\u00E7 rejim i\u00E7in \u00E7arpanlar [0.6, 1.0, 1.8] olarak tan\u0131mlanm\u0131\u015Ft\u0131r. Buna g\u00F6re "),
      Ri("\u03C3_L"), R(" = 0.48, "),
      Ri("\u03C3_M"), R(" = 0.80, "),
      Ri("\u03C3_H"), R(" = 1.44 tick/\u221Asaniye de\u011Ferleri elde edilmektedir."),
    ]),

    // 3.2
    heading2("3.2 Dolum Modeli"),
    bodyNI("Emir dolumlar\u0131, yo\u011Funluk tabanl\u0131 Poisson s\u00FCreci ile modellenmektedir. Delta tick cinsinden ifade edildi\u011Finde, dolum yo\u011Funlu\u011Fu:"),
    bodyNI([Ri("\u03BB(\u03B4)"), R(" = "), Ri("A"), R(" \u00B7 exp(\u2212"), Ri("k"), R(" \u00B7 "), Ri("\u03B4"), R(")")], { alignment: AlignmentType.CENTER, before: 40, after: 40 }),
    bodyNI([
      R("form\u00FCl\u00FCyle hesaplanmaktad\u0131r. Burada "), Ri("A"), R(" = 5.0 (delta=0\u2019daki temel yo\u011Funluk, dolum/saniye) ve "),
      Ri("k"), R(" = 1.5 (tick ba\u015F\u0131na \u00FCstel azalma) parametreleridir. Bir zaman ad\u0131m\u0131nda en az bir dolumun ger\u00E7ekle\u015Fme olas\u0131l\u0131\u011F\u0131:"),
    ]),
    bodyNI([Ri("P"), R("_fill = 1 \u2212 exp(\u2212"), Ri("\u03BB"), R(" \u00B7 \u0394t)")], { alignment: AlignmentType.CENTER, before: 40, after: 40 }),
    bodyNI("olarak verilmektedir. Hem bid hem ask taraf\u0131 i\u00E7in ba\u011F\u0131ms\u0131z Bernoulli denemeleri ger\u00E7ekle\u015Ftirilmektedir."),
    body("Gecikme modeli (latency_steps = 1), ajan\u0131n kotasyon hesaplamas\u0131nda bir \u00F6nceki ad\u0131m\u0131n mid-price de\u011Ferini kullanmas\u0131na yol a\u00E7makta; bu durum ters se\u00E7im (adverse selection) riskini i\u00E7selle\u015Ftirmektedir. Komisyon \u00FCcreti her i\u015Flem i\u00E7in 0.2 baz puan olarak uygulanmaktad\u0131r."),

    // 3.3
    heading2("3.3 Rejim Modeli"),
    bodyNI("Volatilite rejimleri, \u00FC\u00E7 durumlu (L: D\u00FC\u015F\u00FCk, M: Orta, H: Y\u00FCksek) birinci derece Markov zinciri ile \u00FCretilmektedir. Ge\u00E7i\u015F matrisi yap\u0131\u015Fkan (sticky) olacak \u015Fekilde tasarlanm\u0131\u015Ft\u0131r:"),
    bodyNI("P = [[0.9967, 0.0023, 0.0010], [0.0042, 0.9917, 0.0041], [0.0010, 0.0030, 0.9960]]", { alignment: AlignmentType.CENTER, before: 40, after: 40 }),
    bodyNI("Beklenen rejim s\u00FCreleri s\u0131ras\u0131yla L: ~300, M: ~120, H: ~250 zaman ad\u0131m\u0131d\u0131r. Bu yap\u0131\u015Fkanl\u0131k, kayan ger\u00E7ekle\u015Fmi\u015F volatilite (rolling realized volatility \u2014 RV) ile rejim tespitinin m\u00FCmk\u00FCn olmas\u0131n\u0131 sa\u011Flamaktad\u0131r."),
    body([
      R("Rejim tespiti i\u00E7in RV pencere boyutu 50 ad\u0131m, \u0131s\u0131nma s\u00FCresi (warmup) 1000 ad\u0131m olarak belirlenmi\u015Ftir. E\u015Fik de\u011Ferleri \u0131s\u0131nma d\u00F6neminin 33. ve 66. persentillerinden kalibre edilmektedir. Ger\u00E7ek zamanl\u0131 tespitte look-ahead bias engellenmi\u015Ftir; "),
      Ri("regime_hat"),
      R(" yaln\u0131zca ge\u00E7mi\u015F veriden hesaplanmaktad\u0131r. Elde edilen tespit do\u011Frulu\u011Fu %60.7\u2019dir (rastgele s\u0131n\u0131r: %33.3)."),
    ]),

    // 3.4
    heading2("3.4 Gymnasium Ortam\u0131"),
    bodyNI("OpenAI Gymnasium uyumlu MMEnv ortam\u0131 olu\u015Fturulmu\u015Ftur. G\u00F6zlem uzay\u0131 6 boyutludur:"),
    bodyNI([
      R("obs = ["), Ri("q"), R("_norm, "), Ri("\u03C3\u0302"), R("_t, "), Ri("\u03C4"), R(", "), Ri("r_L"), R(", "), Ri("r_M"), R(", "), Ri("r_H"), R("]"),
    ], { alignment: AlignmentType.CENTER, before: 40, after: 40 }),
    bodyNI([
      R("Burada "), Ri("q"), R("_norm = inv / inv_max_clip envanter normalizasyonu, "),
      Ri("\u03C3\u0302"), R("_t kayan ger\u00E7ekle\u015Fmi\u015F volatilite, "),
      Ri("\u03C4"), R(" = (T\u2212t)/T kalan zaman fraksiyonu, "),
      Ri("r_L"), R("/"), Ri("r_M"), R("/"), Ri("r_H"),
      R(" ise rejim one-hot kodlamas\u0131d\u0131r (ppo_blind i\u00E7in hepsi s\u0131f\u0131r)."),
    ]),
    body("Eylem uzay\u0131 MultiDiscrete([5, 5]) \u015Feklinde tan\u0131mlanm\u0131\u015Ft\u0131r:"),
    bodyNI([Ri("h"), R("_idx \u2208 {0,1,2,3,4} \u2192 "), Ri("h"), R(" = h_idx + 1 tick (half-spread)")], { before: 40, indent: { left: 284 } }),
    bodyNI([Ri("m"), R("_idx \u2208 {0,1,2,3,4} \u2192 "), Ri("m"), R(" = m_idx \u2212 2 tick (skew)")], { before: 0, indent: { left: 284 } }),
    bodyNI([Ri("delta_bid"), R(" = max(1, "), Ri("h"), R(" + "), Ri("m"), R(")")], { before: 0, indent: { left: 284 } }),
    bodyNI([Ri("delta_ask"), R(" = max(1, "), Ri("h"), R(" \u2212 "), Ri("m"), R(")")], { before: 0, indent: { left: 284 } }),
    body("\u00D6d\u00FCl fonksiyonu \u015Fu \u015Fekilde tan\u0131mlanm\u0131\u015Ft\u0131r:"),
    bodyNI([Ri("R"), R("_t = (equity_t \u2212 equity_{t\u22121}) \u2212 "), Ri("\u03B7"), R(" \u00B7 inv_t\u00B2")], { alignment: AlignmentType.CENTER, before: 40, after: 40 }),
    bodyNI([R("Burada "), Ri("\u03B7"), R(" = 0.001 envanter ceza katsay\u0131s\u0131d\u0131r (\u03B7 ablasyonu ile optimize edilmi\u015Ftir).")]),

    // 3.5
    heading2("3.5 Referans Stratejiler"),
    heading3("3.5.1 Naif Sabit-Spread Stratejisi"),
    bodyNI([
      R("Her zaman ad\u0131m\u0131nda simetrik sabit half-spread uygulanmaktad\u0131r: "),
      Ri("delta_bid"), R(" = "), Ri("delta_ask"), R(" = "), Ri("h"),
      R(" = 2 tick. Envanter fark\u0131ndal\u0131\u011F\u0131 veya skew mekanizmas\u0131 i\u00E7ermemektedir."),
    ]),

    heading3("3.5.2 Avellaneda-Stoikov Stratejisi"),
    bodyNI("Rezervasyon fiyat\u0131 ve yar\u0131-spread \u015Fu form\u00FCllerle hesaplanmaktad\u0131r:"),
    bodyNI([Ri("r"), R(" = mid \u2212 "), Ri("q"), R(" \u00B7 "), Ri("\u03B3"), R(" \u00B7 "), Ri("\u03C3\u00B2"), R(" \u00B7 "), Ri("\u03C4")], { alignment: AlignmentType.CENTER, before: 40, after: 20 }),
    bodyNI([Ri("d"), R(" = \u00BD \u00B7 "), Ri("\u03B3"), R(" \u00B7 "), Ri("\u03C3\u00B2"), R(" \u00B7 "), Ri("\u03C4"), R(" + (1/"), Ri("\u03B3"), R(") \u00B7 ln(1 + "), Ri("\u03B3"), R("/"), Ri("k"), R("_price)")], { alignment: AlignmentType.CENTER, before: 0, after: 40 }),
    bodyNI([
      R("Burada "), Ri("\u03B3"), R(" = 0.01 risk aversion parametresi, "),
      Ri("k"), R("_price = "), Ri("k"), R("_ticks / tick_size fiyat cinsinden yo\u011Funluk azalma parametresidir. Delta de\u011Ferleri [1, 25] tick aral\u0131\u011F\u0131nda k\u0131rp\u0131lmaktad\u0131r."),
    ]),

    // 3.6
    heading2("3.6 PPO E\u011Fitimi ve De\u011Ferlendirme Protokol\u00FC"),
    bodyNI("Stable-Baselines3 k\u00FCt\u00FCphanesi kullan\u0131larak PPO e\u011Fitimi ger\u00E7ekle\u015Ftirilmi\u015Ftir. Hiperparametreler:"),

    mkTable(
      ["Parametre", "De\u011Fer"],
      [
        ["total_timesteps", "1.000.000"],
        ["learning_rate", "0.0003"],
        ["n_steps", "2048"],
        ["batch_size", "256"],
        ["n_epochs", "10"],
        ["gamma", "0.999"],
        ["gae_lambda", "0.95"],
        ["clip_range", "0.2"],
        ["ent_coef", "0.01"],
      ],
      [2400, 2563],
    ),
    ...emptyP(1),
    body("Her seed i\u00E7in episode uzunlu\u011Fu 8000 ad\u0131m olup walk-forward b\u00F6l\u00FCnmesi %70/%30 (train: 5600, test: 2400 ad\u0131m) \u015Feklinde uygulanm\u0131\u015Ft\u0131r. De\u011Ferlendirme yaln\u0131zca test b\u00F6l\u00FCm\u00FCnden ger\u00E7ekle\u015Ftirilmektedir. Toplam 20 ba\u011F\u0131ms\u0131z tohum kullan\u0131lm\u0131\u015Ft\u0131r (seeds: 1\u201320). E\u011Fitim GPU \u00FCzerinde ger\u00E7ekle\u015Ftirilmi\u015Ftir (NVIDIA CUDA, PyTorch 2.6.0+cu124)."),
  ];
}

function buildResults() {
  // widths for 7-col table to fit single column: 4963 total
  const w7 = [900, 600, 600, 600, 750, 750, 763];
  // widths for 6-col table to fit single column: 4963 total
  const w6 = [900, 780, 600, 850, 850, 983];

  return [
    heading1("4. SONU\u00C7LAR VE TARTI\u015EMA"),

    heading2("4.1 Ana Deney Sonu\u00E7lar\u0131 (20 Tohum, OOS)"),
    bodyNI([R("Tablo 1.", { bold: true }), R(" Out-of-Sample Performans \u00D6zeti (20 Tohum, Ortalama \u00B1 Std)")], { before: 40, after: 40 }),

    mkTable(
      ["Strateji", "Ort. Eq.", "Std", "Sharpe", "inv_p99", "Fill R."],
      [
        ["AS",        "5.05", "4.72", "0.105", "29.95", "0.444"],
        ["Naif",      "4.49", "3.49", "0.126", "21.20", "0.119"],
        ["ppo_aware", "4.10", "0.78", "0.715", "2.00",  "0.236"],
        ["ppo_blind", "4.42", "0.71", "0.740", "2.05",  "0.232"],
      ],
      w6,
      { centerAll: true },
    ),
    ...emptyP(1),
    bodyNI("Ana bulgular \u00FC\u00E7 ba\u015Fl\u0131k alt\u0131nda \u00F6zetlenebilir:"),

    bodyNI([R("Birinci bulgu \u2014 PPO\u2019nun Sharpe \u00DCst\u00FCnl\u00FC\u011F\u00FC: ", { bold: true }),
      R("Her iki PPO varyant\u0131 da Sharpe oran\u0131 a\u00E7\u0131s\u0131ndan klasik referans stratejileri kar\u015F\u0131s\u0131nda belirgin \u00FCst\u00FCnl\u00FCk sergilemi\u015Ftir. "),
      R("ppo_aware", { italics: true }), R(" ortalama Sharpe = 0.715, "),
      R("ppo_blind", { italics: true }), R(" ise 0.740 de\u011Feri elde ederken, AS i\u00E7in bu de\u011Fer 0.105, naif strateji i\u00E7in ise 0.126 olarak \u00F6l\u00E7\u00FClm\u00FC\u015Ft\u00FCr. Bu fark yakla\u015F\u0131k 6\u20137 kat b\u00FCy\u00FCkl\u00FC\u011F\u00FCndedir ve temel mekanizmas\u0131 envanter kontrol\u00FCd\u00FCr: PPO varyantlar\u0131 inv_p99 \u2248 2 tick d\u00FCzeyinde \u00E7al\u0131\u015F\u0131rken, AS ve naif stratejiler s\u0131ras\u0131yla 29.95 ve 21.20 de\u011Ferlerine ula\u015Fmaktad\u0131r. Y\u00FCksek envanter, k\u00FCm\u00FClatif de\u011Ferleme volatilitesini art\u0131rarak Sharpe oran\u0131n\u0131 d\u00FC\u015F\u00FCrmektedir."),
    ], { before: 80 }),

    bodyNI([R("\u0130kinci bulgu \u2014 Null Sonu\u00E7: Rejim Fark\u0131ndal\u0131\u011F\u0131 Hipotezi Desteklenmedi: ", { bold: true }),
      R("ppo_aware", { italics: true }), R(", 20 tohumun yaln\u0131zca 9\u2019unda "),
      R("ppo_blind", { italics: true }), R("\u2019\u0131 geride b\u0131rakm\u0131\u015Ft\u0131r. Bu oran istatistiksel olarak anlaml\u0131 bir fark olu\u015Fturmamaktad\u0131r ve rejim bilgisinin performans \u00FCzerinde net bir katk\u0131 sa\u011Flad\u0131\u011F\u0131 hipotezini desteklememektedir. Ortalama equity de\u011Ferlerindeki fark da ihmal edilebilir d\u00FCzeydedir: "),
      R("ppo_aware", { italics: true }), R(" = 4.10 \u00B1 0.78, "),
      R("ppo_blind", { italics: true }), R(" = 4.42 \u00B1 0.71."),
    ], { before: 80 }),

    body("Bu null sonu\u00E7 i\u00E7in \u00FC\u00E7 a\u00E7\u0131klay\u0131c\u0131 hipotez \u00F6ne s\u00FCr\u00FClmektedir:"),
    bodyNI([
      R("(a) G\u00F6zlem uzay\u0131nda "), Ri("\u03C3\u0302_t"),
      R(" de\u011Feri halihaz\u0131rda mevcut oldu\u011Fundan, one-hot rejim kodlamas\u0131 "),
      Ri("\u03C3\u0302_t"), R("\u2019den t\u00FCretilmi\u015F bilgiyi yedekli bi\u00E7imde sunmakta ve marjinal katk\u0131 sa\u011Flamamaktad\u0131r."),
    ], { indent: { left: 284 } }),
    bodyNI("(b) \u00D6d\u00FCl fonksiyonu rejime \u00F6zg\u00FC davran\u0131\u015F\u0131 do\u011Frudan te\u015Fvik etmedi\u011Finden, rejim bilgisini performansa d\u00F6n\u00FC\u015Ft\u00FCrmek i\u00E7in sinyal yetersiz kalmaktad\u0131r.", { indent: { left: 284 } }),
    bodyNI("(c) %60.7 d\u00FCzeyindeki rejim tespit do\u011Frulu\u011Fu, yanl\u0131\u015F s\u0131n\u0131fland\u0131rmalar\u0131n avantaj yerine g\u00FCr\u00FClt\u00FC \u00FCretmesine neden olmaktad\u0131r.", { indent: { left: 284 } }),

    bodyNI([R("\u00DC\u00E7\u00FCnc\u00FC bulgu \u2014 PPO Varyans Avantaj\u0131: ", { bold: true }),
      R("PPO varyantlar\u0131n\u0131n equity std de\u011Ferleri (0.71\u20130.78) AS (4.72) ve naif (3.49) stratejilerine k\u0131yasla belirgin bi\u00E7imde d\u00FC\u015F\u00FCkt\u00FCr. Bu durum, PPO\u2019nun yaln\u0131zca daha y\u00FCksek Sharpe oran\u0131 de\u011Fil, ayn\u0131 zamanda daha tutarl\u0131 ve g\u00FCvenilir bir performans profili sundu\u011Funa i\u015Faret etmektedir."),
    ], { before: 80 }),

    // 4.2
    heading2("4.2 Eylem Analizi (Davran\u0131\u015Fsal Farkl\u0131la\u015Fma)"),
    bodyNI([R("Tablo 2.", { bold: true }), R(" Rejim Baz\u0131nda Eylem Da\u011F\u0131l\u0131m\u0131 (Ortalama \u00B1 Std, 20 Tohum)")], { before: 40, after: 40 }),

    mkTable(
      ["Strateji", "Rejim", "Ort.h", "Std h", "Ort.m", "Std m", "P(h=5)"],
      [
        ["AS",        "L", "1.00", "0.00", "\u22120.01", "0.02", "0.000"],
        ["AS",        "M", "1.00", "0.00", "\u22120.02", "0.03", "0.000"],
        ["AS",        "H", "1.00", "0.00", "\u22120.02", "0.03", "0.000"],
        ["Naif",      "L", "2.00", "0.00", "0.00",  "0.00", "0.000"],
        ["Naif",      "M", "2.00", "0.00", "0.00",  "0.00", "0.000"],
        ["Naif",      "H", "2.00", "0.00", "0.00",  "0.00", "0.000"],
        ["ppo_aware", "L", "1.43", "0.63", "\u22120.05", "0.22", "0.000"],
        ["ppo_aware", "M", "1.68", "0.72", "\u22120.01", "0.25", "0.008"],
        ["ppo_aware", "H", "1.74", "0.71", "0.01",  "0.22", "0.000"],
        ["ppo_blind", "L", "1.39", "0.47", "\u22120.03", "0.24", "0.000"],
        ["ppo_blind", "M", "1.42", "0.41", "0.00",  "0.23", "0.000"],
        ["ppo_blind", "H", "1.60", "0.42", "\u22120.01", "0.17", "0.000"],
      ],
      w7,
      { centerAll: true },
    ),
    ...emptyP(1),
    bodyNI([
      R("ppo_aware", { italics: true }),
      R(" ajan\u0131nda rejime g\u00F6re eylem farkl\u0131la\u015Fmas\u0131 s\u0131n\u0131rl\u0131d\u0131r. Ortalama half-spread de\u011Ferleri L/M/H rejimlerinde s\u0131ras\u0131yla "),
      Ri("h"), R(" = 1.43 / 1.68 / 1.74 olup, farklar dar bir bantta kalmaktad\u0131r. Skew ortalamalar\u0131 da "),
      Ri("m"), R(" = \u22120.05, \u22120.01, +0.01 seviyelerinde s\u0131f\u0131ra yak\u0131nd\u0131r."),
    ]),

    body([
      R("Buna kar\u015F\u0131n "),
      R("ppo_blind", { italics: true }),
      R(" i\u00E7in de benzer \u00F6l\u00E7ekte bir desen g\u00F6zlenmektedir ("),
      Ri("h"), R(" \u2248 1.39\u20131.60, "),
      Ri("m"), R(" \u2248 \u22120.03\u20130.00). Dolay\u0131s\u0131yla g\u00FCncel eylem analizi, rejim bilgisinin eylem d\u00FCzeyinde g\u00FC\u00E7l\u00FC ve belirgin bir ayr\u0131\u015Fma \u00FCretmedi\u011Fini g\u00F6stermektedir."),
    ]),
  ];
}

function buildConclusion() {
  return [
    heading1("5. SONU\u00C7"),
    bodyNI("Bu \u00E7al\u0131\u015Fma, volatilite rejimleri alt\u0131nda peki\u015Ftirmeli \u00F6\u011Frenme tabanl\u0131 piyasa yap\u0131c\u0131l\u0131\u011F\u0131n\u0131 ara\u015Ft\u0131rmaktad\u0131r. Temel bulgular \u015Fu \u015Fekilde \u00F6zetlenebilir:"),

    body("Birincisi, her iki PPO varyant\u0131 da Sharpe oran\u0131 a\u00E7\u0131s\u0131ndan Avellaneda-Stoikov ve naif referans stratejilerini yakla\u015F\u0131k 6\u20137 kat ge\u00E7mi\u015Ftir. Bu \u00FCst\u00FCnl\u00FC\u011F\u00FCn temel kayna\u011F\u0131, PPO\u2019nun envanter riskini etkin bi\u00E7imde y\u00F6netmesi ve inv_p99 \u2248 2 tick d\u00FCzeyinde tutmas\u0131d\u0131r.", { before: 80 }),

    body([
      R("\u0130kincisi, rejim fark\u0131ndal\u0131\u011F\u0131 hipotezi istatistiksel olarak desteklenmemi\u015Ftir. "),
      R("ppo_aware", { italics: true }),
      R(", 20 tohumun yaln\u0131zca 9\u2019unda "),
      R("ppo_blind", { italics: true }),
      R("\u2019\u0131 geride b\u0131rakm\u0131\u015F; ortalama performans fark\u0131 ihmal edilebilir d\u00FCzeyde kalm\u0131\u015Ft\u0131r. Bu null sonu\u00E7 i\u00E7in en g\u00FC\u00E7l\u00FC a\u00E7\u0131klama, g\u00F6zlem uzay\u0131nda halihaz\u0131rda bulunan "),
      Ri("\u03C3\u0302_t"),
      R(" de\u011Ferinin rejim bilgisini \u00F6rt\u00FCk olarak i\u00E7ermesi ve one-hot rejim kodlamas\u0131n\u0131n yedekli bilgi sunmas\u0131d\u0131r."),
    ], { before: 80 }),

    body([
      R("\u00DC\u00E7\u00FCnc\u00FCs\u00FC, "),
      R("ppo_aware", { italics: true }),
      R(" ve "),
      R("ppo_blind", { italics: true }),
      R(" aras\u0131ndaki eylem da\u011F\u0131l\u0131mlar\u0131 g\u00FCncel veride birbirine yak\u0131n seyretmektedir. Bu durum, ana fark\u0131n rejime \u00F6zg\u00FC eylem ayr\u0131\u015Fmas\u0131ndan ziyade genel envanter kontrol\u00FCnden kaynakland\u0131\u011F\u0131n\u0131 d\u00FC\u015F\u00FCnd\u00FCrmektedir."),
    ], { before: 80 }),

    body("Gelecek \u00E7al\u0131\u015Fmalar kapsam\u0131nda \u015Fu y\u00F6nler \u00F6nerilmektedir:", { before: 120 }),
    bodyNI("(1) Rejim parametrelerini g\u00F6zlem uzay\u0131ndan \u00E7\u0131kararak bilgi fazlal\u0131\u011F\u0131n\u0131 giderme ve pure ablation tasar\u0131m\u0131.", { before: 40, indent: { left: 284 } }),
    bodyNI("(2) Rejime ko\u015Fullu \u00F6d\u00FCl tasar\u0131m\u0131 \u2014 y\u00FCksek volatilite rejiminde envanter cezas\u0131n\u0131n art\u0131r\u0131lmas\u0131 gibi mekanizmalar.", { indent: { left: 284 } }),
    bodyNI("(3) Skew penalty ablasyonu (c=0 kontrol grubu dahil) ile eylem d\u00FCzeyinde d\u00FCzenlile\u015Ftirmenin sistematik de\u011Ferlendirmesi.", { indent: { left: 284 } }),
    bodyNI("(4) Model yanl\u0131\u015F belirleme (model misspecification) benchmark\u2019\u0131 \u2014 AS parametrelerinin rejime ba\u011F\u0131ml\u0131 k\u0131l\u0131nmas\u0131.", { indent: { left: 284 } }),
  ];
}

function buildReferences() {
  const refs = [
    "[1] Avellaneda, M., & Stoikov, S. (2008). High-frequency trading in a limit order book. Quantitative Finance, 8(3), 217-224.",
    "[2] Schulman, J., Wolski, F., Dhariwal, P., Radford, A., & Klimov, O. (2017). Proximal policy optimization algorithms. arXiv preprint arXiv:1707.06347.",
    "[3] Spooner, T., Fearnley, J., Savani, R., & Koukorinis, A. (2018). Market making via reinforcement learning. In Proceedings of the 17th International Conference on Autonomous Agents and MultiAgent Systems (pp. 434-442).",
    "[4] Raffin, A., Hill, A., Gleave, A., Kanervisto, A., Ernestus, M., & Dormann, N. (2021). Stable-baselines3: Reliable reinforcement learning implementations. Journal of Machine Learning Research, 22(268), 1-8.",
    "[5] Cont, R. (2001). Empirical characteristics of asset returns: Stylized facts. Quantitative Finance, 1(2), 223-236.",
    "[6] Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series and the business cycle. Econometrica, 57(2), 357-384.",
  ];
  return [
    heading1("KAYNAKLAR"),
    ...refs.map(r => bodyNI(r, { before: 0, after: 60, indent: { left: 284, hanging: 284 } })),
  ];
}

// ── assemble document ──────────────────────────────────────────────

const pageDef = {
  size: { width: PAGE_W, height: PAGE_H, orientation: "portrait" },
  margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
};

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: FONT, size: SZ_BODY },
        paragraph: {
          spacing: { before: 0, after: 120, line: LINE_SINGLE },
        },
      },
      heading1: {
        run: { font: FONT, size: SZ_BODY, bold: true, allCaps: true },
        paragraph: {
          spacing: { before: 120, after: 60, line: LINE_SINGLE },
          alignment: AlignmentType.CENTER,
        },
      },
      heading2: {
        run: { font: FONT, size: SZ_BODY, bold: true, italics: true },
        paragraph: { spacing: { before: 100, after: 40, line: LINE_SINGLE } },
      },
      heading3: {
        run: { font: FONT, size: SZ_BODY, bold: true },
        paragraph: { spacing: { before: 80, after: 30, line: LINE_SINGLE } },
      },
    },
  },
  sections: [
    // Section 1: Title page — single column
    {
      properties: {
        page: pageDef,
        // No column property = single column
      },
      children: [
        ...buildTitlePage(),
        // Section-break paragraph: triggers NEXT_PAGE break and switches to 2-col
        new Paragraph({
          children: [],
          spacing: { after: 0, line: LINE_SINGLE },
          section: {
            type: SectionType.NEXT_PAGE,
            page: pageDef,
            column: { space: COL_SPACE, count: 2 },
          },
        }),
      ],
    },
    // Section 2: All content — 2 columns
    {
      properties: {
        page: pageDef,
        column: { space: COL_SPACE, count: 2 },
      },
      children: [
        ...buildNomenclature(),
        ...buildGlossary(),
        ...buildAbstract(),
        ...buildIntroduction(),
        ...buildTheory(),
        ...buildResults(),
        ...buildConclusion(),
        ...buildReferences(),
      ],
    },
  ],
});

// ── write to disk ──────────────────────────────────────────────────
const outName = process.env.THESIS_OUT || "thesis_draft.docx";
const outPath = path.resolve(__dirname, "..", "manuscript", outName);
Packer.toBuffer(doc).then(buf => {
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, buf);
  console.log("OK  ->", outPath, `(${buf.length} bytes)`);
}).catch(err => {
  console.error("FAIL:", err);
  process.exit(1);
});
