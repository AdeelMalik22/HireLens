from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.router import api_router
from app.api.dashboard import router as dashboard_router
from app.api.auth import router as auth_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.auth import require_dashboard_auth


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-assisted resume screening API.",
    lifespan=lifespan,
)
app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key, max_age=settings.session_max_age_seconds, https_only=False, same_site="lax")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(auth_router)
app.include_router(dashboard_router, dependencies=[Depends(require_dashboard_auth)])


@app.get("/", tags=["system"])
async def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=307)
