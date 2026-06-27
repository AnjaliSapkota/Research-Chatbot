import fitz
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Load embedding model

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model loaded.")

# In-memory storage

documents = {}
indexes = {}  # maps doc_id → FAISS index


#  Extract text
def extract_text(pdf_path):
    document = fitz.open(pdf_path)
    text = ""

    for page in document:
        text += page.get_text()

    document.close()
    return text


# Chunk text
def chunk_text(text, chunk_size=400, overlap=80):
    words = text.split()
    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = words[start:end]

        chunks.append(
            " ".join(chunk)
        )

        start += chunk_size - overlap

    return chunks


# Create embeddings

def generate_embeddings(chunks):

    embeddings = embedding_model.encode(
        chunks,
        convert_to_numpy=True
    )

    embeddings = embeddings.astype("float32")

    return embeddings

# Build FAISS index
def create_faiss_index(vectors):
    dimension  = vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors)
    return index


# Store document
def store_document(
    document_id,
    text
):

    chunks = chunk_text(text)   

    embeddings = generate_embeddings(chunks)

    index = create_faiss_index(embeddings)

    documents[document_id] = chunks

    indexes[document_id] = index

    return len(chunks)

# Semantic Search relevant chunks
def search(document_id, question, k=3):
    if document_id not in indexes:
        return []

    index = indexes[document_id]
    chunks = documents[document_id]

    question_vector = embedding_model.encode([question]).astype("float32")

    distances, indices = index.search(question_vector, k)

    results = [chunks[i] for i in indices[0]]
    return results

# def search(
#     document_id,
#     question,
#     k=3
# ):

#     if document_id not in indexes:

#         return []

#     question_vector = embedding_model.encode(
#         [question],
#         convert_to_numpy=True
#     )

#     question_vector = question_vector.astype("float32")

#     index = indexes[document_id]

#     distances, indices = index.search(
#         question_vector,
#         k
#     )

#     chunks = documents[document_id]

#     results = []

#     for idx in indices[0]:

#         if idx < len(chunks):

#             results.append(chunks[idx])

#     return results