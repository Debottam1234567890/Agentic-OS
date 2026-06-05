import os
import json
import math
import chromadb
db_client = chromadb.PersistentClient(path='./knowledge_base')
collection = db_client.get_or_create_collection(name='local_files')
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'node_modules', '.idea', 'knowledge_base'}
ALLOWED_EXTENSIONS = {'.py', '.js', '.html', '.css', '.md', '.txt', '.json', '.xml', '.yml', '.yaml', '.sh', '.bash', '.zsh', '.fish', '.sql', '.java', '.c', '.cpp', '.cs', '.go', '.php', '.rb', '.ts', '.tsx'}
KEYWORD_INDEX_PATH = os.path.join(os.path.dirname(__file__), 'keyword_index.json')
def chunk_text(text, max_chars=10000):
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
def build_index(root_dir='.'):
    docs = []
    metadatas = []
    ids = []
    doc_id = 0
    keyword_store = {}
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue
            full_path = os.path.join(root, filename)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue
            keyword_store[full_path] = content
            chunks = chunk_text(content)
            for chunk in chunks:
                doc_id += 1
                docs.append(chunk)
                metadatas.append({'source': full_path, 'chunk': doc_id})
                ids.append(str(doc_id))
    if docs:
        collection.upsert(documents=docs, metadatas=metadatas, ids=ids)
    with open(KEYWORD_INDEX_PATH, 'w') as f:
        json.dump(keyword_store, f)
    print(f'Indexed {len(keyword_store)} files ({doc_id} chunks)')
