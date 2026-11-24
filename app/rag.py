"""Source-grounded retrieval with a dependency-light lexical fallback."""

import json
import re
from pathlib import Path
from typing import Any


class Retriever:
    def __init__(self, corpus_path: Path = Path("data/processed/requirements_all.json")):
        self.corpus_path = corpus_path
        self.items: list[dict[str, Any]] = []
        self._embedding_collection = None
        self._embedding_model = None
        self._embedding_disabled = False
        if corpus_path.exists():
            self.items = json.loads(corpus_path.read_text(encoding="utf-8"))

    def retrieve(self, query: str, k: int = 6, module: str | None = None) -> list[dict[str, Any]]:
        if module:
            return self._retrieve_all_module(query, module)
        embedded = self._retrieve_embeddings(query, k, module)
        if embedded:
            return embedded
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        candidates = self.items
        if module:
            narrowed = [item for item in candidates if item["module"].lower() == module.lower()]
            candidates = narrowed or candidates
        scored = []
        for item in candidates:
            words = set(re.findall(r"[a-z0-9]+", str(item["text"]).lower()))
            score = len(terms & words) / max(1, len(terms))
            if module and str(item["module"]).lower() == module.lower():
                score += 0.25
            scored.append({
                **item,
                "source_text": item.get("source_text", item.get("text", "")),
                "score": round(min(score, 1.0), 4),
            })
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:k]

    def _retrieve_all_module(self, query: str, module: str) -> list[dict[str, Any]]:
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        selected = [
            item for item in self.items
            if str(item["module"]).lower() == module.lower()
        ]
        scored = []
        for item in selected:
            words = set(re.findall(r"[a-z0-9]+", str(item["text"]).lower()))
            score = len(terms & words) / max(1, len(terms))
            scored.append({
                **item,
                "source_text": item.get("text", ""),
                "score": round(min(score, 1.0), 4),
            })
        return sorted(scored, key=lambda item: (-item["score"], int(item["page"])))

    def _retrieve_embeddings(self, query: str, k: int, module: str | None) -> list[dict[str, Any]]:
        if self._embedding_disabled or not Path("chroma_db").is_dir():
            return []
        try:
            if self._embedding_collection is None:
                import chromadb
                from sentence_transformers import SentenceTransformer
                client = chromadb.PersistentClient(path="chroma_db")
                self._embedding_collection = client.get_collection("finance_requirements")
                self._embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            result = self._embedding_collection.query(
                query_embeddings=self._embedding_model.encode([query]).tolist(),
                n_results=min(max(k * 4, k), len(self.items)),
            )
        except (ImportError, RuntimeError, ValueError, AttributeError, OSError):
            self._embedding_disabled = True
            self._embedding_collection = None
            self._embedding_model = None
            return []
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        by_id = {str(item["id"]): item for item in self.items}
        output = []
        for identifier, distance in zip(ids, distances):
            item = by_id.get(str(identifier))
            if not item or (module and item["module"].lower() != module.lower()):
                continue
            output.append({
                **item,
                "source_text": item.get("text", ""),
                "score": round(1.0 / (1.0 + float(distance)), 4),
            })
        return output

    def guess_module(self, query: str) -> str | None:
        query_lower = query.lower()
        modules = {str(item["module"]) for item in self.items}
        if any(term in query_lower for term in ("agentic ai", "problem statement", "proposed system")):
            if "Agentic AI Requirements" in modules:
                return "Agentic AI Requirements"
        return next((module for module in modules if module.lower() in query_lower), None)


_default = Retriever()


def retrieve(query: str, k: int = 6, module: str | None = None) -> list[dict[str, Any]]:
    return _default.retrieve(query, k, module)


def guess_module(query: str) -> str | None:
    return _default.guess_module(query)
