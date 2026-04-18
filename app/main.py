from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request

from app.routes import chat, documents, health, system
from app.utils.config import get_settings
from app.utils.logging import configure_logging, get_logger
from app.utils.state import AppState


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(component="app")
    app.state.container = AppState.initialize(settings)
    logger.info(
        "app_started",
        environment=settings.app_env,
        embedding_provider=settings.embedding_provider,
        vector_store_provider=settings.vector_store_provider,
        llm_provider=settings.llm_provider,
    )
    yield
    logger.info("app_stopped", environment=settings.app_env)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Production-grade RAG platform for document-grounded Q&A.",
        lifespan=lifespan,
    )

    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(system.router, prefix=settings.api_v1_prefix)
    app.include_router(documents.router, prefix=settings.api_v1_prefix)
    app.include_router(chat.router, prefix=settings.api_v1_prefix)

    if settings.request_log_enabled:
        @app.middleware("http")
        async def log_requests(request: Request, call_next):
            logger = get_logger(component="http", method=request.method, path=request.url.path)
            start = perf_counter()
            try:
                response = await call_next(request)
            except Exception:
                duration_ms = round((perf_counter() - start) * 1000, 2)
                logger.exception("request_failed", duration_ms=duration_ms)
                raise
            duration_ms = round((perf_counter() - start) * 1000, 2)
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            return response

    return app


app = create_app()
