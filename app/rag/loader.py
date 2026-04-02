from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

RAG_DIR = Path(__file__).resolve().parent
SKILLS_PATH = RAG_DIR / "knowledge" / "skills.md"


def load_skill_documents() -> list[Document]:
    if not SKILLS_PATH.is_file():
        return []
    text = SKILLS_PATH.read_text(encoding="utf-8")
    base = Document(page_content=text, metadata={"source": "skills.md"})
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        separators=["\n## ", "\n# ", "\n\n", "\n", " "],
    )
    return splitter.split_documents([base])
