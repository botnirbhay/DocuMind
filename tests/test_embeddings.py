from app.services.embeddings import HashEmbeddingProvider, SentenceTransformerEmbeddingProvider


def test_hash_embedding_provider_returns_stable_vectors() -> None:
    provider = HashEmbeddingProvider(dimensions=16)

    first = provider.embed(["alpha beta"])[0]
    second = provider.embed(["alpha beta"])[0]

    assert first == second
    assert len(first) == 16
    assert any(value != 0.0 for value in first)


def test_sentence_transformer_provider_falls_back_to_hash(monkeypatch) -> None:
    provider = SentenceTransformerEmbeddingProvider("sentence-transformers/all-MiniLM-L6-v2")

    def raise_failure():
        raise OSError("torch DLL failed")

    monkeypatch.setattr(provider, "_get_model", raise_failure)

    vector = provider.embed(["alpha beta"])[0]

    assert len(vector) == 64
    assert any(value != 0.0 for value in vector)
