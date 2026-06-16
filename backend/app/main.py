import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import (
    catalog,
    estimation,
    generation,
    image,
    project,
    report,
    task,
    variant,
    zone,
)
from app.core.config import BASE_DIR, settings
from app.core.exceptions import AppError
from app.utils.file_handler import ensure_storage_dirs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("house_renovation")

app = FastAPI(title="House Renovation AI", version="1.0.0", debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Expected, client-facing errors (e.g. AI service unavailable -> 503)."""
    logger.warning("AppError on %s %s: %s", request.method, request.url.path, exc.message)
    return JSONResponse(status_code=exc.status_code, content={"success": False, "msg": exc.message, "data": None})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    """Never leak stack traces to clients; log them server-side instead."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "msg": "Something went wrong. Please try again.", "data": None},
    )


ensure_storage_dirs()

storage_root = BASE_DIR / "storage"
app.mount("/storage", StaticFiles(directory=str(storage_root)), name="storage")

api_prefix = "/api/v1"
app.include_router(project.router, prefix=api_prefix)
app.include_router(variant.router, prefix=api_prefix)
app.include_router(image.router, prefix=api_prefix)
app.include_router(zone.router, prefix=api_prefix)
app.include_router(catalog.router, prefix=api_prefix)
app.include_router(generation.router, prefix=api_prefix)
app.include_router(estimation.router, prefix=api_prefix)
app.include_router(task.router, prefix=api_prefix)
app.include_router(report.router, prefix=api_prefix)


@app.get("/")
def root():
    return {"success": True, "msg": "House Renovation AI API", "data": {"docs": "/docs"}}


@app.get("/health")
def health():
    return {"success": True, "msg": "OK", "data": None}
