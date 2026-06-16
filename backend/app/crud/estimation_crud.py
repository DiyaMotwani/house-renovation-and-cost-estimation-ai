import uuid

from sqlalchemy.orm import Session, joinedload

from app.catalog.loader import get_material_by_id
from app.core.constants import (
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

        items = []
        grand_total = 0.0
        max_days = 0.0

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
            )
            self.db.add(estimation)
            items.append(estimation)
            grand_total += costs["total_cost_inr"]
            max_days = max(max_days, costs["estimated_days"])

        project_crud.update_status(project_id, PROJECT_STATUS_ESTIMATION_COMPLETE)
        self.db.commit()
        for item in items:
            self.db.refresh(item)

        return {
            "success": True,
            "msg": "Estimation complete",
            "data": {"items": items, "grand_total_inr": round(grand_total, 2), "total_days": round(max_days, 2)},
        }

    def get_estimation(self, project_id: uuid.UUID) -> dict:
        try:
            items = (
                self.db.query(ProjectEstimation)
                .filter(ProjectEstimation.project_id == project_id)
                .all()
            )
            if not items:
                return {"success": False, "msg": "No estimation found", "data": None}

            grand_total = sum(i.total_cost_inr for i in items)
            total_days = max(i.estimated_days for i in items)
            return {
                "success": True,
                "msg": "Estimation fetched",
                "data": {
                    "items": items,
                    "grand_total_inr": round(grand_total, 2),
                    "total_days": round(total_days, 2),
                },
            }
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
