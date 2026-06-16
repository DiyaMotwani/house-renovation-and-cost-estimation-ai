from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.zone_crud import ZoneCRUD
from app.db.session import get_db
from app.schemas.zone_schema import (
    AssignMaterialSchema,
    BulkAssignMaterialsSchema,
    UpdateZoneSchema,
    ZoneResponseSchema,
)

router = APIRouter(prefix="/projects/{project_id}/zones", tags=["zones"])


@router.get("/")
def list_zones(project_id: UUID, db: Session = Depends(get_db)):
    result = ZoneCRUD(db).list_zones(project_id)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": [ZoneResponseSchema.model_validate(z) for z in result["data"]],
    }


@router.put("/{zone_id}")
def update_zone(project_id: UUID, zone_id: UUID, payload: UpdateZoneSchema, db: Session = Depends(get_db)):
    result = ZoneCRUD(db).update_zone(project_id, zone_id, payload.estimated_sqft)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ZoneResponseSchema.model_validate(result["data"])}


@router.post("/assign")
def bulk_assign_materials(project_id: UUID, payload: BulkAssignMaterialsSchema, db: Session = Depends(get_db)):
    assignments = [{"zone_id": a.zone_id, "material_id": a.material_id} for a in payload.assignments]
    result = ZoneCRUD(db).bulk_assign_materials(project_id, assignments)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": result["data"]}


@router.put("/{zone_id}/assign")
def assign_material(project_id: UUID, zone_id: UUID, payload: AssignMaterialSchema, db: Session = Depends(get_db)):
    result = ZoneCRUD(db).assign_material(project_id, zone_id, payload.material_id)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": result["data"]}


@router.delete("/{zone_id}/assign")
def remove_material(project_id: UUID, zone_id: UUID, db: Session = Depends(get_db)):
    return ZoneCRUD(db).remove_material(project_id, zone_id)
