# Layout Aware Text Extraction

Pipeline OCR end-to-end yang mampu membaca **posisi, ukuran font, warna, dan alignment** teks dari gambar secara otomatis, lalu merender ulang hasilnya sebagai **file HTML interaktif** yang tampilannya menyerupai gambar asli — lengkap dengan toolbar edit layaknya aplikasi pengolah kata.

---

## Daftar Isi

- [Gambaran Umum](#gambaran-umum)
- [Arsitektur](#arsitektur)
- [Tech Stack](#tech-stack)
- [Struktur Proyek](#struktur-proyek)
- [Prasyarat](#prasyarat)
- [Instalasi](#instalasi)
- [Konfigurasi](#konfigurasi)
- [Menjalankan Aplikasi](#menjalankan-aplikasi)
- [Argumen CLI](#argumen-cli)
- [Struktur Output](#struktur-output)
- [Format Data JSON](#format-data-json)
- [Toolbar HTML Interaktif](#toolbar-html-interaktif)
- [Keputusan Desain](#keputusan-desain)
- [Troubleshooting](#troubleshooting)

---

## Gambaran Umum

Alat ini membangun representasi teks yang kaya secara visual dari sebuah gambar (flyer, slide, poster, brosur). Setiap teks yang ditemukan diekstrak bersama informasi posisi, ukuran, warna, dan gaya tipografinya, kemudian dirender ulang sebagai overlay di atas gambar background pada sebuah halaman HTML.

Kemampuan utama:

- Ekstraksi teks dari gambar menggunakan dua engine OCR (PaddleOCR & EasyOCR)
- Pra-pemrosesan gambar otomatis: upscale resolusi + CLAHE contrast enhancement
- Koreksi teks OCR otomatis: normalisasi spasi, perbaikan karakter salah, penggantian frasa
- Klasifikasi elemen: membedakan *hero title*, *top title area*, dan teks isi
- Estimasi gaya visual per elemen: font size, font weight, warna teks, warna background, alignment
- Filter noise cerdas: mengabaikan logo, elemen kontras rendah, dan karakter sampah
- Dua mode cover teks: CSS backdrop blur atau OpenCV inpainting TELEA
- Output HTML interaktif: teks dapat diedit langsung di browser
- Output JSON terstruktur: data elemen siap pakai untuk keperluan downstream
- Mode debug: bounding box dan binary mask tersimpan sebagai gambar terpisah

---

## Arsitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                          │
│                                                                 │
│  Gambar Input (.jpg / .png / .bmp / .webp)                      │
│      │                                                          │
│      ▼                                                          │
│  preprocess_for_ocr()                                           │
│      ├── Upscale ×2 (jika lebar < 1600px, INTER_CUBIC)          │
│      └── CLAHE contrast enhancement (channel V, HSV)           │
│      │                                                          │
│      ▼                                                          │
│  run_ocr()                                                      │
│      ├── PaddleOCR (default) ──► DB detection + angle cls      │
│      └── EasyOCR (fallback)  ──► multi-lang [en, id]           │
│      │                                                          │
│      ▼                                                          │
│  filter_noise() ──────────────► Hapus logo, noise, low contrast │
│      │                                                          │
│      ▼                                                          │
│  merge_same_line() ───────────► Gabungkan kata dalam satu baris │
│      │                          + deduplicate via IoU           │
│      │                                                          │
│      ▼                                                          │
│  enrich_style() ──────────────► Font size, weight, warna,      │
│      ├── K-means (k=2)          alignment per elemen            │
│      ├── Border median                                          │
│      └── Dimensi bounding box                                   │
│      │                                                          │
│      ├──(css mode)────────────► Gambar asli sebagai background  │
│      └──(inpaint mode)────────► Background di-inpaint TELEA     │
│      │                                                          │
│      ▼                                                          │
│  generate_html() ─────────────► HTML interaktif + toolbar edit  │
│      │                                                          │
│      ▼                                                          │
│  Output: *_css_cover.html + *_background.png + *_data.json      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Komponen | Teknologi | Keterangan |
|---|---|---|
| Bahasa | Python 3.9+ | Single-file, tanpa dependensi internal |
| Computer Vision | OpenCV (cv2) | Pra-pemrosesan, masking, inpainting TELEA |
| Numerik | NumPy | Operasi piksel, K-means, median |
| OCR (default) | PaddleOCR | DB detection, angle classification, akurasi tinggi |
| OCR (fallback) | EasyOCR | Mendukung Bahasa Indonesia + Inggris |
| Output Frontend | HTML + CSS + Vanilla JS | Toolbar edit floating, contenteditable |
| Serialisasi | JSON (NumpyEncoder) | Tipe data NumPy otomatis dikonversi |

---

## Struktur Proyek

```
layout-aware-extraction/
├── layout_aware_extraction.py   ← Script utama (single-file, semua logika di sini)
├── input/                       ← Letakkan gambar input di sini (buat manual)
├── output/                      ← Hasil output (dibuat otomatis saat dijalankan)
│   ├── nama_file_css_cover.html
│   ├── nama_file_background.png
│   ├── nama_file_data.json
│   ├── nama_file_debug.png      ← hanya dengan flag --debug
│   ├── nama_file_mask.png       ← hanya dengan flag --debug
│   ├── _tmp/
│   │   └── nama_file_ocr_input.png
│   └── results.json
└── README.md
```

Seluruh logika berada dalam satu file Python. Tidak ada modul tambahan atau konfigurasi eksternal yang diperlukan.

---

## Prasyarat

- Python 3.9 atau lebih baru
- OpenCV dan NumPy
- Minimal satu OCR engine: PaddleOCR (direkomendasikan) atau EasyOCR

---

## Instalasi

**1. Clone repository**

```bash
git clone https://github.com/username/layout-aware-extraction.git
cd layout-aware-extraction
```

**2. Buat dan aktifkan virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

**3. Install dependensi dasar**

```bash
pip install opencv-python numpy
```

**4. Install OCR engine**

PaddleOCR (CPU, direkomendasikan):
```bash
pip install paddlepaddle paddleocr
```

EasyOCR:
```bash
pip install easyocr
```

> Untuk GPU, ganti `paddlepaddle` dengan `paddlepaddle-gpu` dan sesuaikan versi CUDA.

---

## Konfigurasi

Tidak diperlukan file konfigurasi eksternal. Semua parameter diatur sebagai konstanta di bagian atas `layout_aware_extraction.py`:

| Konstanta | Default | Keterangan |
|---|---|---|
| `MIN_CONF` | `0.38` | Batas minimum confidence OCR |
| `UPSCALE_IF_WIDTH_BELOW` | `1600` | Gambar dengan lebar di bawah nilai ini di-upscale sebelum OCR |
| `OCR_UPSCALE` | `2.0` | Faktor pengali resolusi saat upscale |
| `MIN_FONT_SIZE` | `10` | Ukuran font minimum output (px) |
| `MAX_FONT_SIZE` | `90` | Ukuran font maksimum untuk teks biasa (px) |
| `MIN_LOCAL_CONTRAST` | `18.0` | Batas kontras minimum; elemen di bawah nilai ini + confidence rendah dibuang |
| `LINE_HEIGHT` | `1.12` | Nilai line-height CSS pada HTML output |
| `IGNORE_TOP_RIGHT_LOGO` | `True` | Abaikan teks di area logo pojok kanan atas |
| `LOGO_X_START_RATIO` | `0.78` | Titik awal horizontal area logo (rasio terhadap lebar gambar) |
| `LOGO_Y_END_RATIO` | `0.18` | Titik akhir vertikal area logo (rasio terhadap tinggi gambar) |
| `FONT_FAMILY` | Poppins, Montserrat, ... | Stack font CSS untuk HTML output |

---

## Menjalankan Aplikasi

Letakkan gambar di folder `./input`, lalu jalankan:

```bash
python layout_aware_extraction.py
```

Buka file `./output/nama_file_css_cover.html` di browser untuk melihat hasilnya.

---

## Argumen CLI

| Argumen | Default | Keterangan |
|---|---|---|
| `--input` | `./input` | Path ke file gambar tunggal atau folder berisi gambar |
| `--output` | `./output` | Folder tujuan hasil output |
| `--engine` | `paddle` | Engine OCR: `paddle` atau `easyocr` |
| `--cover-mode` | `css` | Mode cover teks: `css` (backdrop blur) atau `inpaint` (OpenCV TELEA) |
| `--debug` | *(tidak aktif)* | Simpan gambar debug (bounding box) dan binary mask |
| `--clean-output` | *(tidak aktif)* | Hapus seluruh isi folder output sebelum dijalankan |

**Contoh penggunaan:**

```bash
# Proses satu file
python layout_aware_extraction.py --input ./poster.png

# Proses folder dengan EasyOCR
python layout_aware_extraction.py --input ./input --engine easyocr

# Mode inpaint + debug + output bersih
python layout_aware_extraction.py --cover-mode inpaint --debug --clean-output

# Kombinasi lengkap
python layout_aware_extraction.py \
  --input ./input \
  --output ./output \
  --engine paddle \
  --cover-mode inpaint \
  --debug \
  --clean-output
```

---

## Struktur Output

Untuk setiap gambar input bernama `nama_file.jpg`, dihasilkan:

```
output/
├── nama_file_css_cover.html    ← File utama: tampilan HTML interaktif yang dapat diedit
├── nama_file_background.png    ← Gambar background (asli atau ter-inpaint)
├── nama_file_data.json         ← Data elemen teks terstruktur
├── nama_file_debug.png         ← (--debug) Bounding box merah tiap elemen
├── nama_file_mask.png          ← (--debug) Binary mask area teks
├── _tmp/
│   └── nama_file_ocr_input.png ← Gambar setelah pra-pemrosesan (input ke OCR)
└── results.json                ← Ringkasan path semua output sesi ini
```

---

## Format Data JSON

Setiap elemen dalam array `elements` pada file `*_data.json`:

```json
{
  "text":        "Talent Development",
  "x":           142,
  "y":           380,
  "w":           310,
  "h":           38,
  "confidence":  0.961,
  "contrast":    47.5,
  "font_size":   39,
  "line_height": 1.12,
  "font_weight": "700",
  "color":       "#ffffff",
  "cover_color": "#1a3a5c",
  "align":       "center",
  "bg_lum":      28.4
}
```

| Field | Tipe | Keterangan |
|---|---|---|
| `text` | string | Teks hasil OCR setelah koreksi |
| `x`, `y` | int | Koordinat pojok kiri atas bounding box (piksel) |
| `w`, `h` | int | Lebar dan tinggi bounding box (piksel) |
| `confidence` | float | Skor kepercayaan OCR (0.0 – 1.0) |
| `contrast` | float | Kontras lokal area teks (persentil 95 − 5 grayscale) |
| `font_size` | int | Estimasi ukuran font (px) |
| `line_height` | float | Nilai line-height CSS |
| `font_weight` | string | `"500"`, `"600"`, atau `"700"` |
| `color` | string | Warna teks dalam format hex |
| `cover_color` | string | Warna background cover dalam format hex |
| `align` | string | `"left"` atau `"center"` |
| `bg_lum` | float | Luminansi rata-rata background (0 – 255) |

---

## Toolbar HTML Interaktif

File HTML output dilengkapi toolbar edit **floating popup** yang muncul otomatis saat mengklik elemen teks.

| Fitur | Keterangan |
|---|---|
| Font family | Inter, Arial, Georgia, Trebuchet MS, Courier New, Poppins, Montserrat |
| Ukuran font | Input angka + tombol `−` / `+`, rentang 6 – 250 px |
| **Bold** | Tombol toolbar atau `Ctrl+B` |
| *Italic* | Tombol toolbar atau `Ctrl+I` |
| Underline | Tombol toolbar atau `Ctrl+U` |
| ~~Strikethrough~~ | Tombol toolbar |
| Warna teks | Color picker dengan preview bar warna |
| Alignment | Rata kiri / tengah / kanan / kiri-kanan |

Semua teks dapat diedit langsung di browser via atribut `contenteditable`. Toolbar tersembunyi otomatis saat klik di luar elemen aktif.

---

## Keputusan Desain

**Single-file architecture**

Seluruh pipeline — pra-pemrosesan, OCR, filter, merge, estimasi gaya, hingga generasi HTML — berada dalam satu file Python. Ini menyederhanakan deployment dan distribusi; tidak ada dependency internal yang perlu dikelola.

**Hybrid OCR: PaddleOCR sebagai default, EasyOCR sebagai fallback**

PaddleOCR dipilih sebagai default karena akurasinya lebih tinggi, terutama untuk teks dengan variasi sudut dan ukuran. Jika PaddleOCR tidak terpasang atau gagal dijalankan, EasyOCR diaktifkan secara otomatis tanpa intervensi pengguna. EasyOCR juga secara eksplisit mendukung Bahasa Indonesia (`['en', 'id']`).

**Estimasi gaya berbasis piksel, bukan metadata**

Font size, warna teks, dan warna background diestimasi langsung dari piksel gambar menggunakan K-means clustering (k=2) dan analisis border median — bukan dari metadata file. Pendekatan ini bekerja pada gambar raster apapun tanpa memerlukan informasi tambahan.

**Tiga kelas elemen teks**

Elemen diklasifikasikan menjadi tiga kelas — *hero title*, *top title area*, dan teks biasa — karena masing-masing memerlukan kalkulasi font size yang berbeda. Hero title menggunakan rumus berbasis luas area dan panjang teks; top title menggunakan perkalian langsung dari tinggi bounding box dengan faktor yang lebih besar; teks biasa menggunakan faktor konservatif dengan batas minimum dan maksimum yang ketat.

**Dua mode cover: CSS vs Inpaint**

Mode `css` (default) lebih cepat karena tidak memodifikasi piksel gambar — teks asli hanya "ditutup" oleh `<div>` berwarna dengan efek backdrop blur. Mode `inpaint` menghasilkan background yang lebih bersih secara visual menggunakan algoritma TELEA dari OpenCV, namun membutuhkan waktu pemrosesan lebih lama karena setiap piksel teks harus direkonstruksi dari piksel sekitarnya.

**CLAHE untuk pra-pemrosesan kontras**

Contrast Limited Adaptive Histogram Equalization (CLAHE) diterapkan pada channel Value (V) ruang warna HSV — bukan grayscale langsung — agar peningkatan kontras tidak mengubah saturasi warna. Ini memastikan estimasi warna downstream tetap akurat.

---

## Troubleshooting

**PaddleOCR gagal saat instalasi**
```bash
pip install paddlepaddle==2.6.0
pip install paddleocr==2.7.3
```

**Teks tidak terdeteksi / hasil terlalu sedikit**

Kurangi `MIN_CONF` (misal `0.25`) dan/atau `MIN_LOCAL_CONTRAST` (misal `10.0`) di bagian konstanta. Aktifkan `--debug` untuk melihat bounding box hasil deteksi mentah.

**Terlalu banyak noise terdeteksi sebagai teks**

Naikkan `MIN_CONF` (misal `0.55`) dan/atau `MIN_LOCAL_CONTRAST` (misal `25.0`).

**Ukuran font di HTML tidak proporsional**

Sesuaikan `MIN_FONT_SIZE` dan `MAX_FONT_SIZE`. Untuk hero title, ubah faktor pengali `1.80` pada fungsi `estimate_font_size()`.

**Logo atau watermark ikut terdeteksi**

Pastikan `IGNORE_TOP_RIGHT_LOGO = True`. Sesuaikan `LOGO_X_START_RATIO` dan `LOGO_Y_END_RATIO` sesuai posisi logo pada gambar target Anda.

**Format gambar tidak terbaca**

Format yang didukung: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`. Format lain perlu dikonversi terlebih dahulu.
