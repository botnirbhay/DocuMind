from app.services.reranker import NoOpReranker, SentenceTransformerReranker
from app.services.vector_store import VectorSearchMatch
from tests.test_retrieval import _build_document_record


def test_noop_reranker_preserves_existing_order() -> None:
    matches = [
        _build_match("doc-1", "one.txt", "Alpha chunk", 0.8),
        _build_match("doc-1", "one.txt", "Beta chunk", 0.6),
    ]

    reranked = NoOpReranker().rerank(query="alpha", matches=matches, top_k=1)

    assert reranked == [matches[0]]


def test_sentence_transformer_reranker_uses_model_scores(monkeypatch) -> None:
    reranker = SentenceTransformerReranker("cross-encoder/ms-marco-MiniLM-L-6-v2")

    class FakeModel:
        def predict(self, pairs):
            assert len(pairs) == 2
            return [0.1, 2.2]

    monkeypatch.setattr(reranker, "_get_model", lambda: FakeModel())
    matches = [
        _build_match("doc-1", "guide.txt", "General guidance", 0.9),
        _build_match("doc-1", "guide.txt", "Appeal review timeline is seven business days.", 0.4),
    ]

    reranked = reranker.rerank(query="appeal review timeline", matches=matches, top_k=2)

    assert reranked[0].chunk.text == "Appeal review timeline is seven business days."
    assert reranked[0].score > reranked[1].score


def test_sentence_transformer_reranker_falls_back_cleanly(monkeypatch) -> None:
    reranker = SentenceTransformerReranker("cross-encoder/ms-marco-MiniLM-L-6-v2")
    monkeypatch.setattr(reranker, "_get_model", lambda: (_ for _ in ()).throw(RuntimeError("missing torch")))
    matches = [
        _build_match("doc-1", "guide.txt", "General guidance", 0.9),
        _build_match("doc-1", "guide.txt", "Appeal review timeline is seven business days.", 0.4),
    ]

    reranked = reranker.rerank(query="appeal review timeline", matches=matches, top_k=2)

    assert reranked == matches


def _build_match(document_id: str, filename: str, text: str, score: float) -> VectorSearchMatch:
    record = _build_document_record(document_id, filename, [text])
    return VectorSearchMatch(chunk=record.chunks[0], score=score)
