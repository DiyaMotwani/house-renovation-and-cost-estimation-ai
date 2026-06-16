import base64
import json
import re
from pathlib import Path
from typing import Any

from groq import Groq

from app.core.config import settings
from app.core.exceptions import AIServiceError


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        raise


def _image_to_data_uri(image_path: str) -> str:
    path = Path(image_path)
    ext = path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def call_groq_with_image(image_path: str, prompt: str) -> dict[str, Any]:
    api_key = (settings.GROQ_API_KEY or "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        raise AIServiceError(
            "The image AI service is not configured. Add a valid GROQ_API_KEY "
            "(from https://console.groq.com/keys) to backend/.env and restart."
        )

    client = Groq(api_key=api_key)
    data_uri = _image_to_data_uri(image_path)

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            temperature=0.2,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
    except AIServiceError:
        raise
    except Exception as e:  # network / auth / rate-limit from the provider
        raise AIServiceError(f"The image AI service is temporarily unavailable: {e}") from e

    content = response.choices[0].message.content or ""
    return _extract_json(content)
