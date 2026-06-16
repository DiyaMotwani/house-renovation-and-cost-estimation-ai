import uuid

from sqlalchemy.orm import Session

from app.core.constants import TASK_STATUS_COMPLETED, TASK_STATUS_FAILED, TASK_STATUS_PROCESSING
from app.models.renovation_models import TaskRecord


class TaskCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_task_by_id(self, task_id: uuid.UUID) -> dict:
        try:
            task = self.db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
            if not task:
                return {"success": False, "msg": "Task not found", "data": None}
            return {"success": True, "msg": "Task fetched", "data": task}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def get_task_by_celery_id(self, celery_task_id: str) -> dict:
        try:
            task = self.db.query(TaskRecord).filter(TaskRecord.celery_task_id == celery_task_id).first()
            if not task:
                return {"success": False, "msg": "Task not found", "data": None}
            return {"success": True, "msg": "Task fetched", "data": task}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def get_latest_validation_task(self, project_id: uuid.UUID) -> dict:
        try:
            task = (
                self.db.query(TaskRecord)
                .filter(TaskRecord.project_id == project_id, TaskRecord.task_type == "validate_image")
                .order_by(TaskRecord.created_at.desc())
                .first()
            )
            if not task:
                return {"success": False, "msg": "No validation task found", "data": None}
            return {"success": True, "msg": "Task fetched", "data": task}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def update_task_status(
        self,
        celery_task_id: str,
        status: str,
        result: dict | None = None,
        error_message: str | None = None,
    ) -> dict:
        try:
            task = self.db.query(TaskRecord).filter(TaskRecord.celery_task_id == celery_task_id).first()
            if not task:
                return {"success": False, "msg": "Task not found", "data": None}
            task.status = status
            if result is not None:
                task.result = result
            if error_message is not None:
                task.error_message = error_message
            self.db.commit()
            self.db.refresh(task)
            return {"success": True, "msg": "Task updated", "data": task}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def mark_processing(self, celery_task_id: str) -> dict:
        return self.update_task_status(celery_task_id, TASK_STATUS_PROCESSING)

    def mark_completed(self, celery_task_id: str, result: dict) -> dict:
        return self.update_task_status(celery_task_id, TASK_STATUS_COMPLETED, result=result)

    def mark_failed(self, celery_task_id: str, error_message: str) -> dict:
        return self.update_task_status(celery_task_id, TASK_STATUS_FAILED, error_message=error_message)
