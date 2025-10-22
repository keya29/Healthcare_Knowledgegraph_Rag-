# ingest/chunk_loader.py
import os
from types import SimpleNamespace
from .text_splitter import Chunker  # import from text_splitter.py

# Prefer LangChain's PyPDFLoader when available, but provide a lightweight
# fallback using PyPDF2 so the project can run without langchain_community.
try:
    from langchain_community.document_loaders import PyPDFLoader  # type: ignore
    _HAS_LANGCHAIN_LOADER = True
except Exception:
    _HAS_LANGCHAIN_LOADER = False
    try:
        from PyPDF2 import PdfReader  # type: ignore
    except Exception:
        PdfReader = None

def load_chunks(pdf_folder):
    """
    Returns a list of chunk objects:
    chunk.page_content, chunk.metadata
    """
    chunker = Chunker()
    chunks = []

    global_counter = 0
    for filename in os.listdir(pdf_folder):
        if not filename.lower().endswith(".pdf"):
            continue

        abs_path = os.path.join(pdf_folder, filename)

        if _HAS_LANGCHAIN_LOADER:
            loader = PyPDFLoader(abs_path)
            docs = loader.load()
            doc_chunks = chunker.chunk(docs)
        else:
            # Fallback: read PDF pages as plain text using PyPDF2 PdfReader
            doc_texts = []
            if PdfReader is None:
                # If neither loader is available, skip this file but warn via empty text
                doc_texts = [""]
            else:
                try:
                    reader = PdfReader(abs_path)
                    for page in reader.pages:
                        try:
                            doc_texts.append(page.extract_text() or "")
                        except Exception:
                            doc_texts.append("")
                except Exception:
                    doc_texts = [""]

            # Build simple doc-like objects for the splitter
            class _SimpleDoc:
                def __init__(self, page_content, metadata=None):
                    self.page_content = page_content
                    self.metadata = metadata or {}

            docs = [_SimpleDoc(t) for t in doc_texts]
            doc_chunks = chunker.chunk(docs)

        for c in doc_chunks:
            # create a stable, global chunk id used by Neo4j ingestion
            chunk_id = f"chunk_{global_counter}"
            md = {
                "source": filename,
                "chunk_id": chunk_id,
                # preserve any per-doc metadata the splitter provided
                **(getattr(c, "metadata", {}) or {}),
            }
            chunks.append(
                SimpleNamespace(
                    page_content=c.page_content,
                    metadata=md,
                )
            )
            global_counter += 1
    return chunks
