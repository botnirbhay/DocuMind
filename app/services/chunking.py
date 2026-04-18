from enum import StrEnum

from app.services.documents import DocumentChunk, DocumentSection


class ChunkingStrategy(StrEnum):
    FIXED = "fixed"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"


def fixed_size_chunks(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    _validate_chunk_options(chunk_size, chunk_overlap)
    chunks: list[str] = []
    step = chunk_size - chunk_overlap

    for start in range(0, len(cleaned), step):
        chunk = cleaned[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(cleaned):
            break

    return chunks


def recursive_chunks(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    _validate_chunk_options(chunk_size, chunk_overlap)
    segments = _recursive_split(cleaned, chunk_size, separators=["\n\n", "\n", ". ", " "])
    merged = _merge_segments(segments, chunk_size)
    return _apply_overlap(merged, chunk_overlap)


def build_document_chunks(
    *,
    document_id: str,
    filename: str,
    file_type: str,
    upload_timestamp: str,
    sections: list[DocumentSection],
    strategy: ChunkingStrategy,
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    chunk_records: list[DocumentChunk] = []
    chunk_index = 0

    for section in sections:
        if strategy == ChunkingStrategy.FIXED:
            parts = fixed_size_chunks(section.text, chunk_size, chunk_overlap)
        elif strategy == ChunkingStrategy.RECURSIVE:
            parts = recursive_chunks(section.text, chunk_size, chunk_overlap)
        else:
            raise ValueError(f"Unsupported chunking strategy for Phase 2: {strategy}")

        for part in parts:
            chunk_records.append(
                DocumentChunk(
                    chunk_id=f"{document_id}-chunk-{chunk_index:04d}",
                    document_id=document_id,
                    filename=filename,
                    file_type=file_type,
                    upload_timestamp=upload_timestamp,
                    chunk_index=chunk_index,
                    text=part,
                    page_number=section.page_number,
                    preview=_preview_text(part),
                )
            )
            chunk_index += 1

    return chunk_records


def _validate_chunk_options(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be 0 or greater")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")


def _recursive_split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    if len(text) <= chunk_size:
        return [text.strip()]
    if not separators:
        return fixed_size_chunks(text, chunk_size, 0)

    separator = separators[0]
    parts = text.split(separator)
    if len(parts) == 1:
        return _recursive_split(text, chunk_size, separators[1:])

    results: list[str] = []
    buffer = ""

    for part in parts:
        candidate = part.strip()
        if not candidate:
            continue

        joined = candidate if not buffer else f"{buffer}{separator}{candidate}"
        if len(joined) <= chunk_size:
            buffer = joined
            continue

        if buffer:
            results.append(buffer.strip())
            buffer = ""

        if len(candidate) <= chunk_size:
            buffer = candidate
        else:
            results.extend(_recursive_split(candidate, chunk_size, separators[1:]))

    if buffer:
        results.append(buffer.strip())

    return results


def _merge_segments(segments: list[str], chunk_size: int) -> list[str]:
    if not segments:
        return []

    merged: list[str] = []
    current = segments[0]

    for segment in segments[1:]:
        candidate = f"{current}\n\n{segment}".strip()
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        merged.append(current.strip())
        current = segment

    merged.append(current.strip())
    return merged


def _apply_overlap(chunks: list[str], chunk_overlap: int) -> list[str]:
    if chunk_overlap == 0 or len(chunks) < 2:
        return chunks

    overlapped: list[str] = [chunks[0]]
    for previous, current in zip(chunks, chunks[1:]):
        prefix = previous[-chunk_overlap:].strip()
        if prefix and not current.startswith(prefix):
            overlapped.append(f"{prefix} {current}".strip())
        else:
            overlapped.append(current)
    return overlapped


def _preview_text(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3].rstrip()}..."
