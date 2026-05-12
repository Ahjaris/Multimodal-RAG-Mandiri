import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.ingest import process_pdf
from app.query import answer_question
from app.config import UPLOAD_PATH

# ── App ────────────────────────────────────────────────────
app = FastAPI(
    title="Multimodal RAG — Bank Mandiri 2025",
    description="API untuk tanya-jawab berbasis dokumen PDF Bank Mandiri",
    version="1.0.0"
)

# ── Models ─────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class QueryResponse(BaseModel):
    question: str
    answer: str
    source_pages: list[int]
    chunks_used: int

# ── Endpoints ──────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "RAG API aktif"}

@app.post("/ingest")
async def ingest_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Hanya file PDF yang diterima")

    save_path = os.path.join(UPLOAD_PATH, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return process_pdf(save_path)

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(400, "Pertanyaan tidak boleh kosong")

    return answer_question(request.question, request.top_k)