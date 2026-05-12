# Multimodal RAG — Bank Mandiri 2025

> End-to-end Retrieval Augmented Generation pipeline yang mampu memproses dokumen PDF multimodal (teks, tabel, gambar, infografis) dan menjawab pertanyaan berbasis dokumen melalui REST API.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Evaluation Results](#evaluation-results)
- [Design Decisions](#design-decisions)

---

## Overview

Sistem ini membangun sebuah knowledge base dari dokumen PDF Laporan Bank Mandiri 2025 yang mengandung teks, tabel, dan gambar/infografis. User dapat mengajukan pertanyaan dalam Bahasa Indonesia, dan sistem akan memberikan jawaban akurat beserta referensi halaman sumber.

**Kemampuan utama:**
- Ekstraksi teks dan tabel dari PDF secara struktural
- Interpretasi gambar, chart, dan infografis menggunakan Vision Language Model
- Knowledge injection manual untuk konten visual yang kompleks
- Semantic search berbasis vector similarity
- Answer synthesis menggunakan LLM dengan LangChain orchestration
- Source page metadata di setiap response untuk traceability

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                          │
│                                                                 │
│  PDF Upload                                                     │
│      │                                                          │
│      ▼                                                          │
│  parser.py ──── PyMuPDF ──────► Teks per halaman               │
│      │                                                          │
│      ├──── Groq Vision ────────► Deskripsi gambar/chart        │
│      │     (llama-3.2-11b)                                      │
│      │                                                          │
│      └──── Manual Injection ───► Deskripsi infografis kompleks │
│                                  (hal. 8 & 9)                   │
│      │                                                          │
│      ▼                                                          │
│  ingest.py ─── LangChain ──────► RecursiveCharacterTextSplitter│
│                TextSplitter      chunk_size=1000, overlap=200   │
│      │                                                          │
│      ▼                                                          │
│  Gemini Embedding ─────────────► Vector (1536 dim)             │
│  (gemini-embedding-001)                                         │
│      │                                                          │
│      ▼                                                          │
│  ChromaDB ─────────────────────► Persistent vector store       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      QUERY PIPELINE                             │
│                                                                 │
│  User Question                                                  │
│      │                                                          │
│      ▼                                                          │
│  Gemini Embedding ─────────────► Query vector                  │
│      │                                                          │
│      ▼                                                          │
│  ChromaDB ─────────────────────► Top-K similar chunks          │
│  Similarity Search               + metadata (source_pages)     │
│      │                                                          │
│      ▼                                                          │
│  LangChain LCEL Chain                                           │
│  PromptTemplate                                                 │
│      │ llm (ChatGroq)                                           │
│      │ StrOutputParser                                          │
│      │                                                          │
│      ▼                                                          │
│  Response: answer + source_pages + chunks_used                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Teknologi | Keterangan |
|---|---|---|
| API Framework | FastAPI | REST API dengan auto-generated Swagger UI |
| Orchestration | LangChain (LCEL) | PromptTemplate, ChatGroq, StrOutputParser |
| PDF Parser | PyMuPDF (fitz) | Ekstraksi teks dan gambar dari PDF |
| Vision Model | Groq — Llama 3.2 11B Vision | Describe gambar/chart dari PDF |
| Embedding | Google Gemini — gemini-embedding-001 | Semantic embedding Bahasa Indonesia |
| Vector Database | ChromaDB | Persistent local vector store |
| LLM | Groq — Llama 3.3 70B Versatile | Answer synthesis |
| Runtime | Python 3.12 | |

---

## Project Structure

```
rag-mandiri/
├── app/
│   ├── main.py         # FastAPI app — endpoint definitions & request handling
│   ├── parser.py       # PDF parsing — text extraction, vision description, manual injection
│   ├── ingest.py       # Ingestion pipeline — chunking, embedding, ChromaDB storage
│   ├── query.py        # Query pipeline — retrieval, LangChain chain, answer synthesis
│   └── config.py       # Centralized configuration & environment variables
│
├── vectorstore/        # ChromaDB persistent storage (auto-generated on first ingest)
├── uploads/            # Uploaded PDF files (auto-generated)
├── .env                # API keys (not committed to version control)
├── .env.example        # Template for environment variables
├── .gitignore
└── requirements.txt
```

---

## Prerequisites

- Python 3.10+
- Google Gemini API key — [ai.google.dev](https://ai.google.dev)
- Groq API key — [console.groq.com](https://console.groq.com)

---

## Installation

**1. Clone repository**
```bash
git clone https://github.com/username/rag-mandiri.git
cd rag-mandiri
```

**2. Create and activate virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

---

## Configuration

Buat file `.env` di root folder berdasarkan `.env.example`:

```env
GOOGLE_API_KEY=your_google_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

Parameter lain dapat dikonfigurasi di `app/config.py`:

```python
VECTORSTORE_PATH = "./vectorstore"   # lokasi ChromaDB
UPLOAD_PATH = "./uploads"            # lokasi file upload
COLLECTION_NAME = "mandiri_2025"     # nama collection ChromaDB
CHUNK_SIZE = 1000                    # ukuran chunk dalam karakter
CHUNK_OVERLAP = 200                  # overlap antar chunk
```

---

## Running the Application

**Jalankan development server:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Akses Swagger UI:**
```
http://127.0.0.1:8000/docs
```

---

## API Reference

### `GET /`
Health check endpoint.

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

| Field | Type | Description |
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

**Error responses:**
- `400` — File bukan format PDF

**Proses internal:**
1. Simpan PDF ke `uploads/`
2. Ekstraksi teks per halaman menggunakan PyMuPDF
3. Deskripsi gambar/chart menggunakan Groq Vision
4. Inject deskripsi manual untuk halaman dengan infografis kompleks
5. Chunking dengan `RecursiveCharacterTextSplitter` (1000 karakter, overlap 200)
6. Embedding setiap chunk menggunakan Gemini `gemini-embedding-001`
7. Simpan vector + metadata ke ChromaDB

---

### `POST /query`
Ajukan pertanyaan berdasarkan dokumen yang telah diingesti.

**Request body:**
```json
{
  "question": "Apa saja peran Unit Pelindungan Nasabah?",
  "top_k": 5
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| question | string | required | Pertanyaan dalam Bahasa Indonesia |
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

| Field | Description |
|---|---|
| answer | Jawaban dalam Bahasa Indonesia berdasarkan dokumen |
| source_pages | Nomor halaman sumber jawaban ditemukan |
| chunks_used | Jumlah chunk yang digunakan sebagai context |

**Error responses:**
- `400` — Pertanyaan kosong

**Proses internal:**
1. Embed pertanyaan menggunakan Gemini `gemini-embedding-001`
2. Similarity search di ChromaDB → ambil top-K chunks
3. Susun context dari chunks yang ditemukan
4. Jalankan LangChain LCEL chain: `PromptTemplate | ChatGroq | StrOutputParser`
5. Return jawaban + source pages

---

## Evaluation Results

Berikut hasil pengujian dengan 6 pertanyaan evaluasi dari dokumen:

**1. Peran Unit Pelindungan Nasabah (Sumber: Hal. 7)**
```
Q: Apa saja peran Unit Pelindungan Nasabah menurut peraturan POJK No. 22 Tahun 2023?
A: Unit Pelindungan Nasabah memiliki 9 peran, yaitu: 1. Mensosialisasikan prinsip
   Pelindungan Nasabah kepada seluruh Pegawai Bank. 2. Mengoordinasikan perencanaan
   dan pelaksanaan kepatuhan Bank... (9 poin lengkap)
Source pages: [7, 8]  ✅
```

**2. Jam Penagihan (Sumber: Hal. 7)**
```
Q: Jika Bank Mandiri menggunakan jasa Perusahaan Jasa Penagihan, apakah penagihan
   boleh dilakukan pada jam 21.00?
A: Tidak boleh. Penagihan hanya dapat dilakukan pada pukul 08.00 sampai dengan
   pukul 20.00 waktu wilayah domisili debitur.
Source pages: [5, 7]  ✅
```

**3. Kredit Sektor Tambang & Konstruksi (Sumber: Hal. 4)**
```
Q: Berapa nominal dan persentase pertumbuhan kredit di sektor tambang dan konstruksi?
A: Sektor tambang: Nominal Rp11.614.853 triliun, pertumbuhan 7,98%.
   Sektor konstruksi: Nominal Rp8.264.848 triliun, pertumbuhan 8,27%.
Source pages: [3, 4, 5]  ✅
```

**4. Komposisi DPK 2024 & 2025 (Sumber: Hal. 6)**
```
Q: Sebutkan persentase komposisi dana pihak ketiga (DPK) di Bank Mandiri
   pada tahun 2024 dan 2025?
A: Tahun 2024: Deposito Berjangka 20,57%, Tabungan 39,31%, Giro 40,12%.
   Tahun 2025: Deposito Berjangka 29,11%, Tabungan 36,66%, Giro 34,23%.
Source pages: [1, 2, 3, 6]  ✅
```

**5. Alur Penanganan Pengaduan (Sumber: Hal. 8)**
```
Q: Bagaimana alur penanganan nasabah di Bank Mandiri jika terdapat laporan pengaduan?
A: 1. MENYAMPAIKAN PENGADUAN: Nasabah menyampaikan pengaduan melalui media masa,
   telepon, email, media sosial, atau surat cabang. 2. VERIFIKASI & INPUT: Bank
   menerima, memverifikasi, dan menginput pengaduan... (7 langkah lengkap)
Source pages: [7, 8, 9]  ✅
```

**6. Saluran Pengaduan (Sumber: Hal. 9)**
```
Q: Apa saja saluran pengaduan yang disediakan oleh Bank Mandiri?
A: Bank Mandiri menyediakan: 1. Mandiri Call 14000 (24 jam). 2. Akun X: mandiricare
   dan @bankmandiri. 3. WhatsApp MITA: 0811-8414-000. 4. Website bankmandiri.co.id...
   (9 saluran lengkap)
Source pages: [7, 8, 9]  ✅
```

---

## Design Decisions

**Hybrid Architecture — Custom Parser + LangChain Orchestration**

Parser PDF dibuat custom menggunakan PyMuPDF + Groq Vision karena LangChain Document Loader bawaan tidak mendukung ekstraksi gambar dari PDF. Bagian retrieval dan answer synthesis menggunakan LangChain LCEL untuk orchestration yang terstruktur dan mudah diganti komponennya.

**Knowledge Injection untuk Infografis Kompleks**

Halaman 8 (alur penanganan pengaduan) dan halaman 9 (daftar saluran pengaduan) menggunakan deskripsi manual karena infografis yang terdiri dari panah, kotak, dan elemen visual terpisah tidak dapat dideskripsikan akurat oleh vision model secara otomatis. Pendekatan ini memastikan akurasi jawaban untuk pertanyaan berbasis infografis.

**Gemini untuk Embedding, Groq untuk LLM**

Gemini `gemini-embedding-001` dipilih untuk embedding karena kualitas semantic search-nya baik untuk Bahasa Indonesia. Groq `llama-3.3-70b-versatile` dipilih untuk LLM karena gratis, cepat, dan tidak ada rate limit ketat — cocok untuk development dan demo.

**Chunk Size 1000 dengan Overlap 200**

Nilai ini dipilih sebagai keseimbangan antara konteks yang cukup per chunk dan jumlah chunk yang tidak terlalu banyak. Overlap 200 karakter memastikan informasi di batas antar chunk tidak hilang saat dipotong.
