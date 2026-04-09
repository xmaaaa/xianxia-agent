from __future__ import annotations

from typing import Any

from langchain_core.documents import Document

from app.core.config import settings
from app.rag.loader import load_skill_documents

_vectorstore: Any = None
_retriever: Any = None


def _has_valid_key() -> bool:
    key = settings.openai_api_key
    return bool(key and len(key) > 10)


def _embeddings():
    if not _has_valid_key():
        return None
    from langchain_openai import OpenAIEmbeddings

    kwargs: dict = {
        "api_key": settings.openai_api_key,
        "model": settings.openai_embedding_model,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAIEmbeddings(**kwargs)


def get_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore
    from langchain_chroma import Chroma

    emb = _embeddings()
    if emb is None:
        return None
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
    retriever = get_retriever()
    if retriever is None:
        return ""
    docs: list[Document] = retriever.invoke(query)
    if not docs:
        return ""
    parts = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "功法库")
        parts.append(f"[片段{i} | {src}]\n{d.page_content.strip()}")
    return "\n\n".join(parts)
