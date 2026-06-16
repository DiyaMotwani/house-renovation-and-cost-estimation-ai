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
    material_subtotal_inr: float = 0.0,
    labour_subtotal_inr: float = 0.0,
    gst_pct: float = 0.0,
    gst_amount_inr: float = 0.0,
    total_payable_inr: float = 0.0,
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

    has_after = bool(generated_image_path) and Path(generated_image_path).exists()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Before vs After" if has_after else "Current House", ln=True)
    pdf.ln(2)

    img_width = 85
    y_start = pdf.get_y()

    if Path(original_image_path).exists():
        pdf.image(original_image_path, x=10, y=y_start, w=img_width)
    if has_after:
        pdf.image(generated_image_path, x=105, y=y_start, w=img_width)
    else:
        pdf.set_xy(105, y_start + 28)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(150, 150, 150)
        pdf.multi_cell(img_width, 5, "Redesigned preview not generated yet.", align="C")
        pdf.set_text_color(0, 0, 0)

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
    pdf.cell(0, 10, "Cost Breakdown (Bill of Quantities)", ln=True)
    pdf.set_font("Helvetica", "B", 7)
    # Zone | Material | Qty | Rate | Material | Labour rate | Labour | Total
    col_w2 = [28, 33, 22, 20, 26, 18, 23, 20]
    headers2 = ["Zone", "Material", "Qty", "Rate", "Material", "Lab/sqft", "Labour", "Total"]
    for i, h in enumerate(headers2):
        pdf.cell(col_w2[i], 8, h, border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 7)
    for row in cost_breakdown:
        material = get_material_by_id(row.get("material_id", ""))
        mat_name = material["name"] if material else row.get("material_id", "")
        qty_str = f"{row.get('qty_required', 0):.1f} {row.get('unit', '')}"
        unit_rate = row.get("applied_unit_price_inr") or 0
        labour_rate = row.get("applied_labour_rate_inr") or 0
        pdf.cell(col_w2[0], 7, str(row.get("zone_label", ""))[:16], border=1)
        pdf.cell(col_w2[1], 7, mat_name[:19], border=1)
        pdf.cell(col_w2[2], 7, qty_str[:11], border=1)
        pdf.cell(col_w2[3], 7, f"{unit_rate:,.0f}", border=1, align="R")
        pdf.cell(col_w2[4], 7, f"{row.get('material_cost_inr', 0):,.0f}", border=1, align="R")
        pdf.cell(col_w2[5], 7, f"{labour_rate:,.0f}", border=1, align="R")
        pdf.cell(col_w2[6], 7, f"{row.get('labour_cost_inr', 0):,.0f}", border=1, align="R")
        pdf.cell(col_w2[7], 7, f"{row.get('total_cost_inr', 0):,.0f}", border=1, align="R")
        pdf.ln()

    pdf.ln(3)
    label_w, val_w = 150, 40

    def total_row(label: str, value: str, bold: bool = False):
        pdf.set_font("Helvetica", "B" if bold else "", 9)
        pdf.cell(label_w, 8, label, border=1)
        pdf.cell(val_w, 8, value, border=1, align="R", ln=True)

    total_row("Material subtotal", f"INR {material_subtotal_inr:,.0f}")
    total_row("Labour subtotal", f"INR {labour_subtotal_inr:,.0f}")
    total_row("Subtotal (Material + Labour)", f"INR {grand_total_inr:,.0f}", bold=True)
    if gst_pct:
        total_row(f"GST @ {gst_pct:.0f}%", f"INR {gst_amount_inr:,.0f}")
        total_row("Total Payable (incl. GST)", f"INR {total_payable_inr:,.0f}", bold=True)
    total_row("Estimated Duration", f"{total_days:.1f} working days", bold=True)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    return str(out)
