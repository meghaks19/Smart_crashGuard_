"""Local FAISS retrieval with optional OpenAI wording; retrieval works without an API key."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

class EmergencyRAG:
    def __init__(self, knowledge_dir: str, index_path: str, metadata_path: str, embedding_model: str, top_k: int = 3):
        self.knowledge_dir, self.index_path, self.metadata_path = Path(knowledge_dir), Path(index_path), Path(metadata_path)
        self.embedding_model, self.top_k, self.encoder, self.index, self.chunks = embedding_model, top_k, None, None, []
    def build(self):
        import faiss
        from sentence_transformers import SentenceTransformer
        files = list(self.knowledge_dir.rglob("*.md")) + list(self.knowledge_dir.rglob("*.txt"))
        if not files: raise FileNotFoundError(f"No .md or .txt knowledge files in {self.knowledge_dir}")
        self.chunks = [p.read_text(encoding="utf-8").strip() for p in files if p.read_text(encoding="utf-8").strip()]
        self.encoder = SentenceTransformer(self.embedding_model)
        vectors = self.encoder.encode(self.chunks, normalize_embeddings=True).astype("float32")
        self.index = faiss.IndexFlatIP(vectors.shape[1]); self.index.add(vectors)
        self.index_path.parent.mkdir(parents=True, exist_ok=True); faiss.write_index(self.index, str(self.index_path))
        self.metadata_path.write_text(json.dumps(self.chunks, ensure_ascii=False), encoding="utf-8")
    def _load(self):
        if self.index is not None: return
        import faiss
        from sentence_transformers import SentenceTransformer
        if not self.index_path.exists() or not self.metadata_path.exists(): self.build(); return
        self.encoder = SentenceTransformer(self.embedding_model); self.index = faiss.read_index(str(self.index_path))
        self.chunks = json.loads(self.metadata_path.read_text(encoding="utf-8"))
    def retrieve(self, question: str) -> list[str]:
        self._load(); vector = self.encoder.encode([question], normalize_embeddings=True).astype("float32")
        _, ids = self.index.search(vector, min(self.top_k, len(self.chunks)))
        return [self.chunks[i] for i in ids[0] if i >= 0]
    def answer(self, question: str, use_openai: bool = False) -> str:
        context = "\n\n".join(self.retrieve(question))
        if not use_openai: return context
        from openai import OpenAI
        response = OpenAI().responses.create(model=__import__('os').getenv("OPENAI_MODEL", "gpt-4.1-mini"), store=False,
            input=f"Use only this emergency reference. Give brief, non-medical information.\nREFERENCE:\n{context}\n\nQUESTION: {question}")
        return response.output_text
