import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.constants import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_IMAGE_MIME_TYPES


def ensure_storage_dirs() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.generated_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)


def validate_image_file(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValueError("Only JPG and PNG images are allowed")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Invalid file extension. Use .jpg, .jpeg, or .png")


async def save_upload_file(file: UploadFile, project_id: str) -> tuple[str, int, str]:
    ensure_storage_dirs()
    validate_image_file(file)

    ext = Path(file.filename or "upload.jpg").suffix.lower()
    filename = f"{project_id}_{uuid.uuid4().hex}{ext}"
    dest = settings.upload_dir / filename

    content = await file.read()
    dest.write_bytes(content)
    size_kb = max(1, len(content) // 1024)
    return str(dest), size_kb, file.content_type or "image/jpeg"


def get_sketch_output_path(project_id: str) -> str:
    ensure_storage_dirs()
    return str(settings.generated_dir / f"{project_id}_sketch.png")


def get_generated_output_path(project_id: str) -> str:
    ensure_storage_dirs()
    return str(settings.generated_dir / f"{project_id}_generated.png")


def get_report_output_path(project_id: str) -> str:
    ensure_storage_dirs()
    return str(settings.reports_dir / f"{project_id}_report.pdf")


def delete_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()


def to_serve_path(file_path: str) -> str:
    return file_path.replace("\\", "/")


def copy_file_for_report(src: str, dest: str) -> str:
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_path)
    return str(dest_path)
