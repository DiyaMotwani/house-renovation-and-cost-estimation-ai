from typing import Any


def calculate_zone_cost(
    area_sqft: float,
    material: dict[str, Any],
    custom_unit_price_inr: float | None = None,
    custom_labour_rate_inr: float | None = None,
) -> dict[str, float | str]:
    unit_price = custom_unit_price_inr if custom_unit_price_inr is not None else material["unit_price_inr"]
    labour_rate = custom_labour_rate_inr if custom_labour_rate_inr is not None else material["labour_rate_per_sqft_inr"]

    raw_qty = (area_sqft / material["coverage_sqft_per_unit"]) * material["coats_required"]
    final_qty = raw_qty * (1 + material["wastage_factor"])
    material_cost = final_qty * unit_price
    labour_cost = area_sqft * labour_rate
    total_cost = material_cost + labour_cost
    days = area_sqft * material["days_per_100_sqft"] / 100

    return {
        "area_sqft": round(area_sqft, 2),
        "qty_required": round(final_qty, 2),
        "unit": material["unit"],
        "material_cost_inr": round(material_cost, 2),
        "labour_cost_inr": round(labour_cost, 2),
        "total_cost_inr": round(total_cost, 2),
        "estimated_days": round(days, 2),
    }
