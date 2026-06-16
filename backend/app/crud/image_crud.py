import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.constants import (
    IMAGE_TYPE_MASK,
    IMAGE_TYPE_ORIGINAL,
    PROJECT_STATUS_IMAGE_UPLOADED,
    TASK_STATUS_PENDING,
    TASK_TYPE_VALIDATE_IMAGE,
)
from app.models.renovation_models import ProjectImage, TaskRecord
from app.crud.project_crud import ProjectCRUD
from app.utils.file_handler import delete_file, save_upload_file


class ImageCRUD:
    def __init__(self, db: Session):
        self.db = db

    async def upload_image(self, project_id: uuid.UUID, file: UploadFile) -> dict:
        try:
            from app.workers.ai_worker import task_validate_and_process_image

            project_crud = ProjectCRUD(self.db)
            project_result = project_crud.get_project(project_id)
            if not project_result["success"]:
                return project_result

            file_path, size_kb, mime_type = await save_upload_file(file, str(project_id))

            image = ProjectImage(
                id=uuid.uuid4(),
                project_id=project_id,
                image_type=IMAGE_TYPE_ORIGINAL,
                file_path=file_path,
                mime_type=mime_type,
                file_size_kb=size_kb,
            )
            self.db.add(image)
            project_crud.update_status(project_id, PROJECT_STATUS_IMAGE_UPLOADED)

            celery_result = task_validate_and_process_image.delay(str(project_id), file_path)

            task = TaskRecord(
                id=uuid.uuid4(),
                project_id=project_id,
                celery_task_id=celery_result.id,
                task_type=TASK_TYPE_VALIDATE_IMAGE,
                status=TASK_STATUS_PENDING,
            )
            self.db.add(task)
            self.db.commit()
            self.db.refresh(image)
            self.db.refresh(task)

            return {
                "success": True,
                "msg": "Image uploaded, validation started",
                "data": {"image": image, "task_id": str(task.id), "celery_task_id": celery_result.id},
            }
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    async def upload_mask(self, project_id: uuid.UUID, file: UploadFile) -> dict:
        try:
            project_result = ProjectCRUD(self.db).get_project(project_id)
            if not project_result["success"]:
                return project_result
            file_path, size_kb, mime_type = await save_upload_file(file, f"{project_id}_mask")
            image = ProjectImage(
                id=uuid.uuid4(),
                project_id=project_id,
                image_type=IMAGE_TYPE_MASK,
                file_path=file_path,
                mime_type=mime_type,
                file_size_kb=size_kb,
            )
            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)
            return {"success": True, "msg": "Mask uploaded", "data": image}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def list_images(self, project_id: uuid.UUID) -> dict:
        try:
            images = (
                self.db.query(ProjectImage)
                .filter(ProjectImage.project_id == project_id)
                .order_by(ProjectImage.uploaded_at)
                .all()
            )
            return {"success": True, "msg": "Images fetched", "data": images}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def get_image_by_type(self, project_id: uuid.UUID, image_type: str) -> dict:
        try:
            image = (
                self.db.query(ProjectImage)
                .filter(
                    ProjectImage.project_id == project_id,
                    ProjectImage.image_type == image_type,
                )
                .order_by(ProjectImage.uploaded_at.desc())
                .first()
            )
            if not image:
                return {"success": False, "msg": f"No {image_type} image found", "data": None}
            return {"success": True, "msg": "Image fetched", "data": image}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def create_image_record(
        self,
        project_id: uuid.UUID,
        image_type: str,
        file_path: str,
        mime_type: str = "image/png",
        file_size_kb: int | None = None,
    ) -> dict:
        try:
            image = ProjectImage(
                id=uuid.uuid4(),
                project_id=project_id,
                image_type=image_type,
                file_path=file_path,
                mime_type=mime_type,
                file_size_kb=file_size_kb,
            )
            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)
            return {"success": True, "msg": "Image record created", "data": image}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def delete_image(self, project_id: uuid.UUID, image_id: uuid.UUID) -> dict:
        try:
            image = (
                self.db.query(ProjectImage)
                .filter(ProjectImage.id == image_id, ProjectImage.project_id == project_id)
                .first()
            )
            if not image:
                return {"success": False, "msg": "Image not found", "data": None}
            delete_file(image.file_path)
            self.db.delete(image)
            self.db.commit()
            return {"success": True, "msg": "Image deleted", "data": {"id": str(image_id)}}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}
