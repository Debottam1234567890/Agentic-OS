import os
import json
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
import numpy as np
if not hasattr(np, 'float_'):
    np.float_ = np.float64
import chromadb
from PyPDF2 import PdfReader
import sqlite3

def check_and_clear_incompatible_db(db_path):
    sqlite_file = os.path.join(db_path, "chroma.sqlite3")
    if os.path.exists(sqlite_file):
        try:
            conn = sqlite3.connect(sqlite_file)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(collections)")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            # If the database has the 'topic' column, it was created by a newer version of ChromaDB (e.g. 1.5.9)
            if "topic" in columns:
                import shutil
                shutil.rmtree(db_path)
                print(f"Wiped incompatible newer ChromaDB schema at {db_path}")
        except Exception:
            pass

check_and_clear_incompatible_db('./physics_db')
chroma_client = chromadb.PersistentClient(path='./physics_db')
collection = chroma_client.get_or_create_collection(name='physics_vault')
LEDGER_FILE = '.ingested.json'
def _load_ledger():
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            return json.load(f)
    return []
def _save_ledger(ledger):
    with open(LEDGER_FILE, 'w') as f:
        json.dump(ledger, f, indent=4)
def auto_ingest(directory: str):
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    ledger = _load_ledger()
    for pdf_name in pdf_files:
        if pdf_name in ledger:
            continue
        try:
            pdf_path = os.path.join(directory, pdf_name)
            reader = PdfReader(pdf_path)
            text = ''
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + '\n'
            chunks = []
            current_chunk = ''
            for char in text:
                current_chunk += char
                if len(current_chunk) >= 500:
                    chunks.append(current_chunk)
                    current_chunk = ''
            if current_chunk:
                chunks.append(current_chunk)
            if chunks:
                collection.upsert(documents=chunks, ids=[f'{pdf_name}_chunk_{i}' for i in range(len(chunks))])
            ledger.append(pdf_name)
            _save_ledger(ledger)
        except Exception:
            print(f'Skipping locked/corrupted file: {pdf_name}')
def retrieve(query: str) -> str:
    auto_ingest(os.getcwd())
    results = collection.query(query_texts=[query], n_results=3)
    if results['documents'] and results['documents'][0]:
        return '\n\n...\n\n'.join(results['documents'][0])
    return 'No relevant context found in the vault.'
