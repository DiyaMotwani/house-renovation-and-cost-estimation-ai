from typing import Any


def _resolve_rate(custom: float | None, default: float) -> tuple[float, bool]:
    """Pick the rate to bill at.

    An override only takes effect when it is a real, positive number. A value of
    None, 0 or a negative number is treated as "no override" and falls back to
    the catalog rate -- this lets a user clear an edited field to restore the
    standard rate instead of accidentally pricing the line at zero.
    """
    if custom is not None and custom > 0:
        return float(custom), True
    return float(default), False


def calculate_zone_cost(
    area_sqft: float,
    material: dict[str, Any],
    custom_unit_price_inr: float | None = None,
    custom_labour_rate_inr: float | None = None,
) -> dict[str, Any]:
    base_unit_price = float(material["unit_price_inr"])
    base_labour_rate = float(material["labour_rate_per_sqft_inr"])
    unit_price, unit_overridden = _resolve_rate(custom_unit_price_inr, base_unit_price)
    labour_rate, labour_overridden = _resolve_rate(custom_labour_rate_inr, base_labour_rate)

    area_sqft = max(0.0, float(area_sqft))
    coverage = float(material["coverage_sqft_per_unit"])
    coats = float(material["coats_required"])
    wastage_factor = float(material["wastage_factor"])

    # Quantity before wastage, then the wastage allowance a contractor would add.
    base_qty = (area_sqft / coverage) * coats
    wastage_qty = base_qty * wastage_factor
    final_qty = base_qty + wastage_qty

    material_cost = final_qty * unit_price
    labour_cost = area_sqft * labour_rate
    total_cost = material_cost + labour_cost
    days = area_sqft * float(material["days_per_100_sqft"]) / 100

    return {
        "area_sqft": round(area_sqft, 2),
        "qty_required": round(final_qty, 2),
        "base_qty": round(base_qty, 2),
        "wastage_qty": round(wastage_qty, 2),
        "wastage_pct": round(wastage_factor * 100, 1),
        "coverage_sqft_per_unit": coverage,
        "coats_required": coats,
        "unit": material["unit"],
        "base_unit_price_inr": round(base_unit_price, 2),
        "applied_unit_price_inr": round(unit_price, 2),
        "unit_price_overridden": unit_overridden,
        "base_labour_rate_inr": round(base_labour_rate, 2),
        "applied_labour_rate_inr": round(labour_rate, 2),
        "labour_overridden": labour_overridden,
        "material_cost_inr": round(material_cost, 2),
        "labour_cost_inr": round(labour_cost, 2),
        "total_cost_inr": round(total_cost, 2),
        "estimated_days": round(days, 2),
    }
