from __future__ import annotations

import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from docx import Document
from pypdf import PdfReader

from app.services.chunking import ChunkingStrategy, build_document_chunks
from app.services.documents import DocumentRecord, DocumentRegistry, DocumentSection
from app.utils.logging import get_logger

SUPPORTED_EXTENSIONS = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}
WHITESPACE_PATTERN = re.compile(r"[^\S\n]+")


class IngestionService(Protocol):
    def ingest(
        self,
        *,
        filename: str,
        content: bytes,
        strategy: ChunkingStrategy,
        chunk_size: int,
        chunk_overlap: int,
    ) -> DocumentRecord:
        """Extract content, normalize it, and register document metadata."""


class IngestionError(Exception):
    pass


class UnsupportedFileTypeError(IngestionError):
    pass


class DocumentReadError(IngestionError):
    pass


class EmptyDocumentError(IngestionError):
    pass


class LocalDocumentIngestionService:
    def __init__(self, registry: DocumentRegistry, upload_dir: Path) -> None:
        self._registry = registry
        self._upload_dir = upload_dir
        self._logger = get_logger(component="ingestion")

    def ingest(
        self,
        *,
        filename: str,
        content: bytes,
        strategy: ChunkingStrategy,
        chunk_size: int,
        chunk_overlap: int,
    ) -> DocumentRecord:
        start = perf_counter()
        file_type = detect_file_type(filename)
        if not content:
            raise EmptyDocumentError("Uploaded file is empty.")
        self._logger.info(
            "document_ingest_started",
            filename=filename,
            file_type=file_type,
            bytes=len(content),
            chunking_strategy=str(strategy),
        )

        extraction_start = perf_counter()
        sections = extract_sections(filename=filename, content=content, file_type=file_type)
        extraction_ms = round((perf_counter() - extraction_start) * 1000, 2)
        if not sections:
            raise EmptyDocumentError("No readable text could be extracted from the uploaded document.")

        document_id = uuid4().hex
        upload_timestamp = datetime.now(timezone.utc).isoformat()
        chunking_start = perf_counter()
        chunks = build_document_chunks(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            upload_timestamp=upload_timestamp,
            sections=sections,
            strategy=strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunking_ms = round((perf_counter() - chunking_start) * 1000, 2)
        if not chunks:
            raise EmptyDocumentError("Extracted text was empty after normalization.")

        stored_path = self._persist_upload(document_id=document_id, filename=filename, content=content)
        record = DocumentRecord(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            upload_timestamp=upload_timestamp,
            sections=sections,
            chunks=chunks,
            status="ingested",
            stored_path=str(stored_path),
        )
        self._registry.add(record)
        self._logger.info(
            "document_ingest_completed",
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            sections=len(sections),
            chunks=len(chunks),
            extraction_ms=extraction_ms,
            chunking_ms=chunking_ms,
            total_ms=round((perf_counter() - start) * 1000, 2),
        )
        return record

    def _persist_upload(self, *, document_id: str, filename: str, content: bytes) -> Path:
        suffix = Path(filename).suffix.lower()
        stored_path = self._upload_dir / f"{document_id}{suffix}"
        stored_path.write_bytes(content)
        return stored_path


def detect_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    file_type = SUPPORTED_EXTENSIONS.get(suffix)
    if not file_type:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedFileTypeError(f"Unsupported file type '{suffix or 'unknown'}'. Supported types: {supported}.")
    return file_type


def extract_sections(*, filename: str, content: bytes, file_type: str | None = None) -> list[DocumentSection]:
    resolved_type = file_type or detect_file_type(filename)
    if resolved_type == "pdf":
        return extract_pdf_sections(content)
    if resolved_type == "docx":
        return extract_docx_sections(content)
    if resolved_type == "txt":
        return extract_txt_sections(content)
    raise UnsupportedFileTypeError(f"Unsupported file type: {resolved_type}")


def extract_pdf_sections(content: bytes) -> list[DocumentSection]:
    try:
        reader = PdfReader(BytesIO(content))
    except Exception as exc:
        raise DocumentReadError("The PDF file could not be read.") from exc

    raw_pages = [page.extract_text() or "" for page in reader.pages]
    cleaned_pages = strip_repeated_headers_and_footers(raw_pages)
    sections: list[DocumentSection] = []

    for page_number, page_text in enumerate(cleaned_pages, start=1):
        normalized = normalize_text(page_text)
        if normalized:
            sections.append(DocumentSection(text=normalized, page_number=page_number))

    return sections


def extract_docx_sections(content: bytes) -> list[DocumentSection]:
    try:
        document = Document(BytesIO(content))
    except Exception as exc:
        raise DocumentReadError("The DOCX file could not be read.") from exc

    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text and paragraph.text.strip()]
    normalized = normalize_text("\n\n".join(paragraphs))
    return [DocumentSection(text=normalized, page_number=None)] if normalized else []


def extract_txt_sections(content: bytes) -> list[DocumentSection]:
    text = _decode_text_file(content)
    normalized = normalize_text(text)
    return [DocumentSection(text=normalized, page_number=None)] if normalized else []


def normalize_text(text: str) -> str:
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", normalized_newlines)
    paragraphs: list[str] = []

    for block in blocks:
        lines = [WHITESPACE_PATTERN.sub(" ", line).strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        paragraphs.append(" ".join(lines))

    return "\n\n".join(paragraphs).strip()


def strip_repeated_headers_and_footers(page_texts: list[str]) -> list[str]:
    if len(page_texts) < 2:
        return page_texts

    split_pages = [_non_empty_lines(text) for text in page_texts]
    header_counts: dict[str, int] = {}
    footer_counts: dict[str, int] = {}

    for lines in split_pages:
        if lines:
            header_counts[lines[0]] = header_counts.get(lines[0], 0) + 1
            footer_counts[lines[-1]] = footer_counts.get(lines[-1], 0) + 1

    cleaned_pages: list[str] = []
    for lines in split_pages:
        trimmed = list(lines)
        if trimmed and header_counts.get(trimmed[0], 0) > 1:
            trimmed = trimmed[1:]
        if trimmed and footer_counts.get(trimmed[-1], 0) > 1:
            trimmed = trimmed[:-1]
        cleaned_pages.append("\n".join(trimmed))

    return cleaned_pages


def _non_empty_lines(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [WHITESPACE_PATTERN.sub(" ", line).strip() for line in normalized.splitlines() if line.strip()]


def _decode_text_file(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise DocumentReadError("The TXT file could not be decoded with a supported text encoding.")
