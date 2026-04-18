from fastapi import APIRouter, Request

from app.models.schemas import SystemStatusResponse
from app.utils.config import Settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=SystemStatusResponse)
async def system_status(request: Request) -> SystemStatusResponse:
    container = request.app.state.container
    settings: Settings = container.settings

    return SystemStatusResponse(
        app_name=settings.app_name,
        environment=settings.app_env,
        llm_provider=settings.llm_provider,
        embedding_provider=settings.embedding_provider,
        vector_store_provider=settings.vector_store_provider,
        services=container.describe_services(),
    )
