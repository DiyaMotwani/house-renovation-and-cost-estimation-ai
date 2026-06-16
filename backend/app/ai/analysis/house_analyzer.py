from typing import Any

from app.ai.groq_client import call_groq_with_image
from app.ai.prompts import house_description_prompt


def analyze_house(image_path: str) -> dict[str, Any]:
    raw = call_groq_with_image(image_path, house_description_prompt())
    return {
        "house_description": raw.get("house_description", ""),
        "renovation_needs": raw.get("renovation_needs", []),
        "renovation_suggestions": raw.get("renovation_suggestions", []),
        "style_hint": raw.get("style_hint", "mixed"),
        "dimension_hints": raw.get("dimension_hints", {}),
    }
