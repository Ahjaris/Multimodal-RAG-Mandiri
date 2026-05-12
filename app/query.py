import chromadb
from google import genai
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from app.config import *

gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

chroma_client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.2,
    max_tokens=1024
)

prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""Kamu adalah asisten yang menjawab pertanyaan berdasarkan dokumen Laporan Bank Mandiri 2025.
Jawab HANYA berdasarkan context yang diberikan.
Jika informasi tidak ada di context, katakan informasi tidak ditemukan dalam dokumen.
Jawab dalam Bahasa Indonesia yang jelas dan terstruktur.

Context dari dokumen:
{context}

Pertanyaan: {question}

Jawaban:"""
)

chain = prompt_template | llm | StrOutputParser()

def embed_query(text: str) -> list[float]:
    result = gemini_client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=[text],
    )
    return result.embeddings[0].values

def answer_question(question: str, top_k: int = 5) -> dict:
    query_vector = embed_query(question)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    context_parts = []
    source_pages = []
    for chunk, meta in zip(chunks, metadatas):
        context_parts.append(f"[Halaman {meta['page']}]\n{chunk}")
        if meta["page"] not in source_pages:
            source_pages.append(meta["page"])

    answer = chain.invoke({
        "context": "\n\n---\n\n".join(context_parts),
        "question": question
    })

    return {
        "question": question,
        "answer": answer,
        "source_pages": sorted(source_pages),
        "chunks_used": len(chunks)
    }