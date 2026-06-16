from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import verify_project_owner
from app.crud.estimation_crud import EstimationCRUD
from app.db.session import get_db
from app.schemas.estimation_schema import EstimationSummarySchema, RecalculateEstimationSchema

router = APIRouter(
    prefix="/projects/{project_id}/estimation",
    tags=["estimation"],
    dependencies=[Depends(verify_project_owner)],
)


def _summary_response(result: dict) -> dict:
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": EstimationSummarySchema.model_validate(result["data"]),
    }


@router.post("/run")
def run_estimation(project_id: UUID, variant_id: UUID | None = None, db: Session = Depends(get_db)):
    return _summary_response(EstimationCRUD(db).run_estimation(project_id, variant_id))


@router.get("/")
def get_estimation(project_id: UUID, variant_id: UUID | None = None, db: Session = Depends(get_db)):
    return _summary_response(EstimationCRUD(db).get_estimation(project_id, variant_id))


@router.post("/recalculate")
def recalculate_estimation(
    project_id: UUID, payload: RecalculateEstimationSchema, variant_id: UUID | None = None, db: Session = Depends(get_db)
):
    overrides = [o.model_dump() for o in payload.overrides]
    return _summary_response(EstimationCRUD(db).recalculate(project_id, overrides, variant_id))
