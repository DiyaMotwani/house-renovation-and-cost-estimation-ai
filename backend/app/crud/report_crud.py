import uuid
from pathlib import Path

from sqlalchemy.orm import Session, joinedload

from app.catalog.loader import get_material_by_id
from app.core.constants import PROJECT_STATUS_REPORT_READY
from app.crud.estimation_crud import EstimationCRUD
from app.crud.image_crud import ImageCRUD
from app.crud.project_crud import ProjectCRUD
from app.crud.zone_crud import ZoneCRUD
from app.models.renovation_models import RenovationReport
from app.reports.pdf_generator import generate_pdf_report
from app.utils.file_handler import get_report_output_path


class ReportCRUD:
    def __init__(self, db: Session):
        self.db = db

    def generate_report(self, project_id: uuid.UUID) -> dict:
        try:
            project_crud = ProjectCRUD(self.db)
            project_result = project_crud.get_project(project_id)
            if not project_result["success"]:
                return project_result
            project = project_result["data"]

            estimation_crud = EstimationCRUD(self.db)
            est_result = estimation_crud.get_estimation(project_id)
            if not est_result["success"]:
                est_result = estimation_crud.run_estimation(project_id)
                if not est_result["success"]:
                    return est_result

            image_crud = ImageCRUD(self.db)
            original = image_crud.get_image_by_type(project_id, "original")
            generated = image_crud.get_image_by_type(project_id, "generated")
            if not original["success"] or not generated["success"]:
                return {"success": False, "msg": "Before/after images required", "data": None}

            zone_crud = ZoneCRUD(self.db)
            zones_result = zone_crud.list_zones(project_id)
            zones = zones_result["data"] if zones_result["success"] else []

            zone_map = {z.id: z for z in zones}
            zones_summary = []
            cost_breakdown = []

            for item in est_result["data"]["items"]:
                zone = zone_map.get(item.zone_id)
                material = get_material_by_id(item.material_id)
                zones_summary.append(
                    {
                        "zone_label": zone.label if zone else "",
                        "material_name": material["name"] if material else item.material_id,
                        "area_sqft": item.area_sqft,
                    }
                )
                cost_breakdown.append(
                    {
                        "zone_label": zone.label if zone else "",
                        "material_id": item.material_id,
                        "qty_required": item.qty_required,
                        "unit": item.unit,
                        "material_cost_inr": item.material_cost_inr,
                        "labour_cost_inr": item.labour_cost_inr,
                        "total_cost_inr": item.total_cost_inr,
                    }
                )

            output_path = get_report_output_path(str(project_id))
            generate_pdf_report(
                project_name=project.name,
                original_image_path=original["data"].file_path,
                generated_image_path=generated["data"].file_path,
                zones_summary=zones_summary,
                cost_breakdown=cost_breakdown,
                grand_total_inr=est_result["data"]["grand_total_inr"],
                total_days=est_result["data"]["total_days"],
                house_description=project.house_description or "",
                renovation_needs=project.renovation_needs or [],
                renovation_suggestions=project.renovation_suggestions or [],
                output_path=output_path,
            )

            existing = (
                self.db.query(RenovationReport)
                .filter(RenovationReport.project_id == project_id)
                .first()
            )
            if existing:
                existing.file_path = output_path
                existing.grand_total_inr = est_result["data"]["grand_total_inr"]
                existing.total_days = est_result["data"]["total_days"]
                report = existing
            else:
                report = RenovationReport(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    file_path=output_path,
                    grand_total_inr=est_result["data"]["grand_total_inr"],
                    total_days=est_result["data"]["total_days"],
                )
                self.db.add(report)

            project_crud.update_status(project_id, PROJECT_STATUS_REPORT_READY)
            self.db.commit()
            self.db.refresh(report)

            return {"success": True, "msg": "Report generated", "data": report}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def get_report(self, project_id: uuid.UUID) -> dict:
        try:
            report = (
                self.db.query(RenovationReport)
                .filter(RenovationReport.project_id == project_id)
                .first()
            )
            if not report:
                return {"success": False, "msg": "Report not found", "data": None}
            return {"success": True, "msg": "Report fetched", "data": report}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def get_report_file_path(self, project_id: uuid.UUID) -> dict:
        try:
            result = self.get_report(project_id)
            if not result["success"]:
                return result
            path = Path(result["data"].file_path)
            if not path.exists():
                return {"success": False, "msg": "Report file missing", "data": None}
            return {"success": True, "msg": "Report path fetched", "data": str(path)}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}
