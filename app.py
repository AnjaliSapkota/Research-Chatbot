from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os
import shutil
import fitz
import uuid

from regex import search
from backend.rag import extract_text, store_document, search

app = FastAPI(title="Research Chatbot")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


#upload pdf
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text
    text = extract_text(file_path)

    # Store in RAG system
    num_chunks = store_document(file_id, text)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "chunks": num_chunks,
        "status": "indexed"
    }

# Ask Question
@app.post("/ask")
async def ask(request: Request):

    chunks = search(
        request.document_id,
        request.question,
        k=3
    )

    if len(chunks) == 0:
        return {
            "answer": "No relevant information found."
        }

    context = "\n\n".join(chunks)

    return {
        "answer": context,
        "retrieved_chunks": chunks
    }


# Health Check
@app.get("/health")
def health():
    return {
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)