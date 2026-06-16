from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import verify_project_owner
from app.crud.zone_crud import ZoneCRUD
from app.db.session import get_db
from app.schemas.zone_schema import (
    AssignMaterialSchema,
    BulkAssignMaterialsSchema,
    CreateZoneSchema,
    UpdateZoneSchema,
    ZoneResponseSchema,
)

router = APIRouter(
    prefix="/projects/{project_id}/zones",
    tags=["zones"],
    dependencies=[Depends(verify_project_owner)],
)


@router.get("/")
def list_zones(project_id: UUID, variant_id: UUID | None = None, db: Session = Depends(get_db)):
    result = ZoneCRUD(db).list_zones(project_id, variant_id)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": [ZoneResponseSchema.model_validate(z) for z in result["data"]],
    }


@router.post("/")
def create_zone(project_id: UUID, payload: CreateZoneSchema, db: Session = Depends(get_db)):
    result = ZoneCRUD(db).create_zone(project_id, payload.model_dump())
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ZoneResponseSchema.model_validate(result["data"])}


@router.put("/{zone_id}")
def update_zone(project_id: UUID, zone_id: UUID, payload: UpdateZoneSchema, db: Session = Depends(get_db)):
    result = ZoneCRUD(db).update_zone(project_id, zone_id, payload.model_dump(exclude_unset=True))
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ZoneResponseSchema.model_validate(result["data"])}


@router.delete("/{zone_id}")
def delete_zone(project_id: UUID, zone_id: UUID, db: Session = Depends(get_db)):
    return ZoneCRUD(db).delete_zone(project_id, zone_id)


@router.post("/assign")
def bulk_assign_materials(
    project_id: UUID, payload: BulkAssignMaterialsSchema, variant_id: UUID | None = None, db: Session = Depends(get_db)
):
    assignments = [{"zone_id": a.zone_id, "material_id": a.material_id} for a in payload.assignments]
    result = ZoneCRUD(db).bulk_assign_materials(project_id, assignments, variant_id)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": result["data"]}


@router.put("/{zone_id}/assign")
def assign_material(
    project_id: UUID, zone_id: UUID, payload: AssignMaterialSchema, variant_id: UUID | None = None, db: Session = Depends(get_db)
):
    result = ZoneCRUD(db).assign_material(project_id, zone_id, payload.material_id, variant_id)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": result["data"]}


@router.delete("/{zone_id}/assign")
def remove_material(project_id: UUID, zone_id: UUID, variant_id: UUID | None = None, db: Session = Depends(get_db)):
    return ZoneCRUD(db).remove_material(project_id, zone_id, variant_id)
