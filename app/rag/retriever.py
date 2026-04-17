from __future__ import annotations

import logging
import os
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.rag.loader import load_skill_documents

logger = logging.getLogger("app.rag.retriever")

_vectorstore: Any = None
_retriever: Any = None


class _SentenceTransformerEmbeddings(Embeddings):
    """Lightweight LangChain-compatible wrapper around sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        hf_endpoint = os.environ.get("HF_ENDPOINT", "")
        if not hf_endpoint:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode([text], show_progress_bar=False)[0].tolist()


def _embeddings() -> Embeddings:
    return _SentenceTransformerEmbeddings()


def get_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore
    from langchain_chroma import Chroma

    emb = _embeddings()
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    _vectorstore = Chroma(
        embedding_function=emb,
        persist_directory=str(settings.chroma_persist_dir),
        collection_name="xianxia_skills",
    )
    try:
        count = _vectorstore._collection.count()
    except Exception:
        count = 0
    if count == 0:
        docs = load_skill_documents()
        if docs:
            _vectorstore.add_documents(docs)
    return _vectorstore


def get_retriever():
    global _retriever
    if _retriever is not None:
        return _retriever
    vs = get_vectorstore()
    if vs is None:
        return None
    _retriever = vs.as_retriever(search_kwargs={"k": 4})
    return _retriever


def retrieve_context_text(query: str) -> str:
    if not query.strip():
        return ""
    try:
        retriever = get_retriever()
        if retriever is None:
            return ""
        docs: list[Document] = retriever.invoke(query)
    except Exception:
        logger.exception("RAG retrieval failed, returning empty context")
        return ""
    if not docs:
        return ""
    parts = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "功法库")
        parts.append(f"[片段{i} | {src}]\n{d.page_content.strip()}")
    return "\n\n".join(parts)
