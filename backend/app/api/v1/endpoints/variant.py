from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import verify_project_owner
from app.crud.estimation_crud import EstimationCRUD
from app.crud.image_crud import ImageCRUD
from app.crud.variant_crud import VariantCRUD
from app.db.session import get_db
from app.schemas.variant_schema import (
    CreateVariantSchema,
    RenameVariantSchema,
    VariantResponseSchema,
)

router = APIRouter(
    prefix="/projects/{project_id}/variants",
    tags=["variants"],
    dependencies=[Depends(verify_project_owner)],
)


def _variant(result: dict) -> dict:
    if not result["success"]:
        return result
    return {"success": True, "msg": result["msg"], "data": VariantResponseSchema.model_validate(result["data"])}


@router.get("/")
def list_variants(project_id: UUID, db: Session = Depends(get_db)):
    result = VariantCRUD(db).list_variants(project_id)
    if not result["success"]:
        return result
    return {
        "success": True,
        "msg": result["msg"],
        "data": [VariantResponseSchema.model_validate(v) for v in result["data"]],
    }


@router.post("/")
def create_variant(project_id: UUID, payload: CreateVariantSchema, db: Session = Depends(get_db)):
    return _variant(VariantCRUD(db).create_variant(project_id, payload.name, payload.copy_from_active))


@router.put("/{variant_id}/activate")
def activate_variant(project_id: UUID, variant_id: UUID, db: Session = Depends(get_db)):
    return _variant(VariantCRUD(db).activate_variant(project_id, variant_id))


@router.put("/{variant_id}")
def rename_variant(project_id: UUID, variant_id: UUID, payload: RenameVariantSchema, db: Session = Depends(get_db)):
    return _variant(VariantCRUD(db).rename_variant(project_id, variant_id, payload.name))


@router.delete("/{variant_id}")
def delete_variant(project_id: UUID, variant_id: UUID, db: Session = Depends(get_db)):
    return VariantCRUD(db).delete_variant(project_id, variant_id)


@router.get("/compare")
def compare_variants(project_id: UUID, db: Session = Depends(get_db)):
    """Side-by-side: each variant with its preview image and headline costs."""
    variants_result = VariantCRUD(db).list_variants(project_id)
    if not variants_result["success"]:
        return variants_result

    image_crud = ImageCRUD(db)
    estimation_crud = EstimationCRUD(db)
    items = []
    for variant in variants_result["data"]:
        img = image_crud.get_generated_for_variant(project_id, variant.id)
        est = estimation_crud.get_estimation(project_id, variant.id)
        # Populate a missing estimate from this variant's own materials so the
        # comparison is accurate; never overwrite one that already exists
        # (keeps any rate overrides the user set for that design).
        if not est["success"]:
            est = estimation_crud.run_estimation(project_id, variant.id)
        est_data = est["data"] if est["success"] else None
        items.append(
            {
                "variant": VariantResponseSchema.model_validate(variant),
                "generated_image_path": img["data"].file_path if img["success"] else None,
                "grand_total_inr": est_data["grand_total_inr"] if est_data else None,
                "total_payable_inr": est_data["total_payable_inr"] if est_data else None,
                "total_days": est_data["total_days"] if est_data else None,
            }
        )
    return {"success": True, "msg": "Comparison built", "data": items}
