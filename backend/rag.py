import fitz
import os
import faiss
from numpy import indices
from sentence_transformers import SentenceTransformer
from backend.database import save_chunks, get_chunk
from langchain_text_splitters import RecursiveCharacterTextSplitter


VECTOR_DIR = "vectors"
os.makedirs(VECTOR_DIR, exist_ok=True)


# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model loaded.")


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)


#  Extract text
def extract_text(pdf_path):
    document = fitz.open(pdf_path)
    text = ""

    for page in document:
        text += page.get_text()

    document.close()
    return text


# Chunk text
def chunk_text(text):
    """
    Split text into overlapping chunks using LangChain's
    RecursiveCharacterTextSplitter.
    """

    text = text.replace("\r", "").strip()

    return text_splitter.split_text(text)


# Create embeddings

def generate_embeddings(chunks):

    embeddings = embedding_model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    embeddings = embeddings.astype("float32")

    return embeddings

# Build FAISS index
def create_faiss_index(vectors):
    dimension  = vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)
    return index


# Store document
def store_document(document_id, text):

    # Split document
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("No text could be extracted from the PDF.")

    save_chunks(document_id, chunks)

    # Generate embeddings
    embeddings = generate_embeddings(chunks)

    # Build FAISS index
    index = create_faiss_index(embeddings)

    faiss.write_index(
        index,
        os.path.join(VECTOR_DIR, f"{document_id}.index")
    )

    print(f"Stored {len(chunks)} chunks.")
    
    return len(chunks)


# Semantic Search relevant chunks
def search(document_id, question, k=5):

    index_path = os.path.join(
        VECTOR_DIR,
        f"{document_id}.index"
    )

    if not os.path.exists(index_path):
        return []

    # Load FAISS index
    index = faiss.read_index(index_path)

    # Embed question
    question_vector = embedding_model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    # Search
    distances, indices = index.search(question_vector, k)

    print("Similarity Scores:", distances)
    print("Retrieved Indices:", indices)

    results = []

    for idx in indices[0]:

        chunk = get_chunk(document_id, int(idx))

        if chunk:
            results.append(chunk)

    print("\nRetrieved Chunks:")
    print("=" * 80)

    for i, chunk in enumerate(results):
        print(f"Chunk {i+1}:")
        print(chunk[:300])
        print("-" * 80)
    return results