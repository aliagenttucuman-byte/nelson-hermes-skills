import os
import io
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.config import Config
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import requests

app = FastAPI(title="RAG PoC API - Etapa 2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config S3 (MinIO)
S3_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:9000")
S3_BUCKET = os.getenv("S3_BUCKET", "rag-documents")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test123456")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
    config=Config(signature_version="s3v4"),
)

# Config Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "http://localhost:6333")
qdrant = QdrantClient(QDRANT_HOST)
COLLECTION_NAME = "rag_documents"

# Config LLM — OpenCode Zen (producción) con fallback a Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
OPENCODE_BASE_URL = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4-nano")

embeddings_model = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_HOST)

ollama_client = OpenAI(base_url=f"{OLLAMA_HOST}/v1", api_key="ollama")


def get_llm_client():
    """Devuelve cliente para generación de respuestas. OpenCode Zen primero, Ollama fallback."""
    if OPENCODE_API_KEY:
        return OpenAI(
            base_url=OPENCODE_BASE_URL,
            api_key=OPENCODE_API_KEY,
            default_headers={
                "HTTP-Referer": os.getenv("OPENCODE_REFERER", "https://github.com/nelson/rag"),
                "X-Title": os.getenv("OPENCODE_TITLE", "NelsonRAG"),
            },
        )
    return ollama_client

# Text splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)


def init_bucket():
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
    except:
        s3_client.create_bucket(Bucket=S3_BUCKET)


def init_qdrant():
    try:
        qdrant.get_collection(COLLECTION_NAME)
    except:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )


@app.on_event("startup")
async def startup():
    init_bucket()
    init_qdrant()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/documents")
async def list_documents():
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        items = response.get("Contents", [])
        return {
            "documents": [
                {"key": obj["Key"], "size": obj["Size"], "last_modified": obj["LastModified"].isoformat()}
                for obj in items
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    try:
        contents = await file.read()

        # Guardar en S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=file.filename,
            Body=contents,
            ContentType="application/pdf",
        )

        # Procesar: extraer texto, chunking, embeddings, guardar en Qdrant
        await process_pdf(file.filename, contents)

        return {"message": "Archivo subido y procesado correctamente", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def process_pdf(filename: str, contents: bytes):
    """Extrae texto del PDF, hace chunking, genera embeddings y guarda en Qdrant."""
    # Extraer texto
    text = ""
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    if not text.strip():
        return

    # Chunking
    chunks = splitter.split_text(text)

    # Generar embeddings y guardar en Qdrant
    points = []
    for i, chunk in enumerate(chunks):
        embedding = embeddings_model.embed_query(chunk)
        point_id = str(uuid.uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": chunk,
                    "document": filename,
                    "chunk_index": i,
                }
            )
        )

    if points:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)


@app.post("/ask")
async def ask_question(question: dict):
    """Recibe una pregunta, busca chunks relevantes y genera respuesta con LLM."""
    query = question.get("question", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")

    try:
        # 1. Generar embedding de la pregunta
        query_embedding = embeddings_model.embed_query(query)

        # 2. Buscar en Qdrant
        search_result = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=5,
        ).points

        if not search_result:
            return {"answer": "No encontré información relevante en los documentos subidos.", "sources": []}

        # 3. Construir contexto
        context = "\n\n".join([f"[Documento: {hit.payload['document']}]\n{hit.payload['text']}" for hit in search_result])

        # 4. Generar respuesta con OpenCode Zen (gpt-5.4-nano) con fallback a Ollama
        prompt = f"""Basándote ÚNICAMENTE en la siguiente información de los documentos, responde la pregunta de forma clara y concisa.

INFORMACIÓN DE LOS DOCUMENTOS:
{context}

PREGUNTA: {query}

RESPUESTA:"""

        client = get_llm_client()
        model = LLM_MODEL if OPENCODE_API_KEY else "llama3.2:3b"
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3,
        )
        answer = response.choices[0].message.content.strip()

        sources = [
            {"document": hit.payload["document"], "score": hit.score, "text": hit.payload["text"][:200] + "..."}
            for hit in search_result
        ]

        return {"answer": answer, "sources": sources}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def stats():
    """Estadísticas de la colección vectorial."""
    try:
        info = qdrant.get_collection(COLLECTION_NAME)
        return {
            "collection": COLLECTION_NAME,
            "points_count": info.points_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
