from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import verify_project_owner
from app.crud.image_crud import ImageCRUD
from app.db.session import get_db
from app.schemas.image_schema import ImageResponseSchema

router = APIRouter(
    prefix="/projects/{project_id}/images",
    tags=["images"],
    dependencies=[Depends(verify_project_owner)],
)


@router.post("/upload")
async def upload_image(project_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    result = await ImageCRUD(db).upload_image(project_id, file)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": {
            "image": ImageResponseSchema.model_validate(result["data"]["image"]),
            "task_id": result["data"]["task_id"],
            "celery_task_id": result["data"]["celery_task_id"],
        },
    }


@router.get("/")
def list_images(project_id: UUID, db: Session = Depends(get_db)):
    result = ImageCRUD(db).list_images(project_id)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": [ImageResponseSchema.model_validate(i) for i in result["data"]],
    }


@router.post("/mask")
async def upload_mask(project_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    result = await ImageCRUD(db).upload_mask(project_id, file)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ImageResponseSchema.model_validate(result["data"])}


@router.delete("/{image_id}")
def delete_image(project_id: UUID, image_id: UUID, db: Session = Depends(get_db)):
    return ImageCRUD(db).delete_image(project_id, image_id)
