from typing import Any

from app.ai.groq_client import call_groq_with_image


def validate_image(image_path: str) -> dict[str, Any]:
    prompt = """Analyze this image for a house exterior renovation project.

Evaluate:
1. Is this a house exterior photo (not interior, not a random object)?
2. Is the image sharp enough (not heavily blurred)?
3. Is the resolution acceptable for renovation planning (at least 640px on shortest side)?

Return JSON only with this exact structure:
{
  "quality": "pass" or "fail",
  "reason": "explanation if fail, empty string if pass",
  "detected_as": "house exterior" or what you detected,
  "resolution_acceptable": true or false
}

Return ONLY valid JSON. No markdown. No explanation. No extra text."""

    return call_groq_with_image(image_path, prompt)
