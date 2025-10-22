"""ingest/text_splitter.py

Provides a small Chunker wrapper around a LangChain text splitter.
This module intentionally keeps a minimal API: Chunker(chunk_size, chunk_overlap)
with a .chunk(docs) method that returns a list of objects with `page_content` and `metadata`.
"""
from __future__ import annotations

from typing import List, Iterable

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    _HAS_LANGCHAIN_SPLITTER = True
except Exception:
    RecursiveCharacterTextSplitter = None  # type: ignore
    _HAS_LANGCHAIN_SPLITTER = False


class Chunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        if _HAS_LANGCHAIN_SPLITTER:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )

    def _simple_split(self, text: str) -> List[str]:
        # naive sentence/character-based splitter to use when LangChain is not installed
        if not text:
            return [""]
        parts = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            parts.append(text[start:end])
            start = end - self.chunk_overlap if end < len(text) else end
        return parts

    def chunk(self, docs: Iterable) -> List:
        """Split Document-like objects or strings into chunk objects with
        `page_content` and `metadata` attributes.
        """
        texts = []
        metadatas = []
        for d in docs:
            if hasattr(d, "page_content"):
                texts.append(d.page_content)
                metadatas.append(getattr(d, "metadata", {}) or {})
            else:
                texts.append(str(d))
                metadatas.append({})

        split_docs = []
        for i, t in enumerate(texts):
            if _HAS_LANGCHAIN_SPLITTER:
                parts = self.splitter.split_text(t)
            else:
                parts = self._simple_split(t)

            for j, p in enumerate(parts):
                class _Chunk:
                    def __init__(self, page_content, metadata):
                        self.page_content = page_content
                        self.metadata = metadata

                md = dict(metadatas[i]) if metadatas else {}
                md.update({"source_index": i, "part_index": j})
                split_docs.append(_Chunk(p, md))

        return split_docs
