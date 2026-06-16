from fastapi import APIRouter, Query

from app.catalog.loader import get_material_by_id, load_catalog

router = APIRouter(prefix="/catalog/materials", tags=["catalog"])


@router.get("/")
def list_materials(category: str | None = Query(None)):
    try:
        materials = load_catalog()
        if category:
            materials = [m for m in materials if m["category"] == category]
        return {"success": True, "msg": "Catalog fetched", "data": materials}
    except Exception as e:
        return {"success": False, "msg": str(e), "data": None}


@router.get("/{material_id}")
def get_material(material_id: str):
    try:
        material = get_material_by_id(material_id)
        if not material:
            return {"success": False, "msg": "Material not found", "data": None}
        return {"success": True, "msg": "Material fetched", "data": material}
    except Exception as e:
        return {"success": False, "msg": str(e), "data": None}
