from typing import Any

from app.ai.groq_client import call_groq_with_image


def detect_zones(image_path: str) -> dict[str, Any]:
    prompt = """Analyze this house exterior photo and identify structural renovation zones.

Identify zones such as: upper_wall, lower_wall, balcony, railing, parapet, entrance, columns, roof_edge, etc.

For each zone:
- estimate the visible surface area in square feet based on typical Indian residential proportions.
- give a bounding box "box_2d" of the region in the image as normalized percentages
  {"x": left%, "y": top%, "w": width%, "h": height%} where each value is 0-100
  (e.g. the upper-left quarter is {"x":0,"y":0,"w":50,"h":50}). This lets the user
  see the detected region overlaid on the photo.

Return JSON only with this exact structure:
{
  "zones": [
    {
      "zone_key": "upper_wall",
      "label": "Upper wall",
      "description": "Upper floor exterior wall",
      "estimated_sqft": 320.0,
      "box_2d": {"x": 10, "y": 5, "w": 80, "h": 35}
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
