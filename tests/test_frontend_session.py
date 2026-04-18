from frontend.utils.session import append_chat_turn, initialize_state, record_uploaded_documents, reset_conversation


def test_initialize_state_sets_defaults() -> None:
    state = {}

    initialize_state(state)

    assert state["backend_url"] == "http://127.0.0.1:8000"
    assert state["uploaded_documents"] == []
    assert state["chat_history"] == []
    assert state["session_id"]


def test_record_uploaded_documents_deduplicates_by_document_id() -> None:
    state = {}
    initialize_state(state)

    record_uploaded_documents(
        state,
        [
            {"document_id": "doc-1", "filename": "one.txt", "chunks_extracted": 2, "status": "ingested"},
            {"document_id": "doc-1", "filename": "one.txt", "chunks_extracted": 2, "status": "ingested"},
        ],
    )

    assert len(state["uploaded_documents"]) == 1


def test_append_chat_turn_and_reset_conversation() -> None:
    state = {}
    initialize_state(state)
    previous_session_id = state["session_id"]

    append_chat_turn(
        state,
        question="What is DocuMind?",
        response={
            "answer": "DocuMind is a grounded document assistant.",
            "confidence_score": 0.72,
            "citations": [{"chunk_id": "chunk-1"}],
            "retrieved_chunks": [{"chunk_id": "chunk-1"}],
        },
    )
    new_session_id = reset_conversation(state)

    assert len(state["chat_history"]) == 0
    assert new_session_id != previous_session_id
