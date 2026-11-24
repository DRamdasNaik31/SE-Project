"""Optional embedding index with a deterministic lexical fallback.

The fallback remains the default so the application works without model
downloads. When sentence-transformers and Chroma are installed, `build_index`
creates a local persistent index while preserving page/module metadata.
"""

import json
from pathlib import Path
from typing import Any


def build_index(
    corpus_path: Path = Path("data/processed/requirements_all.json"),
    persist_dir: Path = Path("chroma_db"),
    collection_name: str = "finance_requirements",
) -> dict[str, Any]:
    if not corpus_path.is_file():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Embedding RAG requires sentence-transformers and chromadb. "
            "Install requirements-ml.txt first."
        ) from exc
    items = json.loads(corpus_path.read_text(encoding="utf-8"))
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(collection_name)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    documents = [str(item["text"]) for item in items]
    collection.upsert(
        ids=[str(item["id"]) for item in items],
        documents=documents,
        embeddings=model.encode(documents).tolist(),
        metadatas=[{"module": item["module"], "page": item["page"]} for item in items],
    )
    return {"collection": collection_name, "documents": len(items), "persist_dir": str(persist_dir)}
