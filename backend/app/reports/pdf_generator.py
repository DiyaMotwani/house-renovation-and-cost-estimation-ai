from pathlib import Path
from typing import Any

from fpdf import FPDF

from app.catalog.loader import get_material_by_id


class RenovationReportPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, "This estimate is advisory only and not legally binding.", align="C")


def generate_pdf_report(
    project_name: str,
    original_image_path: str,
    generated_image_path: str,
    zones_summary: list[dict[str, Any]],
    cost_breakdown: list[dict[str, Any]],
    grand_total_inr: float,
    total_days: float,
    output_path: str,
    house_description: str = "",
    renovation_needs: list[str] | None = None,
    renovation_suggestions: list[str] | None = None,
) -> str:
    pdf = RenovationReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Exterior Renovation Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 10, project_name, ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Before vs After", ln=True)
    pdf.ln(2)

    img_width = 85
    y_start = pdf.get_y()

    if Path(original_image_path).exists():
        pdf.image(original_image_path, x=10, y=y_start, w=img_width)
    if Path(generated_image_path).exists():
        pdf.image(generated_image_path, x=105, y=y_start, w=img_width)

    pdf.set_y(y_start + 65)
    pdf.ln(5)

    if house_description:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "House Analysis", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 6, house_description[:900])
        pdf.ln(2)
    if renovation_needs:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Renovation Needs", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for need in renovation_needs[:6]:
            pdf.cell(0, 6, f"- {str(need)[:120]}", ln=True)
    if renovation_suggestions:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Suggestions", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for suggestion in renovation_suggestions[:6]:
            pdf.cell(0, 6, f"- {str(suggestion)[:120]}", ln=True)
        pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Zone & Material Summary", ln=True)
    pdf.set_font("Helvetica", "B", 9)
    col_w = [60, 70, 60]
    headers = ["Zone", "Material", "Sq Ft"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 8, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for row in zones_summary:
        pdf.cell(col_w[0], 8, str(row.get("zone_label", ""))[:28], border=1)
        pdf.cell(col_w[1], 8, str(row.get("material_name", ""))[:32], border=1)
        pdf.cell(col_w[2], 8, f"{row.get('area_sqft', 0):.1f}", border=1)
        pdf.ln()
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Cost Breakdown", ln=True)
    pdf.set_font("Helvetica", "B", 8)
    col_w2 = [35, 40, 25, 30, 30, 30]
    headers2 = ["Zone", "Material", "Qty", "Mat Cost", "Labour", "Total"]
    for i, h in enumerate(headers2):
        pdf.cell(col_w2[i], 8, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for row in cost_breakdown:
        material = get_material_by_id(row.get("material_id", ""))
        mat_name = material["name"] if material else row.get("material_id", "")
        qty_str = f"{row.get('qty_required', 0):.1f} {row.get('unit', '')}"
        pdf.cell(col_w2[0], 8, str(row.get("zone_label", ""))[:18], border=1)
        pdf.cell(col_w2[1], 8, mat_name[:20], border=1)
        pdf.cell(col_w2[2], 8, qty_str[:12], border=1)
        pdf.cell(col_w2[3], 8, f"{row.get('material_cost_inr', 0):,.0f}", border=1)
        pdf.cell(col_w2[4], 8, f"{row.get('labour_cost_inr', 0):,.0f}", border=1)
        pdf.cell(col_w2[5], 8, f"{row.get('total_cost_inr', 0):,.0f}", border=1)
        pdf.ln()

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(160, 10, "Grand Total", border=1)
    pdf.cell(30, 10, f"INR {grand_total_inr:,.0f}", border=1, ln=True)
    pdf.cell(160, 10, "Estimated Duration", border=1)
    pdf.cell(30, 10, f"{total_days:.1f} days", border=1, ln=True)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    return str(out)
