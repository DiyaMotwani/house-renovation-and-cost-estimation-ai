import uuid
from pathlib import Path

from app.ai.analysis.house_analyzer import analyze_house
from app.ai.generation.image_generator import generate_image
from app.ai.prompts import masked_generation_prompt
from app.ai.sketch.sketch_generator import generate_sketch
from app.ai.suggestion.material_suggester import suggest_materials
from app.ai.validation.image_validator import validate_image
from app.ai.zone_detection.zone_detector import detect_zones
from app.core.constants import (
    IMAGE_TYPE_GENERATED,
    IMAGE_TYPE_SKETCH,
    PROJECT_STATUS_FAILED,
    PROJECT_STATUS_GENERATION_COMPLETE,
    PROJECT_STATUS_IMAGE_REJECTED,
    PROJECT_STATUS_ZONES_DETECTED,
    TASK_STATUS_PROCESSING,
)
from app.crud.image_crud import ImageCRUD
from app.crud.project_crud import ProjectCRUD
from app.crud.task_crud import TaskCRUD
from app.crud.zone_crud import ZoneCRUD
from app.db.database import SessionLocal
from app.utils.file_handler import get_generated_output_path, get_sketch_output_path
from app.utils.prompt_builder import build_prompt
from app.workers.celery_app import celery_app

DEFAULT_ZONES = [
    {
        "zone_key": "upper_wall",
        "label": "Upper wall",
        "description": "Upper floor exterior wall",
        "estimated_sqft": 280.0,
    },
    {
        "zone_key": "lower_wall",
        "label": "Lower wall",
        "description": "Ground floor exterior wall",
        "estimated_sqft": 320.0,
    },
    {
        "zone_key": "balcony",
        "label": "Balcony",
        "description": "Balcony slab and front face",
        "estimated_sqft": 80.0,
    },
]


def _normalize_mask_path(mask_path: str | None) -> str | None:
    if not mask_path:
        return None
    p = Path(mask_path)
    if not p.exists():
        raise ValueError("Mask image not found")
    return str(p)


@celery_app.task(bind=True, name="task_validate_and_process_image")
def task_validate_and_process_image(self, project_id: str, image_path: str):
    db = SessionLocal()
    try:
        pid = uuid.UUID(project_id)
        task_crud = TaskCRUD(db)
        project_crud = ProjectCRUD(db)
        image_crud = ImageCRUD(db)
        zone_crud = ZoneCRUD(db)

        task_crud.mark_processing(self.request.id)

        validation = validate_image(image_path)
        if validation.get("quality") != "pass":
            project_crud.update_status(pid, PROJECT_STATUS_IMAGE_REJECTED)
            result = {"validation": validation}
            task_crud.mark_completed(self.request.id, result)
            return result

        sketch_path = get_sketch_output_path(project_id)
        generate_sketch(image_path, sketch_path)
        sketch_size = Path(sketch_path).stat().st_size // 1024
        image_crud.create_image_record(pid, IMAGE_TYPE_SKETCH, sketch_path, "image/png", sketch_size)

        zones_data = detect_zones(image_path)
        zones_list = zones_data.get("zones") or []
        if not zones_list:
            zones_list = DEFAULT_ZONES
        zone_crud.save_zones_from_detection(pid, zones_list)
        project_crud.update_zone_metadata(
            pid,
            zones_data.get("approx_front_width_ft"),
            zones_data.get("num_floors"),
        )

        house_analysis = analyze_house(image_path)
        project_crud.update_house_analysis(pid, house_analysis)
        suggestions = suggest_materials(image_path, house_analysis)

        project_crud.update_status(pid, PROJECT_STATUS_ZONES_DETECTED)

        result = {
            "validation": validation,
            "zones": {**zones_data, "zones": zones_list},
            "suggestions": suggestions,
            "analysis": house_analysis,
            "sketch_path": sketch_path,
        }
        task_crud.mark_completed(self.request.id, result)
        return result
    except Exception as e:
        task_crud = TaskCRUD(db)
        task_crud.mark_failed(self.request.id, str(e))
        ProjectCRUD(db).update_status(uuid.UUID(project_id), PROJECT_STATUS_FAILED)
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="task_generate_renovation")
def task_generate_renovation(
    self,
    project_id: str,
    image_path: str,
    zone_assignments: list,
    mask_path: str | None = None,
    generation_context: dict | None = None,
    variant_id: str | None = None,
):
    db = SessionLocal()
    try:
        pid = uuid.UUID(project_id)
        vid = uuid.UUID(variant_id) if variant_id else None
        task_crud = TaskCRUD(db)
        project_crud = ProjectCRUD(db)
        image_crud = ImageCRUD(db)

        task_crud.mark_processing(self.request.id)

        prompt = build_prompt(zone_assignments)
        generation_context = generation_context or {}
        house_context = generation_context.get("house_description", "")
        zone_context = generation_context.get("zone_context", "")
        prompt = masked_generation_prompt(prompt, zone_context, house_context)
        output_path = get_generated_output_path(project_id, variant_id)
        generation_meta = generate_image(
            image_path=image_path,
            prompt=prompt,
            output_path=output_path,
            mask_path=_normalize_mask_path(mask_path),
            preserve_unmasked=True,
        )

        gen_size = Path(generation_meta["output_path"]).stat().st_size // 1024
        if vid:
            image_crud.clear_generated_for_variant(pid, vid)
        image_crud.create_image_record(pid, IMAGE_TYPE_GENERATED, output_path, "image/png", gen_size, variant_id=vid)

        project_crud.update_status(pid, PROJECT_STATUS_GENERATION_COMPLETE)

        result = {
            "generated_path": output_path,
            "prompt": prompt,
            "mask_path": mask_path,
            "generation_meta": generation_meta,
        }
        task_crud.mark_completed(self.request.id, result)
        return result
    except Exception as e:
        task_crud = TaskCRUD(db)
        task_crud.mark_failed(self.request.id, str(e))
        ProjectCRUD(db).update_status(uuid.UUID(project_id), PROJECT_STATUS_FAILED)
        raise
    finally:
        db.close()
