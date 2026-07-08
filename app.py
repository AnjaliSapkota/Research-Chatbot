from fastapi import FastAPI, UploadFile, File, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import os
import shutil
import uuid

from backend.database import init_db
from backend.rag import extract_text, store_document, search
from backend.llm import generate_answer

# FastAPI App
app = FastAPI(title="Research Chatbot")

# Initialize SQLite database
init_db()

# Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Upload Folder
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Request Models
class QuestionRequest(BaseModel):
    document_id: str
    question: str

# Home Page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# Upload PDF
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    # Validate file
    if not file.filename.lower().endswith(".pdf"):
        return {
            "status": "error",
            "message": "Only PDF files are allowed."
        }

    # Unique ID for this document
    document_id = str(uuid.uuid4())

    # Save uploaded file
    file_path = os.path.join(
        UPLOAD_DIR,
        f"{document_id}.pdf"
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:

        # Extract text
        text = extract_text(file_path)

        # Store into FAISS + SQLite
        chunk_count = store_document(
            document_id,
            text
        )

        return {
            "status": "success",
            "document_id": document_id,
            "filename": file.filename,
            "chunks": chunk_count
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# Ask Question
@app.post("/ask")
async def ask(data: QuestionRequest):

    chunks = search(
        data.document_id,
        data.question,
        k=3
    )

    if not chunks:
        return {
            "answer": "No relevant information found.",
            "sources": []
        }

    answer = generate_answer(
        data.question,
        chunks
    )

    return {
        "answer": answer,
        "sources": chunks
    }

# Health Check

@app.get("/health")
async def health():

    return {
        "status": "running"
    }

# Run App

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )