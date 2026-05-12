import chromadb
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.parser import parse_pdf
from app.config import *

# ── Setup ──────────────────────────────────────────────────
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

chroma_client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " "]
)

# ── Functions ──────────────────────────────────────────────
def embed_texts(texts: list[str]) -> list[list[float]]:
    result = gemini_client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=texts,
    )
    return [e.values for e in result.embeddings]

def process_pdf(pdf_path: str) -> dict:
    print("Step 1: Parsing PDF...")
    pages = parse_pdf(pdf_path)

    all_chunks, all_metadatas, all_ids = [], [], []
    chunk_counter = 0

    print("Step 2: Chunking...")
    for page_data in pages:
        full_text = page_data["text"]
        for img_desc in page_data["images_description"]:
            full_text += "\n\n" + img_desc

        if not full_text.strip():
            continue

        for chunk in splitter.split_text(full_text):
            all_chunks.append(chunk)
            all_metadatas.append({"page": page_data["page"], "source": pdf_path})
            all_ids.append(f"chunk_{chunk_counter}")
            chunk_counter += 1

    print(f"Step 3: Embedding {len(all_chunks)} chunks...")
    all_vectors = []
    for i in range(0, len(all_chunks), 10):
        batch = all_chunks[i:i+10]
        all_vectors.extend(embed_texts(batch))
        print(f"  Embedded {min(i+10, len(all_chunks))}/{len(all_chunks)}")

    print("Step 4: Simpan ke ChromaDB...")
    collection.add(
        documents=all_chunks,
        embeddings=all_vectors,
        metadatas=all_metadatas,
        ids=all_ids
    )

    return {
        "status": "success",
        "total_pages": len(pages),
        "total_chunks": len(all_chunks)
    }