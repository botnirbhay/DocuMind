from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.services.api_client import DocuMindApiClient, DocuMindApiError, UploadPayload
from frontend.utils.session import append_chat_turn, initialize_state, record_uploaded_documents, reset_conversation

FALLBACK_ANSWER = "I dont have enough information from the provided documents."

st.set_page_config(
    page_title="DocuMind",
    page_icon="DM",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_state(st.session_state)
if "backend_url_input" not in st.session_state:
    st.session_state["backend_url_input"] = os.getenv("DOCUMIND_API_URL", st.session_state["backend_url"])

DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"


def main() -> None:
    _inject_styles()

    backend_url = _sync_backend_url()
    api_client = DocuMindApiClient(base_url=backend_url)

    try:
        system_status = api_client.get_system_status()
    except DocuMindApiError as exc:
        system_status = None
        backend_error = str(exc)
    else:
        backend_error = None

    _render_sidebar(api_client, system_status, backend_error)
    _render_main(api_client, system_status, backend_error)
    api_client.close()


def _render_sidebar(api_client: DocuMindApiClient, system_status: dict | None, backend_error: str | None) -> None:
    with st.sidebar:
        st.markdown("## DocuMind")
        st.caption("Upload files, build the index, then ask grounded questions.")

        st.text_input(
            "Backend URL",
            key="backend_url_input",
            help="Defaults to the local FastAPI backend. Change this only if your API is running elsewhere.",
        )
        st.caption(f"Current target: `{st.session_state['backend_url_input'].strip() or DEFAULT_BACKEND_URL}`")

        if backend_error:
            st.error(backend_error)
        elif system_status:
            st.success(f"Connected to {system_status['app_name']}")
        else:
            st.warning("Backend status is unavailable.")

        st.divider()
        st.markdown("### Upload documents")
        uploaded_files = st.file_uploader(
            "Add PDFs, DOCX files, or TXT notes",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="DocuMind ingests one or more files and prepares them for grounded retrieval.",
        )
        chunking_strategy = st.selectbox(
            "Chunking strategy",
            options=["recursive", "fixed"],
            index=0,
            help="Recursive keeps paragraphs intact when possible. Fixed uses strict chunk sizes.",
        )
        chunk_size = st.slider("Chunk size", min_value=200, max_value=1600, value=800, step=100)
        chunk_overlap = st.slider("Chunk overlap", min_value=0, max_value=400, value=120, step=20)
        if st.button("Upload documents", use_container_width=True, type="primary"):
            if not uploaded_files:
                st.warning("Choose at least one document before uploading.")
            else:
                try:
                    with st.spinner("Uploading and extracting document chunks..."):
                        response = api_client.upload_documents(
                            files=[
                                UploadPayload(path=Path(file.name), content=file.getvalue())
                                for file in uploaded_files
                            ],
                            chunking_strategy=chunking_strategy,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                        )
                    record_uploaded_documents(st.session_state, response["documents"])
                    st.session_state["status_message"] = (
                        "success",
                        f"Uploaded {len(response['documents'])} document(s).",
                    )
                    st.rerun()
                except DocuMindApiError as exc:
                    st.session_state["status_message"] = ("error", str(exc))
                    st.rerun()

        st.divider()
        st.markdown("### Index documents")
        documents = st.session_state["uploaded_documents"]
        options = [doc["filename"] for doc in documents]
        selected_filenames = st.multiselect(
            "Choose documents to index",
            options=options,
            default=options,
            help="Leave everything selected to build a multi-document index.",
            disabled=not options,
        )
        selected_ids = [item["document_id"] for item in documents if item["filename"] in selected_filenames]
        if st.button("Build index", use_container_width=True, disabled=not documents):
            try:
                with st.spinner("Building vector index..."):
                    payload = selected_ids or None
                    response = api_client.index_documents(payload)
                st.session_state["last_index_result"] = response
                st.session_state["status_message"] = (
                    "success",
                    f"Indexed {response['total_chunks_indexed']} chunk(s).",
                )
                st.rerun()
            except DocuMindApiError as exc:
                st.session_state["status_message"] = ("error", str(exc))
                st.rerun()

        st.divider()
        st.markdown("### Session")
        st.code(st.session_state["session_id"], language="text")
        session_metrics = st.columns(2)
        session_metrics[0].metric("Turns", len(st.session_state["chat_history"]))
        session_metrics[1].metric("Results", len(st.session_state["search_results"]))
        if st.button("New chat session", use_container_width=True):
            reset_conversation(st.session_state)
            st.session_state["status_message"] = ("info", "Started a fresh session.")
            st.rerun()

        st.divider()
        st.markdown("### Status")
        _render_status_badges(system_status)


def _render_main(api_client: DocuMindApiClient, system_status: dict | None, backend_error: str | None) -> None:
    st.markdown(
        """
        <div class="hero-card">
          <div class="eyebrow">Document QA</div>
          <h1>DocuMind</h1>
          <p>Search and chat across your documents with citations, confidence signals, and clean source previews.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_status_message()

    if backend_error:
        st.info("Start the FastAPI backend, then refresh this page to begin.")
        return

    _render_top_summary()

    tab_chat, tab_search, tab_library = st.tabs(["Chat", "Search", "Library"])
    with tab_chat:
        _render_chat_panel(api_client)
    with tab_search:
        _render_search_panel(api_client)
    with tab_library:
        _render_document_summary()
        st.markdown("### Service status")
        _render_system_panel(system_status)


def _render_top_summary() -> None:
    documents = st.session_state["uploaded_documents"]
    metrics = st.columns(4)
    metrics[0].metric("Documents", len(documents))
    metrics[1].metric("Chunks", sum(item["chunks_extracted"] for item in documents))
    metrics[2].metric(
        "Indexed",
        st.session_state["last_index_result"]["total_chunks_indexed"]
        if st.session_state["last_index_result"]
        else 0,
    )
    metrics[3].metric("Chat turns", len(st.session_state["chat_history"]))


def _render_document_summary() -> None:
    st.markdown("### Document library")
    documents = st.session_state["uploaded_documents"]
    if not documents:
        st.markdown(
            """
            <div class="empty-card">
              <h3>Start with your source documents</h3>
              <p>Upload PDF, DOCX, or TXT files from the sidebar. Then build the index to unlock retrieval and grounded chat.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for document in documents:
        with st.container(border=True):
            meta_left, meta_right = st.columns([1.5, 1])
            meta_left.markdown(f"**{document['filename']}**")
            meta_left.caption(f"ID: `{document['document_id']}`")
            meta_right.markdown(
                f"<div class='doc-badge'>{document['file_type'].upper()} | {document['chunks_extracted']} chunks</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"Status: {document['status']}")


def _render_chat_panel(api_client: DocuMindApiClient) -> None:
    st.markdown("### Chat with your documents")
    st.caption("Ask direct questions. Answers stay grounded in retrieved chunks.")
    top_k = st.slider("Retrieval depth", min_value=1, max_value=8, value=4, key="chat_top_k")

    for turn in st.session_state["chat_history"]:
        with st.chat_message("user"):
            st.markdown(turn["question"])
        with st.chat_message("assistant"):
            _render_answer_block(turn["answer"], turn["confidence_score"])
            _render_citations(turn["citations"])
            _render_retrieved_chunks(turn["retrieved_chunks"], label="Retrieved context")

    prompt = st.chat_input("Ask a question about your uploaded documents")
    if not prompt:
        return

    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Grounding answer in retrieved sources..."):
            response = api_client.query_chat(
                session_id=st.session_state["session_id"],
                user_query=prompt,
                top_k=top_k,
            )
        append_chat_turn(st.session_state, question=prompt, response=response)
        st.session_state["session_id"] = response["session_id"]
        st.rerun()
    except DocuMindApiError as exc:
        with st.chat_message("assistant"):
            st.error(str(exc))


def _render_search_panel(api_client: DocuMindApiClient) -> None:
    st.markdown("### Retrieval preview")
    st.caption("Use this to inspect the raw chunk matches before asking chat questions.")
    with st.form("search-form", clear_on_submit=False):
        query = st.text_input("Search query", placeholder="Find claim deadlines, product dates, policy rules...")
        top_k = st.slider("Top-k matches", min_value=1, max_value=10, value=5, key="search_top_k")
        submitted = st.form_submit_button("Search chunks", use_container_width=True)

    if submitted:
        if not query.strip():
            st.session_state["status_message"] = ("info", "Enter a search query to preview retrieved chunks.")
            st.rerun()
        try:
            with st.spinner("Searching indexed chunks..."):
                response = api_client.search_documents(query=query, top_k=top_k)
            st.session_state["search_results"] = response["matches"]
        except DocuMindApiError as exc:
            st.session_state["search_results"] = []
            st.session_state["status_message"] = ("error", str(exc))
            st.rerun()

    results = st.session_state["search_results"]
    if not results:
        if st.session_state["uploaded_documents"]:
            st.info("Index your documents and run a query to inspect the retrieval layer.")
        else:
            st.info("Upload documents first, then use retrieval preview to inspect matching chunks.")
        return

    for match in results:
        with st.container(border=True):
            header_left, header_right = st.columns([1.5, 1])
            header_left.markdown(f"**{match['filename']}**")
            header_left.caption(f"Chunk {match['chunk_index']} | Document `{match['document_id']}`")
            header_right.markdown(_confidence_chip(match["score"]), unsafe_allow_html=True)
            if match["page_number"] is not None:
                st.caption(f"Page {match['page_number']}")
            st.write(match["text"])


def _render_system_panel(system_status: dict | None) -> None:
    if not system_status:
        st.warning("System status is unavailable.")
        return

    services = system_status.get("services", [])
    for service in services:
        state_label = "Configured" if service["configured"] else "Unavailable"
        st.markdown(
            f"<div class='status-row'><span>{service['name']}</span><span>{state_label}</span></div>",
            unsafe_allow_html=True,
        )
        if service.get("provider"):
            st.caption(f"Provider: {service['provider']}")


def _render_answer_block(answer: str, confidence_score: float) -> None:
    indicator = _grounding_label(answer, confidence_score)
    st.markdown(
        f"""
        <div class="answer-card">
          <div class="answer-meta">
            <span class="grounding-chip">{indicator}</span>
            <span class="confidence-text">Confidence {confidence_score:.2f}</span>
          </div>
          <div class="answer-body">{answer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_citations(citations: list[dict]) -> None:
    if not citations:
        st.caption("No citations were attached because the system did not find sufficient supporting context.")
        return

    with st.expander("Citations", expanded=False):
        for citation in citations:
            page_label = f" | page {citation['page_number']}" if citation["page_number"] is not None else ""
            st.markdown(
                f"**{citation['filename']}**{page_label}  \n"
                f"`{citation['document_id']}` | chunk {citation['chunk_index']} | score {citation['score']:.2f}"
            )
            st.caption(citation["snippet"])


def _render_retrieved_chunks(matches: list[dict], *, label: str) -> None:
    with st.expander(label, expanded=False):
        for match in matches:
            st.markdown(
                f"**{match['filename']}** | chunk {match['chunk_index']} | score {match['score']:.2f}"
            )
            st.caption(match["preview"])


def _render_status_badges(system_status: dict | None) -> None:
    if not system_status:
        st.caption("No backend status available.")
        return
    st.markdown(
        f"<div class='stacked-badge'>Embeddings: {system_status['embedding_provider']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='stacked-badge'>Vector store: {system_status['vector_store_provider']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='stacked-badge'>Answering: {system_status['llm_provider']}</div>",
        unsafe_allow_html=True,
    )


def _render_status_message() -> None:
    status = st.session_state.get("status_message")
    if not status:
        return
    kind, message = status
    if kind == "success":
        st.success(message)
    elif kind == "error":
        st.error(message)
    else:
        st.info(message)
    st.session_state["status_message"] = None


def _grounding_label(answer: str, confidence_score: float) -> str:
    if answer == FALLBACK_ANSWER:
        return "Insufficient context"
    if confidence_score >= 0.65:
        return "Strong grounding"
    if confidence_score >= 0.35:
        return "Moderate grounding"
    return "Low confidence"


def _confidence_chip(score: float) -> str:
    label = "High relevance" if score >= 0.65 else "Relevant" if score >= 0.35 else "Weak match"
    return f"<div class='match-chip'>{label} | {score:.2f}</div>"


def _sync_backend_url() -> str:
    st.session_state["backend_url"] = st.session_state["backend_url_input"].strip() or DEFAULT_BACKEND_URL
    return st.session_state["backend_url"]


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
          .stApp {
            background: #f4f6f8;
            color: #16202a;
          }
          .stApp, .stMarkdown, .stCaption, .stText, label, p, div {
            color: #16202a;
          }
          section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #d7dde5;
          }
          .hero-card, .answer-card, .empty-card {
            background: #ffffff;
            border: 1px solid #d7dde5;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
          }
          .hero-card h1 {
            margin: 0.1rem 0 0.35rem 0;
            font-size: 1.8rem;
            color: #0f1720;
          }
          .hero-card p, .empty-card p, .answer-body {
            color: #324152;
            line-height: 1.5;
            font-size: 0.98rem;
          }
          .eyebrow {
            text-transform: uppercase;
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            color: #385a7a;
            font-weight: 700;
          }
          .doc-badge, .stacked-badge, .match-chip, .grounding-chip {
            display: inline-block;
            border-radius: 999px;
            padding: 0.28rem 0.65rem;
            font-size: 0.76rem;
            font-weight: 600;
          }
          .doc-badge, .stacked-badge {
            color: #264561;
            background: #edf3f8;
          }
          .match-chip {
            color: #0f4b40;
            background: #e8f6f2;
            text-align: right;
          }
          .grounding-chip {
            color: #184d78;
            background: #ebf4fb;
          }
          .answer-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.7rem;
          }
          .confidence-text {
            color: #41566c;
            font-size: 0.82rem;
            font-weight: 600;
          }
          .status-row {
            display: flex;
            justify-content: space-between;
            background: #ffffff;
            border: 1px solid #d7dde5;
            border-radius: 12px;
            padding: 0.65rem 0.8rem;
            margin-bottom: 0.5rem;
            color: #17314d;
            font-size: 0.88rem;
          }
          .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
          }
          .stTabs [data-baseweb="tab"] {
            background: #ffffff;
            border: 1px solid #d7dde5;
            border-radius: 999px;
            padding: 0.35rem 0.9rem;
            color: #21384d;
          }
          .stTabs [aria-selected="true"] {
            background: #eaf1f7 !important;
            border-color: #aac2d6 !important;
          }
          div[data-testid="metric-container"] {
            background: #ffffff;
            border: 1px solid #d7dde5;
            padding: 0.85rem 0.95rem;
            border-radius: 12px;
          }
          div[data-testid="metric-container"] label {
            color: #516578 !important;
          }
          div[data-testid="stChatMessage"] {
            background: transparent;
          }
          @media (max-width: 900px) {
            .hero-card h1 {
              font-size: 1.55rem;
            }
            .answer-meta {
              flex-direction: column;
              align-items: flex-start;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
