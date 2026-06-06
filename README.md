# Multimodal RAG — Bank Mandiri 2025

Pipeline **Retrieval Augmented Generation (RAG)** berbasis REST API yang mampu memproses dokumen PDF multimodal, yaitu dokumen yang berisi teks, gambar, chart, tabel, dan infografis. Sistem ini membangun knowledge base dari dokumen PDF, menyimpan representasi vektor ke ChromaDB, lalu menjawab pertanyaan pengguna berdasarkan konteks dokumen yang paling relevan.

Project ini menggunakan **PyMuPDF** untuk ekstraksi teks dan gambar dari PDF, **Groq Vision** untuk mendeskripsikan konten visual, **Google Gemini Embedding** untuk membuat embedding teks, **ChromaDB** sebagai vector database lokal, dan **Groq Llama 3.3 70B** sebagai LLM untuk menghasilkan jawaban akhir.

---

## Daftar Isi

- [Gambaran Umum](#gambaran-umum)
- [Kemampuan Utama](#kemampuan-utama)
- [Arsitektur Pipeline](#arsitektur-pipeline)
- [Tech Stack](#tech-stack)
- [Struktur Project](#struktur-project)
- [Prasyarat](#prasyarat)
- [Instalasi](#instalasi)
- [Konfigurasi Environment](#konfigurasi-environment)
- [Menjalankan Aplikasi](#menjalankan-aplikasi)
- [Referensi API](#referensi-api)
- [Alur Kerja Program](#alur-kerja-program)
- [Penjelasan Modul Kode](#penjelasan-modul-kode)
- [Keputusan Desain](#keputusan-desain)
- [Catatan Pengembangan](#catatan-pengembangan)

---

## Gambaran Umum

Sistem ini dibuat untuk melakukan tanya jawab berbasis dokumen PDF **Laporan Bank Mandiri 2025**. Pengguna dapat mengunggah file PDF melalui endpoint API, kemudian sistem akan melakukan proses ingestion untuk mengekstrak teks, mendeskripsikan gambar, melakukan chunking, membuat embedding, dan menyimpan data ke ChromaDB.

Setelah proses ingestion selesai, pengguna dapat mengirim pertanyaan melalui endpoint `/query`. Sistem akan mencari chunk dokumen yang paling relevan menggunakan similarity search, menyusun chunk tersebut sebagai context, lalu menghasilkan jawaban menggunakan LLM.

Output jawaban dilengkapi dengan:

- pertanyaan pengguna,
- jawaban berdasarkan dokumen,
- daftar halaman sumber,
- jumlah chunk yang digunakan.

---

## Kemampuan Utama

Kemampuan utama project ini:

- Upload dokumen PDF melalui REST API.
- Mengekstrak teks dari setiap halaman PDF.
- Mengekstrak gambar dari PDF menggunakan PyMuPDF.
- Mendeskripsikan gambar, chart, tabel, dan infografis menggunakan Groq Vision.
- Menambahkan deskripsi manual untuk halaman infografis kompleks.
- Memotong dokumen menjadi chunk menggunakan `RecursiveCharacterTextSplitter`.
- Membuat embedding chunk menggunakan `gemini-embedding-001`.
- Menyimpan chunk, embedding, dan metadata halaman ke ChromaDB.
- Melakukan semantic search terhadap pertanyaan pengguna.
- Menjawab pertanyaan menggunakan LangChain LCEL.
- Mengembalikan metadata halaman sumber pada setiap jawaban.

---

## Arsitektur Pipeline

```text
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                          │
│                                                                 │
│  Upload PDF melalui endpoint /ingest                            │
│      │                                                          │
│      ▼                                                          │
│  main.py                                                        │
│  - Validasi file PDF                                            │
│  - Simpan file ke folder uploads/                               │
│      │                                                          │
│      ▼                                                          │
│  ingest.py                                                      │
│  - Memanggil parse_pdf() dari parser.py                         │
│      │                                                          │
│      ▼                                                          │
│  parser.py ───── PyMuPDF ─────────► Teks per halaman            │
│      │                                                          │
│      ├──── Groq Vision ───────────► Deskripsi gambar/chart      │
│      │     llama-3.2-11b-vision-preview                         │
│      │                                                          │
│      └──── Manual Injection ─────► Deskripsi halaman kompleks   │
│                                    Halaman 8 dan 9              │
│      │                                                          │
│      ▼                                                          │
│  RecursiveCharacterTextSplitter                                 │
│  - chunk_size = 1000                                            │
│  - chunk_overlap = 200                                          │
│      │                                                          │
│      ▼                                                          │
│  Gemini Embedding                                               │
│  - models/gemini-embedding-001                                  │
│      │                                                          │
│      ▼                                                          │
│  ChromaDB                                                       │
│  - Persistent vector store                                      │
│  - Metadata halaman sumber                                      │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                       QUERY PIPELINE                            │
│                                                                 │
│  Pertanyaan pengguna melalui endpoint /query                    │
│      │                                                          │
│      ▼                                                          │
│  query.py                                                       │
│  - Embed pertanyaan menggunakan Gemini Embedding                │
│      │                                                          │
│      ▼                                                          │
│  ChromaDB Similarity Search                                     │
│  - Mengambil top-K chunk paling relevan                         │
│  - Mengambil metadata halaman sumber                            │
│      │                                                          │
│      ▼                                                          │
│  LangChain LCEL Chain                                           │
│  PromptTemplate | ChatGroq | StrOutputParser                    │
│      │                                                          │
│      ▼                                                          │
│  Response                                                       │
│  - question                                                     │
│  - answer                                                       │
│  - source_pages                                                 │
│  - chunks_used                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Komponen | Teknologi | Keterangan |
|---|---|---|
| API Framework | FastAPI | Membuat REST API dan Swagger UI otomatis |
| Request Model | Pydantic | Validasi request dan response API |
| PDF Parser | PyMuPDF / fitz | Ekstraksi teks dan gambar dari PDF |
| Vision Model | Groq Llama 3.2 11B Vision Preview | Mendeskripsikan gambar, chart, tabel, dan infografis |
| Embedding Model | Google Gemini `gemini-embedding-001` | Membuat vector embedding dari teks |
| Vector Database | ChromaDB | Penyimpanan vector lokal secara persisten |
| Text Splitter | LangChain Text Splitters | Memotong teks menjadi chunk |
| LLM | Groq Llama 3.3 70B Versatile | Menghasilkan jawaban berdasarkan context |
| Orchestration | LangChain LCEL | Pipeline `PromptTemplate | ChatGroq | StrOutputParser` |
| Environment | python-dotenv | Membaca API key dari file `.env` |
| Bahasa Pemrograman | Python | Bahasa utama project |

---

## Struktur Project

```text
rag-mandiri/
├── app/
│   ├── __init__.py
│   ├── config.py       # Konfigurasi API key, path, collection, dan chunking
│   ├── ingest.py       # Pipeline ingestion: parsing, chunking, embedding, simpan ke ChromaDB
│   ├── main.py         # FastAPI app dan definisi endpoint
│   ├── parser.py       # Parsing PDF, ekstraksi teks, deskripsi gambar, manual injection
│   └── query.py        # Pipeline query: embedding pertanyaan, retrieval, LLM answer
│
├── uploads/            # Folder penyimpanan PDF yang diupload
├── vectorstore/        # Folder penyimpanan ChromaDB persistent
├── .env                # API key, tidak boleh di-commit ke GitHub
├── .env.example        # Contoh konfigurasi environment
├── .gitignore          # File/folder yang diabaikan Git
├── requirements.txt    # Daftar dependency Python
└── README.md           # Dokumentasi project
```

Keterangan folder penting:

| File / Folder | Fungsi |
|---|---|
| `app/config.py` | Menyimpan konfigurasi utama project |
| `app/main.py` | Berisi FastAPI app dan endpoint `/`, `/ingest`, `/query` |
| `app/parser.py` | Mengekstrak teks dan gambar dari PDF |
| `app/ingest.py` | Mengubah PDF menjadi chunk dan menyimpannya ke ChromaDB |
| `app/query.py` | Mengambil chunk relevan dan menghasilkan jawaban |
| `uploads/` | Menyimpan PDF yang diupload user |
| `vectorstore/` | Menyimpan database vector ChromaDB |
| `.env` | Menyimpan `GOOGLE_API_KEY` dan `GROQ_API_KEY` |

---

## Prasyarat

Sebelum menjalankan project, pastikan sudah tersedia:

- Python 3.10 atau lebih baru.
- Google Gemini API key.
- Groq API key.
- pip.
- Virtual environment Python.

---

## Instalasi

### 1. Clone repository

```bash
git clone https://github.com/Ahjaris/Multimodal-RAG-Mandiri.git
cd rag-mandiri
```

### 2. Buat virtual environment

```bash
python -m venv venv
```

### 3. Aktifkan virtual environment

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

### 4. Install dependency

```bash
pip install -r requirements.txt
```

Contoh isi `requirements.txt`:

```txt
fastapi
uvicorn
python-dotenv
python-multipart
pymupdf
groq
chromadb
google-genai
langchain
langchain-core
langchain-groq
langchain-text-splitters
pydantic
```

---

## Konfigurasi Environment

Buat file `.env` di root project.

```env
GOOGLE_API_KEY=isi_google_api_key_kamu
GROQ_API_KEY=isi_groq_api_key_kamu
```

Contoh file `.env.example`:

```env
GOOGLE_API_KEY=
GROQ_API_KEY=
```

Konfigurasi utama terdapat di `app/config.py`.

```python
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

VECTORSTORE_PATH = "./vectorstore"
UPLOAD_PATH = "./uploads"
COLLECTION_NAME = "mandiri_2025"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

Keterangan konfigurasi:

| Konfigurasi | Fungsi |
|---|---|
| `GOOGLE_API_KEY` | API key untuk Google Gemini Embedding |
| `GROQ_API_KEY` | API key untuk Groq Vision dan ChatGroq |
| `VECTORSTORE_PATH` | Lokasi penyimpanan ChromaDB |
| `UPLOAD_PATH` | Lokasi penyimpanan PDF yang diupload |
| `COLLECTION_NAME` | Nama collection di ChromaDB |
| `CHUNK_SIZE` | Ukuran maksimal setiap chunk teks |
| `CHUNK_OVERLAP` | Jumlah overlap antar chunk |

---

## Menjalankan Aplikasi

Pastikan folder `uploads/` sudah tersedia. Jika belum, buat folder tersebut:

```bash
mkdir uploads
```

Jalankan FastAPI server:

```bash
uvicorn app.main:app --reload --port 8000
```

Jika berhasil, server akan berjalan di:

```text
http://127.0.0.1:8000
```

Buka Swagger UI untuk mencoba API:

```text
http://127.0.0.1:8000/docs
```

---

## Referensi API

### GET `/`

Endpoint untuk mengecek apakah API aktif.

**Response:**

```json
{
  "status": "ok",
  "message": "RAG API aktif"
}
```

---

### POST `/ingest`

Endpoint untuk mengupload dan memproses file PDF menjadi knowledge base.

**Request:**

`multipart/form-data`

| Field | Tipe | Keterangan |
|---|---|---|
| `file` | File | File PDF yang akan diproses |

**Contoh response:**

```json
{
  "status": "success",
  "total_pages": 9,
  "total_chunks": 41
}
```

**Error:**

| Status Code | Penyebab |
|---|---|
| `400` | File yang diupload bukan PDF |

**Proses yang terjadi pada endpoint `/ingest`:**

1. FastAPI menerima file PDF dari user.
2. Sistem mengecek apakah ekstensi file adalah `.pdf`.
3. File disimpan ke folder `uploads/`.
4. Fungsi `process_pdf()` dipanggil.
5. PDF diparsing menggunakan `parse_pdf()`.
6. Teks dan deskripsi gambar digabungkan per halaman.
7. Teks dipotong menjadi chunk.
8. Setiap chunk diubah menjadi embedding.
9. Chunk, embedding, dan metadata halaman disimpan ke ChromaDB.
10. API mengembalikan jumlah halaman dan jumlah chunk.

---

### POST `/query`

Endpoint untuk mengirim pertanyaan berdasarkan dokumen yang sudah diingest.

**Request body:**

```json
{
  "question": "Apa saja saluran pengaduan yang disediakan Bank Mandiri?",
  "top_k": 5
}
```

| Field | Tipe | Default | Keterangan |
|---|---|---:|---|
| `question` | string | wajib | Pertanyaan pengguna |
| `top_k` | integer | 5 | Jumlah chunk relevan yang diambil dari ChromaDB |

**Contoh response:**

```json
{
  "question": "Apa saja saluran pengaduan yang disediakan Bank Mandiri?",
  "answer": "Bank Mandiri menyediakan beberapa saluran pengaduan, yaitu Mandiri Call 14000, akun X mandiricare dan @bankmandiri, WhatsApp MITA 0811-8414-000, website Bank Mandiri, Facebook, kantor cabang, email mandiricare@bankmandiri.co.id, Instagram @bankmandiri, dan surat resmi.",
  "source_pages": [9],
  "chunks_used": 5
}
```

**Error:**

| Status Code | Penyebab |
|---|---|
| `400` | Pertanyaan kosong |

**Proses yang terjadi pada endpoint `/query`:**

1. User mengirim pertanyaan.
2. Sistem mengecek apakah pertanyaan kosong atau tidak.
3. Pertanyaan diubah menjadi embedding menggunakan Gemini.
4. ChromaDB mencari top-K chunk paling relevan.
5. Chunk disusun menjadi context dengan format halaman sumber.
6. Context dan pertanyaan dimasukkan ke prompt.
7. ChatGroq menghasilkan jawaban.
8. API mengembalikan jawaban, halaman sumber, dan jumlah chunk yang digunakan.

---

## Alur Kerja Program

### 1. Konfigurasi Project

File `config.py` memuat variabel environment dan konfigurasi utama:

- API key Google Gemini.
- API key Groq.
- path ChromaDB.
- path upload.
- nama collection.
- ukuran chunk.
- overlap antar chunk.

Konfigurasi ini kemudian digunakan oleh modul `ingest.py`, `parser.py`, dan `query.py`.

---

### 2. Upload PDF

Endpoint `/ingest` menerima file PDF dari user. File divalidasi berdasarkan ekstensi `.pdf`. Jika file valid, file disimpan ke folder `uploads/`.

```python
save_path = os.path.join(UPLOAD_PATH, file.filename)
with open(save_path, "wb") as f:
    shutil.copyfileobj(file.file, f)
```

Setelah tersimpan, file diproses oleh fungsi:

```python
process_pdf(save_path)
```

---

### 3. Parsing PDF

Parsing dilakukan oleh fungsi:

```python
parse_pdf(pdf_path)
```

Fungsi ini membuka PDF menggunakan PyMuPDF:

```python
doc = fitz.open(pdf_path)
```

Untuk setiap halaman, sistem mengambil:

- nomor halaman,
- teks halaman menggunakan `page.get_text("text")`,
- deskripsi gambar dari halaman tersebut.

Output `parse_pdf()` berbentuk list dictionary:

```json
[
  {
    "page": 1,
    "text": "teks halaman",
    "images_description": [
      "deskripsi gambar halaman"
    ]
  }
]
```

---

### 4. Deskripsi Gambar dengan Groq Vision

Jika halaman memiliki gambar yang ukurannya memenuhi batas minimum, gambar akan diekstrak lalu dikirim ke Groq Vision.

Fungsi utama:

```python
describe_image_with_groq(image_bytes)
```

Model yang digunakan:

```text
llama-3.2-11b-vision-preview
```

Prompt vision meminta model untuk mendeskripsikan:

- diagram alur,
- chart atau grafik,
- tabel,
- gambar,
- daftar item,
- teks yang tampil pada visual.

---

### 5. Manual Page Description

Beberapa halaman infografis kompleks diberi deskripsi manual melalui dictionary:

```python
MANUAL_PAGE_DESCRIPTIONS = {
    8: "...",
    9: "..."
}
```

Halaman 8 berisi alur penanganan pengaduan nasabah.  
Halaman 9 berisi daftar saluran pengaduan Bank Mandiri.

Manual injection digunakan karena infografis yang kompleks sering kali sulit dideskripsikan secara lengkap oleh vision model secara otomatis.

---

### 6. Chunking Dokumen

Setelah teks halaman dan deskripsi gambar digabungkan, teks dipotong menjadi chunk menggunakan:

```python
RecursiveCharacterTextSplitter
```

Konfigurasi chunking:

```python
chunk_size = 1000
chunk_overlap = 200
separators = ["\n\n", "\n", ". ", " "]
```

Tujuannya agar setiap chunk memiliki konteks yang cukup, tetapi tetap tidak terlalu panjang untuk proses retrieval dan LLM.

---

### 7. Embedding Chunk

Setiap chunk diubah menjadi vector embedding menggunakan:

```python
models/gemini-embedding-001
```

Fungsi utama:

```python
embed_texts(texts)
```

Embedding dilakukan dalam batch berisi 10 chunk:

```python
for i in range(0, len(all_chunks), 10):
    batch = all_chunks[i:i+10]
    all_vectors.extend(embed_texts(batch))
```

Batching dilakukan agar proses embedding lebih stabil dan tidak terlalu berat dalam satu request.

---

### 8. Penyimpanan ke ChromaDB

Setelah chunk dan embedding tersedia, data disimpan ke ChromaDB.

```python
collection.add(
    documents=all_chunks,
    embeddings=all_vectors,
    metadatas=all_metadatas,
    ids=all_ids
)
```

Data yang disimpan:

| Data | Isi |
|---|---|
| `documents` | Teks chunk |
| `embeddings` | Vector embedding chunk |
| `metadatas` | Metadata halaman dan sumber file |
| `ids` | ID unik untuk setiap chunk |

Metadata yang disimpan:

```json
{
  "page": 8,
  "source": "./uploads/nama_file.pdf"
}
```

Metadata ini digunakan untuk menampilkan halaman sumber ketika sistem menjawab pertanyaan.

---

### 9. Query dan Retrieval

Ketika user mengirim pertanyaan ke endpoint `/query`, sistem membuat embedding pertanyaan menggunakan fungsi:

```python
embed_query(question)
```

Kemudian ChromaDB melakukan pencarian:

```python
collection.query(
    query_embeddings=[query_vector],
    n_results=top_k,
    include=["documents", "metadatas", "distances"]
)
```

Hasil retrieval berupa:

- chunk dokumen relevan,
- metadata halaman,
- distance similarity.

---

### 10. Answer Generation

Chunk yang ditemukan disusun menjadi context:

```text
[Halaman 8]
isi chunk dari halaman 8

---

[Halaman 9]
isi chunk dari halaman 9
```

Kemudian context dan pertanyaan dimasukkan ke prompt:

```text
Kamu adalah asisten yang menjawab pertanyaan berdasarkan dokumen Laporan Bank Mandiri 2025.
Jawab HANYA berdasarkan context yang diberikan.
Jika informasi tidak ada di context, katakan informasi tidak ditemukan dalam dokumen.
Jawab dalam Bahasa Indonesia yang jelas dan terstruktur.
```

Pipeline jawaban menggunakan LangChain LCEL:

```python
chain = prompt_template | llm | StrOutputParser()
```

---

## Penjelasan Modul Kode

### `app/config.py`

Modul ini berisi konfigurasi global project.

Fungsi utama:

- membaca `.env`,
- mengambil API key,
- menentukan path vectorstore,
- menentukan path upload,
- menentukan nama collection,
- menentukan chunk size dan overlap.

Variabel penting:

```python
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
VECTORSTORE_PATH = "./vectorstore"
UPLOAD_PATH = "./uploads"
COLLECTION_NAME = "mandiri_2025"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

---

### `app/main.py`

Modul ini merupakan entry point API menggunakan FastAPI.

Isi utama:

- membuat instance FastAPI,
- mendefinisikan model request dan response,
- membuat endpoint `/`,
- membuat endpoint `/ingest`,
- membuat endpoint `/query`.

Endpoint:

| Endpoint | Method | Fungsi |
|---|---|---|
| `/` | GET | Mengecek status API |
| `/ingest` | POST | Upload dan proses PDF |
| `/query` | POST | Mengirim pertanyaan dan mendapatkan jawaban |

---

### `app/parser.py`

Modul ini bertugas membaca isi PDF.

Fungsi utama:

| Fungsi | Keterangan |
|---|---|
| `describe_image_with_groq()` | Mengirim gambar ke Groq Vision dan menerima deskripsi |
| `_describe_page_images()` | Mengekstrak dan mendeskripsikan gambar dari halaman PDF |
| `parse_pdf()` | Mengambil teks dan deskripsi gambar dari seluruh halaman PDF |

Konstanta penting:

| Konstanta | Fungsi |
|---|---|
| `MIN_IMAGE_SIZE` | Mengabaikan gambar kecil agar logo/icon tidak ikut diproses |
| `VISION_PROMPT` | Instruksi untuk Groq Vision |
| `MANUAL_PAGE_DESCRIPTIONS` | Deskripsi manual untuk halaman infografis kompleks |

---

### `app/ingest.py`

Modul ini bertugas membuat knowledge base dari PDF.

Fungsi utama:

| Fungsi | Keterangan |
|---|---|
| `embed_texts()` | Membuat embedding untuk beberapa teks |
| `process_pdf()` | Parsing PDF, chunking, embedding, dan simpan ke ChromaDB |

Tahapan `process_pdf()`:

1. Parsing PDF.
2. Menggabungkan teks halaman dengan deskripsi gambar.
3. Memecah teks menjadi chunk.
4. Membuat embedding semua chunk.
5. Menyimpan chunk ke ChromaDB.
6. Mengembalikan jumlah halaman dan chunk.

---

### `app/query.py`

Modul ini bertugas menjawab pertanyaan pengguna.

Fungsi utama:

| Fungsi | Keterangan |
|---|---|
| `embed_query()` | Membuat embedding dari pertanyaan |
| `answer_question()` | Retrieval chunk relevan dan menghasilkan jawaban |

Komponen utama:

```python
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    max_tokens=1024
)
```

Prompt dirancang agar model hanya menjawab berdasarkan context yang diberikan. Jika jawaban tidak tersedia pada context, model diarahkan untuk mengatakan bahwa informasi tidak ditemukan dalam dokumen.

---

## Keputusan Desain

### 1. Custom Parser dengan PyMuPDF

Parser dibuat menggunakan PyMuPDF karena project perlu mengekstrak bukan hanya teks, tetapi juga gambar dari PDF. PyMuPDF memungkinkan sistem mengambil teks halaman dan mengekstrak gambar dalam bentuk bytes untuk dikirim ke vision model.

---

### 2. Groq Vision untuk Konten Visual

Dokumen PDF tidak selalu berisi teks biasa. Beberapa informasi penting dapat berada dalam chart, tabel gambar, atau infografis. Karena itu, gambar yang ditemukan di halaman PDF dikirim ke Groq Vision agar dapat diubah menjadi deskripsi teks.

---

### 3. Manual Injection untuk Halaman 8 dan 9

Halaman 8 dan 9 diberi deskripsi manual karena berisi infografis yang kompleks. Untuk kasus seperti flowchart, ikon, dan daftar visual, manual injection memastikan informasi penting tetap masuk ke knowledge base secara akurat.

---

### 4. Gemini Embedding untuk Semantic Search

Gemini `gemini-embedding-001` digunakan untuk membuat representasi vector dari chunk dan pertanyaan. Embedding ini memungkinkan sistem mencari chunk berdasarkan makna, bukan hanya kemiripan kata secara literal.

---

### 5. ChromaDB sebagai Vector Store Lokal

ChromaDB digunakan karena mudah dijalankan secara lokal dan mendukung penyimpanan persistent. Data vector tetap tersimpan di folder `vectorstore/`, sehingga tidak perlu membuat ulang knowledge base setiap kali server dijalankan ulang.

---

### 6. LangChain LCEL untuk Answer Generation

LangChain LCEL digunakan untuk menyusun pipeline jawaban secara ringkas dan modular:

```python
chain = prompt_template | llm | StrOutputParser()
```

Dengan struktur ini, prompt, model, atau parser output dapat diganti tanpa mengubah keseluruhan alur.

---

### 7. Chunk Size 1000 dan Overlap 200

Chunk size 1000 dipilih agar setiap chunk memiliki konteks yang cukup. Overlap 200 digunakan agar informasi yang berada di batas antar chunk tidak terpotong sepenuhnya.

---

### 8. Metadata Halaman Sumber

Setiap chunk disimpan dengan metadata halaman. Metadata ini penting agar jawaban tidak hanya berisi teks, tetapi juga dapat menunjukkan halaman sumber yang digunakan.

---

## Catatan Pengembangan

Beberapa pengembangan yang dapat dilakukan:

1. Menambahkan pengecekan otomatis jika API key belum tersedia.
2. Membuat folder `uploads/` otomatis jika belum ada.
3. Menambahkan endpoint untuk menghapus collection ChromaDB.
4. Menambahkan endpoint untuk melihat daftar dokumen yang sudah diingest.
5. Menambahkan reranking agar retrieval lebih akurat.
6. Menambahkan validasi ukuran file PDF.
7. Menambahkan dukungan multi-dokumen dengan metadata nama dokumen.
8. Menambahkan streaming response untuk jawaban panjang.
9. Menambahkan UI sederhana untuk upload PDF dan bertanya.
10. Menambahkan evaluasi retrieval seperti precision@k atau recall@k.

---

## Contoh Workflow

### 1. Jalankan server

```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Buka Swagger UI

```text
http://127.0.0.1:8000/docs
```

### 3. Upload PDF melalui endpoint `/ingest`

Upload dokumen PDF Bank Mandiri 2025.

### 4. Tunggu proses ingestion selesai

Contoh response:

```json
{
  "status": "success",
  "total_pages": 9,
  "total_chunks": 41
}
```

### 5. Kirim pertanyaan melalui endpoint `/query`

Contoh request:

```json
{
  "question": "Apa saja saluran pengaduan yang tersedia?",
  "top_k": 5
}
```

### 6. Terima jawaban

Contoh response:

```json
{
  "question": "Apa saja saluran pengaduan yang tersedia?",
  "answer": "Saluran pengaduan yang tersedia meliputi Mandiri Call 14000, akun X mandiricare dan @bankmandiri, WhatsApp MITA, website Bank Mandiri, Facebook, kantor cabang, email, Instagram, dan surat resmi.",
  "source_pages": [9],
  "chunks_used": 5
}
```

---

## Kesimpulan

Project **Multimodal RAG — Bank Mandiri 2025** merupakan sistem tanya-jawab berbasis dokumen PDF yang menggabungkan parsing teks, pemahaman gambar, semantic search, vector database, dan LLM. Dengan pipeline ingestion dan query yang terpisah, sistem ini dapat memproses dokumen PDF multimodal dan memberikan jawaban dalam Bahasa Indonesia berdasarkan context dokumen yang paling relevan.
