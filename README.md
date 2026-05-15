# Multimodal RAG — Bank Mandiri 2025

> Pipeline Retrieval Augmented Generation end-to-end yang mampu memproses dokumen PDF multimodal (teks, tabel, gambar, infografis) dan menjawab pertanyaan berbasis dokumen melalui REST API.

---

## Daftar Isi

- [Gambaran Umum](#gambaran-umum)
- [Arsitektur](#arsitektur)
- [Tech Stack](#tech-stack)
- [Struktur Project](#struktur-project)
- [Prasyarat](#prasyarat)
- [Instalasi](#instalasi)
- [Konfigurasi](#konfigurasi)
- [Menjalankan Aplikasi](#menjalankan-aplikasi)
- [Referensi API](#referensi-api)
- [Hasil Evaluasi](#hasil-evaluasi)
- [Keputusan Desain](#keputusan-desain)

---

## Gambaran Umum

Sistem ini membangun sebuah knowledge base dari dokumen PDF Laporan Bank Mandiri 2025 yang mengandung teks, tabel, dan gambar/infografis. Pengguna dapat mengajukan pertanyaan dalam Bahasa Indonesia, dan sistem akan memberikan jawaban akurat beserta referensi halaman sumber.

**Kemampuan utama:**
- Ekstraksi teks dan tabel dari PDF secara struktural
- Interpretasi gambar, chart, dan infografis menggunakan Vision Language Model
- Knowledge injection manual untuk konten visual yang kompleks
- Semantic search berbasis vector similarity
- Answer synthesis menggunakan LLM dengan LangChain orchestration
- Metadata halaman sumber di setiap response untuk keperluan debugging

---

## Arsitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                          │
│                                                                 │
│  Upload PDF                                                     │
│      │                                                          │
│      ▼                                                          │
│  parser.py ──── PyMuPDF ──────► Teks per halaman                |
│      │                                                          │
│      ├──── Groq Vision ────────► Deskripsi gambar/chart         |
│      │     (llama-3.2-11b)                                      │
│      │                                                          │
│      └──── Manual Injection ───► Deskripsi infografis kompleks  |
│                                  (hal. 8 & 9)                   │
│      │                                                          │
│      ▼                                                          │
│  ingest.py ─── LangChain ──────► RecursiveCharacterTextSplitter |
│                TextSplitter      chunk_size=1000, overlap=200   │
│      │                                                          │
│      ▼                                                          │
│  Gemini Embedding ─────────────► Vector                         |
│  (gemini-embedding-001)                                         │
│      │                                                          │
│      ▼                                                          │
│  ChromaDB ─────────────────────► Persistent vector store        |
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      QUERY PIPELINE                             │
│                                                                 │
│  Pertanyaan Pengguna                                            │
│      │                                                          │
│      ▼                                                          │
│  Gemini Embedding ─────────────► Query vector                   |
│      │                                                          │
│      ▼                                                          │
│  ChromaDB ─────────────────────► Top-K chunk paling relevan     |
│  Similarity Search               + metadata (halaman sumber)    |
│      │                                                          │
│      ▼                                                          │
│  LangChain LCEL Chain                                           │
│      PromptTemplate                                             │
│      │ ChatGroq (llama-3.3-70b)                                 |
│      │ StrOutputParser                                          │
│      │                                                          │
│      ▼                                                          │
│  Response: jawaban + halaman sumber + jumlah chunk              |
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Komponen | Teknologi | Keterangan |
|---|---|---|
| API Framework | FastAPI | REST API dengan Swagger UI otomatis |
| Orchestration | LangChain (LCEL) | PromptTemplate, ChatGroq, StrOutputParser |
| PDF Parser | PyMuPDF (fitz) | Ekstraksi teks dan gambar dari PDF |
| Vision Model | Groq — Llama 3.2 11B Vision | Mendeskripsikan gambar/chart dari PDF |
| Embedding | Google Gemini — gemini-embedding-001 | Semantic embedding Bahasa Indonesia |
| Vector Database | ChromaDB | Penyimpanan vector lokal yang persisten |
| LLM | Groq — Llama 3.3 70B Versatile | Pembuatan jawaban |
| Bahasa Pemrograman | Python 3.12 | | Bahasa utama untuk pengembangan sistem |

---

## Struktur Project

```
rag-mandiri/
├── app/
│   ├── main.py         # FastAPI — definisi endpoint & penanganan request
│   ├── parser.py       # Parsing PDF — ekstraksi teks, deskripsi gambar, manual injection
│   ├── ingest.py       # Pipeline ingestion — chunking, embedding, penyimpanan ChromaDB
│   ├── query.py        # Pipeline query — retrieval, LangChain chain, pembuatan jawaban
│   └── config.py       # Konfigurasi terpusat & environment variables
│
├── vectorstore/        # Penyimpanan ChromaDB (dibuat otomatis saat pertama ingest)
├── uploads/            # File PDF yang diupload (dibuat otomatis)
├── .env                # API key (tidak di-commit ke version control)
├── .env.example        # Template environment variables
├── .gitignore          # Daftar file/folder yang diabaikan Git
└── requirements.txt    # Daftar dependency Python project
```

---

## Prasyarat

- Python 3.10 atau lebih baru
- Google Gemini API key — [ai.google.dev](https://ai.google.dev)
- Groq API key — [console.groq.com](https://console.groq.com)

---

## Instalasi

**1. Clone repository**
```bash
git clone https://github.com/Ahjaris/Multimodal-RAG-Mandiri.git
cd Multimodal-RAG-Mandiri
```

**2. Buat dan aktifkan virtual environment**
```bash
python -m venv nama_venv

# Windows
nama_venv\Scripts\activate

# Mac/Linux
source nama_venv/bin/activate
```

**3. Install semua dependensi**
```bash
pip install -r requirements.txt
```

---

## Konfigurasi

Buat file `.env` di root folder berdasarkan `.env.example`:

```env
GOOGLE_API_KEY=isi_google_gemini_api_key_kamu
GROQ_API_KEY=isi_groq_api_key_kamu
```

Parameter lain dapat dikonfigurasi di `app/config.py`:

```python
VECTORSTORE_PATH = "./vectorstore"   # lokasi penyimpanan ChromaDB
UPLOAD_PATH = "./uploads"            # lokasi file yang diupload
COLLECTION_NAME = "mandiri_2025"     # nama collection ChromaDB
CHUNK_SIZE = 1000                    # ukuran chunk dalam karakter
CHUNK_OVERLAP = 200                  # overlap antar chunk
```

---

## Menjalankan Aplikasi

**Jalankan server:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Buka Swagger UI untuk mencoba endpoint:**
```
http://127.0.0.1:8000/docs
```

---

## Referensi API

### `GET /`
Endpoint pengecekan status server.

**Response:**
```json
{
  "status": "ok",
  "message": "RAG API aktif"
}
```

---

### `POST /ingest`
Upload dan proses file PDF menjadi knowledge base.

**Request:** `multipart/form-data`

| Field | Tipe | Keterangan |
|---|---|---|
| file | File | File PDF yang akan diproses |

**Response:**
```json
{
  "status": "success",
  "total_pages": 9,
  "total_chunks": 41
}
```

**Error:**
- `400` — File bukan format PDF

**Proses yang terjadi:**
1. PDF disimpan ke folder `uploads/`
2. Teks diekstrak per halaman menggunakan PyMuPDF
3. Gambar/chart dideskripsikan menggunakan Groq Vision
4. Deskripsi manual diinjeksi untuk halaman dengan infografis kompleks
5. Teks dipotong menjadi chunk menggunakan `RecursiveCharacterTextSplitter` (1000 karakter, overlap 200)
6. Setiap chunk di-embed menggunakan Gemini `gemini-embedding-001`
7. Vector beserta metadata disimpan ke ChromaDB

---

### `POST /query`
Ajukan pertanyaan berdasarkan dokumen yang sudah diingesti.

**Request body:**
```json
{
  "question": "Apa saja peran Unit Pelindungan Nasabah?",
  "top_k": 5
}
```

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| question | string | wajib diisi | Pertanyaan dalam Bahasa Indonesia |
| top_k | integer | 5 | Jumlah chunk yang diambil saat retrieval |

**Response:**
```json
{
  "question": "Apa saja peran Unit Pelindungan Nasabah?",
  "answer": "Unit Pelindungan Nasabah memiliki beberapa peran...",
  "source_pages": [7, 8],
  "chunks_used": 5
}
```

| Field | Keterangan |
|---|---|
| answer | Jawaban dalam Bahasa Indonesia berdasarkan dokumen |
| source_pages | Nomor halaman tempat jawaban ditemukan |
| chunks_used | Jumlah chunk yang digunakan sebagai context |

**Error:**
- `400` — Pertanyaan kosong

**Proses yang terjadi:**
1. Pertanyaan di-embed menggunakan Gemini `gemini-embedding-001`
2. Similarity search dilakukan di ChromaDB untuk mengambil top-K chunk
3. Chunk yang ditemukan disusun menjadi context
4. LangChain LCEL chain dijalankan: `PromptTemplate | ChatGroq | StrOutputParser`
5. Jawaban beserta halaman sumber dikembalikan ke pengguna

---

## Hasil Evaluasi

Berikut hasil pengujian dengan 6 pertanyaan evaluasi dari dokumen:

**1. Peran Unit Pelindungan Nasabah (Sumber: Hal. 7)**
```
Pertanyaan : Apa saja peran Unit Pelindungan Nasabah menurut peraturan POJK No. 22 Tahun 2023?
Jawaban    : Unit Pelindungan Nasabah memiliki 9 peran, yaitu: 1. Mensosialisasikan prinsip
             Pelindungan Nasabah kepada seluruh Pegawai Bank. 2. Mengoordinasikan perencanaan
             dan pelaksanaan kepatuhan Bank... (9 poin lengkap)
Halaman    : [7, 8]  
```

**2. Jam Penagihan (Sumber: Hal. 7)**
```
Pertanyaan : Jika Bank Mandiri menggunakan jasa Perusahaan Jasa Penagihan, apakah penagihan
             boleh dilakukan pada jam 21.00?
Jawaban    : Tidak boleh. Penagihan hanya dapat dilakukan pada pukul 08.00 sampai dengan
             pukul 20.00 waktu wilayah domisili debitur.
Halaman    : [5, 7]  
```

**3. Kredit Sektor Tambang & Konstruksi (Sumber: Hal. 4)**
```
Pertanyaan : Berapa nominal dan persentase pertumbuhan kredit di sektor tambang dan konstruksi?
Jawaban    : Sektor tambang: Nominal Rp11.614.853 triliun, pertumbuhan 7,98%.
             Sektor konstruksi: Nominal Rp8.264.848 triliun, pertumbuhan 8,27%.
Halaman    : [3, 4, 5]  
```

**4. Komposisi DPK 2024 & 2025 (Sumber: Hal. 6)**
```
Pertanyaan : Sebutkan persentase komposisi dana pihak ketiga (DPK) di Bank Mandiri
             pada tahun 2024 dan 2025?
Jawaban    : Tahun 2024: Deposito Berjangka 20,57%, Tabungan 39,31%, Giro 40,12%.
             Tahun 2025: Deposito Berjangka 29,11%, Tabungan 36,66%, Giro 34,23%.
Halaman    : [1, 2, 3, 6]  
```

**5. Alur Penanganan Pengaduan (Sumber: Hal. 8)**
```
Pertanyaan : Bagaimana alur penanganan nasabah di Bank Mandiri jika terdapat laporan pengaduan?
Jawaban    : 1. MENYAMPAIKAN PENGADUAN: Nasabah menyampaikan pengaduan melalui media masa,
             telepon, email, media sosial, atau surat cabang. 2. VERIFIKASI & INPUT: Bank
             menerima, memverifikasi, dan menginput pengaduan... (7 langkah lengkap)
Halaman    : [7, 8, 9]  
```

**6. Saluran Pengaduan (Sumber: Hal. 9)**
```
Pertanyaan : Apa saja saluran pengaduan yang disediakan oleh Bank Mandiri?
Jawaban    : Bank Mandiri menyediakan: 1. Mandiri Call 14000 (24 jam). 2. Akun X: mandiricare
             dan @bankmandiri. 3. WhatsApp MITA: 0811-8414-000. 4. Website bankmandiri.co.id...
             (9 saluran lengkap)
Halaman    : [7, 8, 9]  
```

---

## Keputusan Desain

**Arsitektur Hybrid — Custom Parser + LangChain Orchestration**

Parser PDF dibuat secara custom menggunakan PyMuPDF dan Groq Vision karena Document Loader bawaan LangChain tidak mendukung ekstraksi gambar dari PDF. Bagian retrieval dan pembuatan jawaban menggunakan LangChain LCEL agar orchestration lebih terstruktur dan setiap komponen mudah diganti tanpa mengubah keseluruhan kode.

**Knowledge Injection untuk Infografis Kompleks**

Halaman 8 (alur penanganan pengaduan) dan halaman 9 (daftar saluran pengaduan) menggunakan deskripsi manual karena infografis yang terdiri dari panah, kotak, dan elemen visual terpisah tidak dapat dideskripsikan secara akurat oleh vision model secara otomatis. Pendekatan ini memastikan akurasi jawaban untuk pertanyaan yang sumbernya berupa infografis.

**Gemini untuk Embedding, Groq untuk LLM**

Gemini `gemini-embedding-001` dipilih untuk embedding karena kualitas semantic search-nya baik untuk Bahasa Indonesia. Groq `llama-3.3-70b-versatile` dipilih untuk LLM karena gratis, cepat, dan memiliki rate limit yang wajar sehingga cocok untuk keperluan pengembangan dan demo.

**Chunk Size 1000 dengan Overlap 200**

Nilai ini dipilih sebagai keseimbangan antara konteks yang cukup per chunk dan jumlah chunk yang tidak terlalu banyak. Overlap 200 karakter memastikan informasi yang berada di batas antar chunk tidak hilang saat teks dipotong.
