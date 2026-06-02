import os
import json
# CRITICAL: Must be set BEFORE importing chromadb/tokenizers to prevent
# macOS fork() crash inside Textual's threaded workers.
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# pyrefly: ignore [missing-import]
import chromadb
from PyPDF2 import PdfReader

# Persistent ChromaDB client — survives across queries
chroma_client = chromadb.PersistentClient(path="./physics_db")
collection = chroma_client.get_or_create_collection(name="physics_vault")

# Ledger file tracks which PDFs have already been ingested
LEDGER_FILE = ".ingested.json"


def _load_ledger():
    """Reads the ingestion ledger from disk."""
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "r") as f:
            return json.load(f)
    return []


def _save_ledger(ledger):
    """Writes the ingestion ledger to disk."""
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=4)


def auto_ingest(directory: str):
    """JIT ingestion: scans directory for new PDFs and upserts chunks into the vault.
    Skips files already recorded in the .ingested.json ledger."""
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith(".pdf")]
    ledger = _load_ledger()

    for pdf_name in pdf_files:
        # Skip already-ingested files
        if pdf_name in ledger:
            continue

        try:
            pdf_path = os.path.join(directory, pdf_name)

            # Extract full text from all pages
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

            # Chunk by 500 characters
            chunks = []
            current_chunk = ""
            for char in text:
                current_chunk += char
                if len(current_chunk) >= 500:
                    chunks.append(current_chunk)
                    current_chunk = ""

            # Catch remaining characters
            if current_chunk:
                chunks.append(current_chunk)

            if chunks:
                collection.upsert(
                    documents=chunks,
                    ids=[f"{pdf_name}_chunk_{i}" for i in range(len(chunks))],
                )

            # Record successful ingestion in the ledger
            ledger.append(pdf_name)
            _save_ledger(ledger)

        except Exception:
            print(f"Skipping locked/corrupted file: {pdf_name}")


def retrieve(query: str) -> str:
    """Auto-ingests new PDFs from cwd, then queries the vault."""
    auto_ingest(os.getcwd())

    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    if results["documents"] and results["documents"][0]:
        return "\n\n...\n\n".join(results["documents"][0])

    return "No relevant context found in the vault."