import uuid
from pathlib import Path

from sqlalchemy.orm import Session, joinedload

from app.core.constants import PROJECT_STATUS_REPORT_READY
from app.crud.estimation_crud import EstimationCRUD
from app.crud.image_crud import ImageCRUD
from app.crud.project_crud import ProjectCRUD
from app.models.renovation_models import RenovationReport
from app.reports.pdf_generator import generate_pdf_report
from app.utils.file_handler import get_report_output_path


def _basis_label(anchor: str | None) -> str:
    """Human-friendly description of how a zone's area (dimension) was derived."""
    if not anchor:
        return "-"
    if anchor == "user_measurement":
        return "measured"
    if anchor.startswith("reference:"):
        return f"ref: {anchor.split(':')[1]}"
    if anchor == "vision_estimate":
        return "AI estimate"
    if anchor == "architectural_prior":
        return "typical"
    return anchor


def _coverage_label(item: dict) -> str:
    cov = item.get("coverage_sqft_per_unit")
    unit = (item.get("unit") or "unit").rstrip("s")
    if cov and cov != 1:
        return f"{cov:g} sqft/{unit}"
    return "-"


class ReportCRUD:
    def __init__(self, db: Session):
        self.db = db

    def generate_report(self, project_id: uuid.UUID, variant_id: uuid.UUID | None = None) -> dict:
        try:
            from app.crud.variant_crud import VariantCRUD

            project_crud = ProjectCRUD(self.db)
            project_result = project_crud.get_project(project_id)
            if not project_result["success"]:
                return project_result
            project = project_result["data"]

            variant_id = VariantCRUD(self.db).resolve_variant_id(project_id, variant_id)

            estimation_crud = EstimationCRUD(self.db)
            est_result = estimation_crud.get_estimation(project_id, variant_id)
            if not est_result["success"]:
                est_result = estimation_crud.run_estimation(project_id, variant_id)
                if not est_result["success"]:
                    return est_result

            image_crud = ImageCRUD(self.db)
            original = image_crud.get_image_by_type(project_id, "original")
            if not original["success"]:
                return {"success": False, "msg": "Upload a house photo before generating a report", "data": None}
            # The redesigned image is optional: degrade gracefully to a
            # before-only report if the user has not generated a preview yet.
            generated = image_crud.get_generated_for_variant(project_id, variant_id)
            generated_path = generated["data"].file_path if generated["success"] else None

            summary = est_result["data"]
            zones_summary = []
            cost_breakdown = []

            for item in summary["items"]:
                zones_summary.append(
                    {
                        "zone_label": item.get("zone_label", ""),
                        "material_name": item.get("material_name") or item["material_id"],
                        "area_sqft": item["area_sqft"],
                        "coverage": _coverage_label(item),
                        "basis": _basis_label(item.get("dimension_anchor_used")),
                    }
                )
                cost_breakdown.append(
                    {
                        "zone_label": item.get("zone_label", ""),
                        "material_id": item["material_id"],
                        "qty_required": item["qty_required"],
                        "unit": item["unit"],
                        "applied_unit_price_inr": item.get("applied_unit_price_inr"),
                        "applied_labour_rate_inr": item.get("applied_labour_rate_inr"),
                        "wastage_pct": item.get("wastage_pct"),
                        "material_cost_inr": item["material_cost_inr"],
                        "labour_cost_inr": item["labour_cost_inr"],
                        "total_cost_inr": item["total_cost_inr"],
                    }
                )

            output_path = get_report_output_path(str(project_id))
            generate_pdf_report(
                project_name=project.name,
                original_image_path=original["data"].file_path,
                generated_image_path=generated_path,
                zones_summary=zones_summary,
                cost_breakdown=cost_breakdown,
                grand_total_inr=summary["grand_total_inr"],
                total_days=summary["total_days"],
                material_subtotal_inr=summary.get("material_subtotal_inr", 0.0),
                labour_subtotal_inr=summary.get("labour_subtotal_inr", 0.0),
                gst_pct=summary.get("gst_pct", 0.0),
                gst_amount_inr=summary.get("gst_amount_inr", 0.0),
                total_payable_inr=summary.get("total_payable_inr", summary["grand_total_inr"]),
                house_description=project.house_description or "",
                renovation_needs=project.renovation_needs or [],
                renovation_suggestions=project.renovation_suggestions or [],
                output_path=output_path,
            )

            # Store the GST-inclusive figure as the headline grand total.
            grand_total_with_gst = summary.get("total_payable_inr", summary["grand_total_inr"])
            existing = (
                self.db.query(RenovationReport)
                .filter(RenovationReport.project_id == project_id)
                .first()
            )
            if existing:
                existing.file_path = output_path
                existing.grand_total_inr = grand_total_with_gst
                existing.total_days = est_result["data"]["total_days"]
                report = existing
            else:
                report = RenovationReport(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    file_path=output_path,
                    grand_total_inr=grand_total_with_gst,
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
