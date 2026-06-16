from typing import Any

from app.ai.groq_client import call_groq_with_image


def detect_zones(image_path: str) -> dict[str, Any]:
    prompt = """Analyze this house exterior photo and identify structural renovation zones.

Identify zones such as: upper_wall, lower_wall, balcony, railing, parapet, entrance, columns, roof_edge, etc.

For each zone estimate the visible surface area in square feet based on typical Indian residential proportions.

Return JSON only with this exact structure:
{
  "zones": [
    {
      "zone_key": "upper_wall",
      "label": "Upper wall",
      "description": "Upper floor exterior wall",
      "estimated_sqft": 320.0
    }
  ],
  "approx_front_width_ft": 28.0,
  "approx_floor_height_ft": 10.0,
  "num_floors": 2,
  "confidence": "low" or "medium" or "high",
  "notes": ""
}

Return ONLY valid JSON. No markdown. No explanation. No extra text."""

    return call_groq_with_image(image_path, prompt)
