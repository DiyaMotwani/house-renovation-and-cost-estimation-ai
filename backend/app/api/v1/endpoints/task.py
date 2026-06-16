from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.task_crud import TaskCRUD
from app.db.session import get_db
from app.schemas.task_schema import TaskStatusResponseSchema

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}/status")
def get_task_status(task_id: UUID, db: Session = Depends(get_db)):
    result = TaskCRUD(db).get_task_by_id(task_id)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": TaskStatusResponseSchema.model_validate(result["data"]),
    }
