from frontend.utils.session import initialize_state, reset_conversation


def test_reset_conversation_clears_search_results_and_status() -> None:
    state = {}
    initialize_state(state)
    state["chat_history"] = [{"question": "Q"}]
    state["search_results"] = [{"chunk_id": "chunk-1"}]
    state["status_message"] = ("info", "hello")

    reset_conversation(state)

    assert state["chat_history"] == []
    assert state["search_results"] == []
    assert state["status_message"] is None
