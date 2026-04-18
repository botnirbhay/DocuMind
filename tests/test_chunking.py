from app.services.chunking import fixed_size_chunks, recursive_chunks


def test_fixed_size_chunking_applies_overlap() -> None:
    text = "abcdefghijklmnopqrstuvwxyz"

    chunks = fixed_size_chunks(text, chunk_size=10, chunk_overlap=2)

    assert chunks == ["abcdefghij", "ijklmnopqr", "qrstuvwxyz"]


def test_recursive_chunking_prefers_paragraph_boundaries() -> None:
    text = "Alpha paragraph.\n\nBeta paragraph.\n\nGamma paragraph."

    chunks = recursive_chunks(text, chunk_size=20, chunk_overlap=0)

    assert chunks == ["Alpha paragraph.", "Beta paragraph.", "Gamma paragraph."]
