from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import (
    catalog,
    estimation,
    generation,
    image,
    project,
    report,
    task,
    zone,
)
from app.core.config import BASE_DIR, settings
from app.utils.file_handler import ensure_storage_dirs

app = FastAPI(title="House Renovation AI", version="1.0.0", debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_storage_dirs()

storage_root = BASE_DIR / "storage"
app.mount("/storage", StaticFiles(directory=str(storage_root)), name="storage")

api_prefix = "/api/v1"
app.include_router(project.router, prefix=api_prefix)
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
