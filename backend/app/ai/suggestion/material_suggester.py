from typing import Any

from app.ai.groq_client import call_groq_with_image
from app.ai.prompts import material_suggestion_prompt


def suggest_materials(image_path: str, house_context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = ""
    if house_context:
        context = (
            f"House description: {house_context.get('house_description', '')}\n"
            f"Renovation needs: {house_context.get('renovation_needs', [])}\n"
            f"Style hint: {house_context.get('style_hint', 'mixed')}\n"
        )
    result = call_groq_with_image(image_path, material_suggestion_prompt(context))
    suggestions = result.get("suggestions", [])
    return {
        "suggestions": suggestions,
        "overall_style": result.get("overall_style", "mixed"),
        "global_reasoning": result.get("global_reasoning", ""),
    }
