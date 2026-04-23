from app.services.chunking import fixed_size_chunks, recursive_chunks


def test_fixed_size_chunking_applies_overlap() -> None:
    text = "abcdefghijklmnopqrstuvwxyz"

    chunks = fixed_size_chunks(text, chunk_size=10, chunk_overlap=2)

    assert chunks == ["abcdefghij", "ijklmnopqr", "qrstuvwxyz"]


def test_recursive_chunking_prefers_paragraph_boundaries() -> None:
    text = "Alpha paragraph.\n\nBeta paragraph.\n\nGamma paragraph."

    chunks = recursive_chunks(text, chunk_size=20, chunk_overlap=0)

    assert chunks == ["Alpha paragraph.", "Beta paragraph.", "Gamma paragraph."]


def test_recursive_chunking_keeps_heading_with_following_content() -> None:
    text = "Eligibility\n\nApplicants must submit a completed form and proof of identity.\n\nTimeline\n\nReviews take 7 business days."

    chunks = recursive_chunks(text, chunk_size=90, chunk_overlap=0)

    assert chunks == [
        "Eligibility\n\nApplicants must submit a completed form and proof of identity.",
        "Timeline\n\nReviews take 7 business days.",
    ]


def test_recursive_chunking_groups_consecutive_bullets_under_heading() -> None:
    text = "Requirements\n\n- Submit a signed form\n\n- Include supporting documents\n\n- Provide contact information"

    chunks = recursive_chunks(text, chunk_size=120, chunk_overlap=0)

    assert chunks == [
        "Requirements\n\n- Submit a signed form\n\n- Include supporting documents\n\n- Provide contact information"
    ]
