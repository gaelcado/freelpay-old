from fastapi import APIRouter
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

router = APIRouter()

@router.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Freelpay API - Swagger UI",
        oauth2_redirect_url="/api/docs/oauth2-redirect"
    )

@router.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title="Freelpay API - ReDoc"
    ) 