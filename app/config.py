import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
VECTORSTORE_PATH = "./vectorstore"
UPLOAD_PATH = "./uploads"
COLLECTION_NAME = "mandiri_2025"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200