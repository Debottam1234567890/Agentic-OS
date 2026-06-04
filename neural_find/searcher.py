import os
import json
import math
import re
# pyrefly: ignore [missing-import]
import chromadb

db_client = chromadb.PersistentClient(path="./knowledge_base")
collection = db_client.get_or_create_collection(name="local_files")

KEYWORD_INDEX_PATH = os.path.join(os.path.dirname(__file__), "keyword_index.json")

# ─── BM25 Keyword Search Engine ───────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Split text into lowercase word tokens."""
    return re.findall(r'[a-z_][a-z0-9_]*', text.lower())

def _bm25_search(query: str, top_k: int = 5) -> list[dict]:
    """
    BM25 ranking over the keyword index.
    Returns a list of {source, score, snippet} dicts, sorted by score descending.
    """
    if not os.path.exists(KEYWORD_INDEX_PATH):
        return []

    with open(KEYWORD_INDEX_PATH, "r") as f:
        keyword_store = json.load(f)

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    N = len(keyword_store)  # total number of documents
    k1 = 1.5
    b = 0.75

    # Precompute document lengths and average
    doc_data = {}
    total_len = 0
    for filepath, content in keyword_store.items():
        tokens = _tokenize(content)
        doc_data[filepath] = {"tokens": tokens, "content": content, "length": len(tokens)}
        total_len += len(tokens)

    avgdl = total_len / max(N, 1)

    # Compute IDF for each query term
    idf = {}
    for term in query_tokens:
        df = sum(1 for d in doc_data.values() if term in d["tokens"])
        idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    # Score each document
    scored = []
    for filepath, data in doc_data.items():
        score = 0.0
        tokens = data["tokens"]
        dl = data["length"]
        
        for term in query_tokens:
            tf = tokens.count(term)
            if tf == 0:
                continue
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * dl / avgdl)
            score += idf[term] * (numerator / denominator)

        # Bonus: exact substring match in the raw content (case-insensitive)
        content_lower = data["content"].lower()
        query_lower = query.lower()
        if query_lower in content_lower:
            score += 5.0  # strong boost for exact substring match
            
        # Also boost if query appears in the filename
        if query_lower in filepath.lower():
            score += 3.0

        if score > 0:
            # Extract the best snippet around the first match
            snippet = _extract_snippet(data["content"], query)
            scored.append({"source": filepath, "score": score, "snippet": snippet})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def _extract_snippet(content: str, query: str, context_chars: int = 150) -> str:
    """Extract a text snippet centered around the first occurrence of the query."""
    idx = content.lower().find(query.lower())
    if idx == -1:
        # No exact match; return the beginning of the file
        return content[:300].strip()

    start = max(0, idx - context_chars)
    end = min(len(content), idx + len(query) + context_chars)
    snippet = content[start:end].strip()
    
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    
    return snippet


# ─── Semantic Vector Search ───────────────────────────────────────────────────

def _semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """ChromaDB vector similarity search. Returns list of {source, score, snippet}."""
    try:
        results = collection.query(query_texts=[query], n_results=top_k, include=["documents", "metadatas", "distances"])
    except Exception:
        return []

    if not results["documents"] or not results["documents"][0]:
        return []

    entries = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        # ChromaDB distance: lower = more similar. Convert to a score (higher = better).
        score = max(0, 1.0 / (1.0 + dist))
        snippet = doc.strip().replace('\n', ' ')
        if len(snippet) > 300:
            snippet = snippet[:300] + "..."
        entries.append({"source": meta["source"], "score": score, "snippet": snippet})

    return entries


# ─── Hybrid Merge (Reciprocal Rank Fusion) ────────────────────────────────────

def _merge_results(bm25_results: list[dict], semantic_results: list[dict], top_k: int = 5) -> list[dict]:
    """
    Reciprocal Rank Fusion (RRF) to merge BM25 and semantic results.
    Each result gets a score of 1/(k + rank) from each system, then summed.
    This is the same algorithm used by Elasticsearch and Azure AI Search.
    """
    K = 60  # RRF constant (industry standard)
    
    # Build a map of source -> best entry
    fused = {}  # source -> {source, rrf_score, snippet}

    for rank, entry in enumerate(bm25_results):
        src = entry["source"]
        rrf = 1.0 / (K + rank + 1)
        if src not in fused or rrf > fused[src]["rrf_score"]:
            fused[src] = {"source": src, "rrf_score": rrf, "snippet": entry["snippet"], "origin": "keyword"}
        else:
            fused[src]["rrf_score"] += rrf

    for rank, entry in enumerate(semantic_results):
        src = entry["source"]
        rrf = 1.0 / (K + rank + 1)
        if src in fused:
            fused[src]["rrf_score"] += rrf  # boost: appears in BOTH systems
            fused[src]["origin"] = "hybrid"
        else:
            fused[src] = {"source": src, "rrf_score": rrf, "snippet": entry["snippet"], "origin": "semantic"}

    # Sort by fused RRF score
    ranked = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)
    return ranked[:top_k]


# ─── Public API ───────────────────────────────────────────────────────────────

from rich.markup import escape

def semantic_search(query: str, top_k: int = 10) -> str:
    """
    Hybrid Search: runs BM25 keyword search AND ChromaDB semantic search,
    then merges results using Reciprocal Rank Fusion (RRF).
    """
    bm25_hits = _bm25_search(query, top_k=top_k * 2)
    vector_hits = _semantic_search(query, top_k=top_k * 2)
    merged = _merge_results(bm25_hits, vector_hits, top_k=top_k)

    if not merged:
        return "[red]No matching documents found.[/red]"

    origin_icons = {"keyword": "🔤", "semantic": "🧠", "hybrid": "⚡"}
    
    output = f"[bold green]Hybrid Search Results for:[/bold green] '{query}'\n\n"

    for i, entry in enumerate(merged):
        icon = origin_icons.get(entry["origin"], "•")
        snippet = entry["snippet"].replace('\n', ' ').strip()
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."
            
        escaped_snippet = escape(snippet)
        output += f"[bold yellow]{i + 1}. {icon}[/bold yellow] [dim]{entry['source']}[/dim]\n"
        output += f"[italic]{escaped_snippet}[/italic]\n\n"

    output += "[dim]🔤 = keyword match  🧠 = semantic match  ⚡ = hybrid (both)[/dim]\n"
    return output