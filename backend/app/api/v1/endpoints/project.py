from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_owner_token, verify_project_owner
from app.crud.project_crud import ProjectCRUD
from app.db.session import get_db
from app.schemas.project_schema import (
    CreateProjectSchema,
    ProjectResponseSchema,
    ScaleAnchorSchema,
    UpdateProjectSchema,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/")
def create_project(
    payload: CreateProjectSchema,
    owner_token: str | None = Depends(get_owner_token),
    db: Session = Depends(get_db),
):
    result = ProjectCRUD(db).create_project(payload.name, owner_token)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ProjectResponseSchema.model_validate(result["data"])}


@router.get("/")
def list_projects(owner_token: str | None = Depends(get_owner_token), db: Session = Depends(get_db)):
    result = ProjectCRUD(db).list_projects(owner_token)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": [ProjectResponseSchema.model_validate(p) for p in result["data"]],
    }


@router.get("/{project_id}", dependencies=[Depends(verify_project_owner)])
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    result = ProjectCRUD(db).get_project(project_id)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ProjectResponseSchema.model_validate(result["data"])}


@router.get("/{project_id}/analysis", dependencies=[Depends(verify_project_owner)])
def get_project_analysis(project_id: UUID, db: Session = Depends(get_db)):
    result = ProjectCRUD(db).get_project(project_id)
    if not result["success"]:
        return result
    p = result["data"]
    return {
        "success": True,
        "msg": "Analysis fetched",
        "data": {
            "house_description": p.house_description,
            "renovation_needs": p.renovation_needs or [],
            "renovation_suggestions": p.renovation_suggestions or [],
            "style_hint": p.style_hint,
            "dimension_hints": p.dimension_hints or {},
        },
    }


@router.put("/{project_id}", dependencies=[Depends(verify_project_owner)])
def update_project(project_id: UUID, payload: UpdateProjectSchema, db: Session = Depends(get_db)):
    result = ProjectCRUD(db).update_project(project_id, payload.name)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ProjectResponseSchema.model_validate(result["data"])}


@router.delete("/{project_id}", dependencies=[Depends(verify_project_owner)])
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    return ProjectCRUD(db).delete_project(project_id)


@router.put("/{project_id}/scale-anchor", dependencies=[Depends(verify_project_owner)])
def set_scale_anchor(project_id: UUID, payload: ScaleAnchorSchema, db: Session = Depends(get_db)):
    result = ProjectCRUD(db).set_scale_anchor(project_id, payload.user_front_width_ft)
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": ProjectResponseSchema.model_validate(result["data"])}
