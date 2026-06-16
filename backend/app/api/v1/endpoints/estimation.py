from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.estimation_crud import EstimationCRUD
from app.db.session import get_db
from app.schemas.estimation_schema import EstimationItemSchema, EstimationSummarySchema, RecalculateEstimationSchema

router = APIRouter(prefix="/projects/{project_id}/estimation", tags=["estimation"])


@router.post("/run")
def run_estimation(project_id: UUID, db: Session = Depends(get_db)):
    result = EstimationCRUD(db).run_estimation(project_id)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": EstimationSummarySchema(
            items=[EstimationItemSchema.model_validate(i) for i in result["data"]["items"]],
            grand_total_inr=result["data"]["grand_total_inr"],
            total_days=result["data"]["total_days"],
        ),
    }


@router.get("/")
def get_estimation(project_id: UUID, db: Session = Depends(get_db)):
    result = EstimationCRUD(db).get_estimation(project_id)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": EstimationSummarySchema(
            items=[EstimationItemSchema.model_validate(i) for i in result["data"]["items"]],
            grand_total_inr=result["data"]["grand_total_inr"],
            total_days=result["data"]["total_days"],
        ),
    }


@router.post("/recalculate")
def recalculate_estimation(project_id: UUID, payload: RecalculateEstimationSchema, db: Session = Depends(get_db)):
    overrides = [o.model_dump() for o in payload.overrides]
    result = EstimationCRUD(db).recalculate(project_id, overrides)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": EstimationSummarySchema(
            items=[EstimationItemSchema.model_validate(i) for i in result["data"]["items"]],
            grand_total_inr=result["data"]["grand_total_inr"],
            total_days=result["data"]["total_days"],
        ),
    }
