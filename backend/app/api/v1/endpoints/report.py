from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.crud.report_crud import ReportCRUD
from app.db.session import get_db
from app.schemas.report_schema import ReportResponseSchema

router = APIRouter(prefix="/projects/{project_id}/report", tags=["report"])


@router.post("/generate")
def generate_report(project_id: UUID, db: Session = Depends(get_db)):
    result = ReportCRUD(db).generate_report(project_id)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ReportResponseSchema.model_validate(result["data"])}


@router.get("/")
def get_report(project_id: UUID, db: Session = Depends(get_db)):
    result = ReportCRUD(db).get_report(project_id)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ReportResponseSchema.model_validate(result["data"])}


@router.get("/download")
def download_report(project_id: UUID, db: Session = Depends(get_db)):
    result = ReportCRUD(db).get_report_file_path(project_id)
    if not result["success"]:
        return result
    return FileResponse(result["data"], media_type="application/pdf", filename=f"renovation_report_{project_id}.pdf")
