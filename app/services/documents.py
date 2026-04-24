from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DocumentSection:
    text: str
    page_number: int | None = None


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    filename: str
    file_type: str
    upload_timestamp: str
    chunk_index: int
    text: str
    page_number: int | None = None
    preview: str = ""


@dataclass(slots=True)
class DocumentRecord:
    document_id: str
    filename: str
    file_type: str
    upload_timestamp: str
    sections: list[DocumentSection]
    chunks: list[DocumentChunk]
    status: str
    stored_path: str | None = None


@dataclass
class DocumentRegistry:
    _documents: dict[str, DocumentRecord] = field(default_factory=dict)

    def add(self, document: DocumentRecord) -> None:
        self._documents[document.document_id] = document

    def get(self, document_id: str) -> DocumentRecord | None:
        return self._documents.get(document_id)

    def remove(self, document_id: str) -> DocumentRecord | None:
        return self._documents.pop(document_id, None)

    def list(self) -> list[DocumentRecord]:
        return list(self._documents.values())

    def clear(self) -> int:
        count = len(self._documents)
        self._documents.clear()
        return count

    def get_chunks(self, document_ids: list[str] | None = None) -> list[DocumentChunk]:
        allowed = set(document_ids) if document_ids is not None else None
        documents = self._documents.values()
        if allowed is not None:
            documents = [document for document in documents if document.document_id in allowed]
        return [chunk for document in documents for chunk in document.chunks]
