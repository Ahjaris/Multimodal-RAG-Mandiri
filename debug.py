# debug.py - jalankan sekali untuk diagnosis
import chromadb
from google import genai
from app.config import *

gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
chroma_client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

def embed_query(text):
    result = gemini_client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=[text],
    )
    return result.embeddings[0].values

question = "Apa saja peran Unit Pelindungan Nasabah menurut peraturan POJK No. 22 Tahun 2023?"
query_vector = embed_query(question)

results = collection.query(
    query_embeddings=[query_vector],
    n_results=5,
    include=["documents", "metadatas", "distances"]
)

for i, (chunk, meta, dist) in enumerate(zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0]
)):
    print(f"\n{'='*50}")
    print(f"Rank {i+1} | Halaman: {meta['page']} | Distance: {dist:.4f}")
    print(f"Chunk: {chunk[:200]}...")