def house_description_prompt() -> str:
    return """Analyze this exterior house image and return JSON only.

Schema:
{
  "house_description": "2-4 sentence factual summary of current exterior condition",
  "renovation_needs": [
    "short bullet text"
  ],
  "renovation_suggestions": [
    "short actionable suggestion"
  ],
  "style_hint": "modern|traditional|contemporary|mixed",
  "dimension_hints": {
    "detected_reference_object": "car|bike|door|window|none",
    "estimated_front_width_ft": 0,
    "estimated_floor_height_ft": 0,
    "confidence": 0.0,
    "reasoning": "brief explanation"
  }
}

Rules:
- Return valid JSON only.
- Be conservative and factual.
- If uncertain, keep confidence low and explain.
"""


def material_suggestion_prompt(context: str) -> str:
    return f"""Analyze the house exterior and recommend renovation materials by zone.

Context:
{context}

Available material IDs:
- exterior_paint_smooth (paint)
- texture_finish_sand (texture)
- terracotta_brick_cladding (cladding)
- vitrified_tiles_exterior (tile)
- glass_railing (railing)
- metal_railing (railing)
- stone_cladding (cladding)
- aluminium_composite_panel (panel)

Return JSON only:
{{
  "suggestions": [
    {{
      "zone_key": "upper_wall",
      "recommended_material_ids": ["exterior_paint_smooth"],
      "reason": "brief reason",
      "confidence": 0.0
    }}
  ],
  "overall_style": "modern|traditional|contemporary|mixed",
  "global_reasoning": "short summary"
}}
"""


def masked_generation_prompt(base_prompt: str, zone_context: str, house_context: str) -> str:
    return (
        f"{base_prompt}. "
        "Apply changes only inside masked regions. "
        "Preserve unmasked architecture exactly, including geometry, windows, and roofline. "
        "Do not alter perspective or camera framing. "
        f"Zone context: {zone_context}. "
        f"House context: {house_context}. "
        "Photorealistic exterior renovation, realistic materials, natural lighting."
    )


def dimension_estimation_prompt(zone_label: str, house_context: str) -> str:
    return f"""Estimate dimensions for cost planning for zone '{zone_label}'.

Use this anchor priority:
1) visible real-world object references (car, bike, door, window),
2) architectural priors (floor height, bay width),
3) location/style priors as fallback.

Return JSON only:
{{
  "estimated_sqft": 0,
  "anchor_used": "car|bike|door|window|architecture|geo_average",
  "confidence": 0.0,
  "reasoning": "brief explanation"
}}

House context:
{house_context}
"""
