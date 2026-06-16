import uuid
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.catalog.loader import get_material_by_id
from app.core.constants import (
    GST_RATE_PCT,
    PROJECT_STATUS_ESTIMATION_COMPLETE,
    PROJECT_STATUS_GENERATION_COMPLETE,
    TASK_STATUS_PENDING,
    TASK_TYPE_GENERATE_RENOVATION,
)
from app.crud.image_crud import ImageCRUD
from app.crud.project_crud import ProjectCRUD
from app.crud.zone_crud import ZoneCRUD
from app.models.renovation_models import ProjectEstimation, ProjectZone, TaskRecord
from app.utils.cost_calculator import calculate_zone_cost


def _empty_costs(est: ProjectEstimation) -> dict:
    """Rate-analysis fallback for a stored item whose material left the catalog."""
    return {
        "wastage_pct": 0.0,
        "base_unit_price_inr": est.custom_unit_price_inr or 0.0,
        "applied_unit_price_inr": est.custom_unit_price_inr or 0.0,
        "unit_price_overridden": est.custom_unit_price_inr is not None,
        "base_labour_rate_inr": est.custom_labour_rate_inr or 0.0,
        "applied_labour_rate_inr": est.custom_labour_rate_inr or 0.0,
        "labour_overridden": est.custom_labour_rate_inr is not None,
    }


def _serialize_item(est: ProjectEstimation, zone: ProjectZone | None, material: dict, costs: dict) -> dict:
    """Flatten a stored estimation + its rate analysis into one BOQ line item."""
    return {
        "id": est.id,
        "project_id": est.project_id,
        "zone_id": est.zone_id,
        "zone_label": zone.label if zone else "",
        "material_id": est.material_id,
        "material_name": material.get("name") if material else est.material_id,
        "category": material.get("category") if material else "",
        "area_sqft": est.area_sqft,
        "qty_required": est.qty_required,
        "unit": est.unit,
        "wastage_pct": costs["wastage_pct"],
        "base_unit_price_inr": costs["base_unit_price_inr"],
        "applied_unit_price_inr": costs["applied_unit_price_inr"],
        "unit_price_overridden": costs["unit_price_overridden"],
        "base_labour_rate_inr": costs["base_labour_rate_inr"],
        "applied_labour_rate_inr": costs["applied_labour_rate_inr"],
        "labour_overridden": costs["labour_overridden"],
        "material_cost_inr": est.material_cost_inr,
        "labour_cost_inr": est.labour_cost_inr,
        "total_cost_inr": est.total_cost_inr,
        "estimated_days": est.estimated_days,
        "custom_unit_price_inr": est.custom_unit_price_inr,
        "custom_labour_rate_inr": est.custom_labour_rate_inr,
        "dimension_anchor_used": est.dimension_anchor_used,
        "dimension_confidence": est.dimension_confidence,
        "dimension_reasoning": est.dimension_reasoning,
        "calculated_at": est.calculated_at,
    }


def _build_summary(items: list[dict]) -> dict:
    """Roll line items up into a contractor-style summary with subtotals + GST."""
    material_subtotal = sum(i["material_cost_inr"] for i in items)
    labour_subtotal = sum(i["labour_cost_inr"] for i in items)
    grand_total = material_subtotal + labour_subtotal
    gst_amount = grand_total * GST_RATE_PCT / 100
    total_payable = grand_total + gst_amount
    total_days = max((i["estimated_days"] for i in items), default=0.0)
    return {
        "items": items,
        "material_subtotal_inr": round(material_subtotal, 2),
        "labour_subtotal_inr": round(labour_subtotal, 2),
        "grand_total_inr": round(grand_total, 2),
        "gst_pct": GST_RATE_PCT,
        "gst_amount_inr": round(gst_amount, 2),
        "total_payable_inr": round(total_payable),
        "total_days": round(total_days, 2),
    }


class EstimationCRUD:
    def __init__(self, db: Session):
        self.db = db

    def run_estimation(self, project_id: uuid.UUID) -> dict:
        try:
            return self._calculate(project_id, overrides=[])
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def recalculate(self, project_id: uuid.UUID, overrides: list[dict]) -> dict:
        try:
            return self._calculate(project_id, overrides=overrides)
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def _calculate(self, project_id: uuid.UUID, overrides: list[dict]) -> dict:
        project_crud = ProjectCRUD(self.db)
        project_result = project_crud.get_project(project_id)
        if not project_result["success"]:
            return project_result
        project = project_result["data"]

        override_map = {o["zone_id"]: o for o in overrides}

        zones = (
            self.db.query(ProjectZone)
            .options(joinedload(ProjectZone.material_assignment))
            .filter(ProjectZone.project_id == project_id)
            .all()
        )

        self.db.query(ProjectEstimation).filter(ProjectEstimation.project_id == project_id).delete()

        # Stamp every line with one consistent timestamp. Serializing from this
        # in-memory value (instead of re-reading the row after commit) keeps the
        # request safe when concurrent recalculations delete each other's rows.
        now = datetime.now()
        items = []

        for zone in zones:
            if not zone.material_assignment:
                return {"success": False, "msg": f"No material for zone: {zone.label}", "data": None}
            material = get_material_by_id(zone.material_assignment.material_id)
            if not material:
                return {"success": False, "msg": f"Material not found", "data": None}

            area = (zone.estimated_sqft or 0) * project.scale_factor
            anchor = "explicit_zone_area"
            confidence = 1.0
            reasoning = "Zone detected area used directly."
            if area <= 0:
                hints = project.dimension_hints or {}
                estimated_width = float(hints.get("estimated_front_width_ft") or 24)
                floor_height = float(hints.get("estimated_floor_height_ft") or 10)
                floors = max(1, int(project.num_floors or 2))
                area = max(120, estimated_width * floor_height * floors * 0.75)
                anchor = hints.get("detected_reference_object") or "geo_average"
                confidence = float(hints.get("confidence") or 0.35)
                reasoning = hints.get("reasoning") or "Estimated via architecture and reference priors."
            override = override_map.get(zone.id, {})
            custom_unit = override.get("custom_unit_price_inr")
            custom_labour = override.get("custom_labour_rate_inr")

            costs = calculate_zone_cost(area, material, custom_unit, custom_labour)

            estimation = ProjectEstimation(
                id=uuid.uuid4(),
                project_id=project_id,
                zone_id=zone.id,
                material_id=material["id"],
                area_sqft=costs["area_sqft"],
                qty_required=costs["qty_required"],
                unit=costs["unit"],
                material_cost_inr=costs["material_cost_inr"],
                labour_cost_inr=costs["labour_cost_inr"],
                total_cost_inr=costs["total_cost_inr"],
                estimated_days=costs["estimated_days"],
                custom_unit_price_inr=custom_unit,
                custom_labour_rate_inr=custom_labour,
                dimension_anchor_used=anchor,
                dimension_confidence=confidence,
                dimension_reasoning=reasoning,
                calculated_at=now,
            )
            self.db.add(estimation)
            items.append(_serialize_item(estimation, zone, material, costs))

        project_crud.update_status(project_id, PROJECT_STATUS_ESTIMATION_COMPLETE)
        self.db.commit()

        return {"success": True, "msg": "Estimation complete", "data": _build_summary(items)}

    def get_estimation(self, project_id: uuid.UUID) -> dict:
        try:
            estimations = (
                self.db.query(ProjectEstimation)
                .filter(ProjectEstimation.project_id == project_id)
                .all()
            )
            if not estimations:
                return {"success": False, "msg": "No estimation found", "data": None}

            zone_map = {
                z.id: z
                for z in self.db.query(ProjectZone).filter(ProjectZone.project_id == project_id).all()
            }

            items = []
            for est in estimations:
                material = get_material_by_id(est.material_id) or {}
                # Re-derive the rate analysis from the stored inputs; the money
                # values come straight off the persisted row so totals match.
                costs = calculate_zone_cost(
                    est.area_sqft, material, est.custom_unit_price_inr, est.custom_labour_rate_inr
                ) if material else {}
                items.append(_serialize_item(est, zone_map.get(est.zone_id), material, costs or _empty_costs(est)))

            return {"success": True, "msg": "Estimation fetched", "data": _build_summary(items)}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}


class GenerationCRUD:
    def __init__(self, db: Session):
        self.db = db

    def trigger_generation(self, project_id: uuid.UUID, options: dict | None = None) -> dict:
        try:
            from app.workers.ai_worker import task_generate_renovation

            image_crud = ImageCRUD(self.db)
            image_result = image_crud.get_image_by_type(project_id, "original")
            if not image_result["success"]:
                return image_result

            zone_crud = ZoneCRUD(self.db)
            assignments_result = zone_crud.get_zone_assignments_for_generation(project_id)
            if not assignments_result["success"]:
                return assignments_result

            project_result = ProjectCRUD(self.db).get_project(project_id)
            project = project_result["data"] if project_result["success"] else None
            options = options or {}
            generation_context = {
                "house_description": getattr(project, "house_description", "") or "",
                "zone_context": options.get("zone_context", ""),
            }

            celery_result = task_generate_renovation.delay(
                str(project_id),
                image_result["data"].file_path,
                assignments_result["data"],
                options.get("mask_image_path"),
                generation_context,
            )

            task = TaskRecord(
                id=uuid.uuid4(),
                project_id=project_id,
                celery_task_id=celery_result.id,
                task_type=TASK_TYPE_GENERATE_RENOVATION,
                status=TASK_STATUS_PENDING,
            )
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            return {
                "success": True,
                "msg": "Generation started",
                "data": {"task_id": str(task.id), "celery_task_id": celery_result.id},
            }
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def get_generation_status(self, project_id: uuid.UUID) -> dict:
        try:
            from app.crud.task_crud import TaskCRUD

            task = (
                self.db.query(TaskRecord)
                .filter(
                    TaskRecord.project_id == project_id,
                    TaskRecord.task_type == TASK_TYPE_GENERATE_RENOVATION,
                )
                .order_by(TaskRecord.created_at.desc())
                .first()
            )
            project_crud = ProjectCRUD(self.db)
            project = project_crud.get_project(project_id)
            status = project["data"].status if project["success"] else "unknown"
            return {
                "success": True,
                "msg": "Generation status fetched",
                "data": {"status": status, "task": task},
            }
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}
