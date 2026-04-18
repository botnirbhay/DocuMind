from app.services.embeddings import HashEmbeddingProvider


def test_hash_embedding_provider_returns_stable_vectors() -> None:
    provider = HashEmbeddingProvider(dimensions=16)

    first = provider.embed(["alpha beta"])[0]
    second = provider.embed(["alpha beta"])[0]

    assert first == second
    assert len(first) == 16
    assert any(value != 0.0 for value in first)
