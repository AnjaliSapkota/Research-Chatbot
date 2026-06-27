import sqlite3
import os


DB_NAME = "chatbot.db"


# Create Connection

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

# Documents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (

            document_id TEXT PRIMARY KEY,

            filename TEXT NOT NULL,

            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

# Chunks Table

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            document_id TEXT NOT NULL,

            chunk_index INTEGER NOT NULL,

            chunk_text TEXT NOT NULL,

            FOREIGN KEY(document_id)
            REFERENCES documents(document_id)

        )
    """)

    
# Chat History (future use)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            document_id TEXT,

            question TEXT,

            answer TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()
    conn.close()


# Save Document
def save_document(document_id, filename):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO documents
        (document_id, filename)

        VALUES (?, ?)
    """, (document_id, filename))

    conn.commit()
    conn.close()


# Save All Chunks
def save_chunks(document_id, chunks):

    conn = get_connection()
    cursor = conn.cursor()

    for index, chunk in enumerate(chunks):

        cursor.execute("""
            INSERT INTO chunks

            (
                document_id,
                chunk_index,
                chunk_text
            )

            VALUES (?, ?, ?)

        """, (

            document_id,
            index,
            chunk

        ))

    conn.commit()
    conn.close()


# Get Chunk
def get_chunk(document_id, chunk_index):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT chunk_text

        FROM chunks

        WHERE document_id=?
        AND chunk_index=?

    """, (

        document_id,
        chunk_index

    ))

    row = cursor.fetchone()

    conn.close()

    if row:
        return row["chunk_text"]

    return None


# Get All Chunks
def get_all_chunks(document_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT chunk_text

        FROM chunks

        WHERE document_id=?

        ORDER BY chunk_index

    """, (document_id,))

    rows = cursor.fetchall()

    conn.close()

    return [row["chunk_text"] for row in rows]


# Save Chat History
def save_chat(question, answer, document_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO chat_history

        (
            document_id,
            question,
            answer
        )

        VALUES (?, ?, ?)

    """, (

        document_id,
        question,
        answer

    ))

    conn.commit()
    conn.close()


# Load Chat History
def load_chat(document_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            question,
            answer,
            created_at

        FROM chat_history

        WHERE document_id=?

        ORDER BY id ASC

    """, (document_id,))

    history = cursor.fetchall()

    conn.close()

    return history


# Delete Document
def delete_document(document_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

        DELETE FROM chunks

        WHERE document_id=?

    """, (document_id,))

    cursor.execute("""

        DELETE FROM documents

        WHERE document_id=?

    """, (document_id,))

    conn.commit()
    conn.close()


# List Uploaded Documents
def list_documents():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM documents

        ORDER BY upload_time DESC

    """)

    docs = cursor.fetchall()

    conn.close()

    return docs