import logging

from app.ai.generation.local_generator import generate_image_local
from app.ai.generation.replicate_generator import generate_image_replicate
from app.core.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger("house_renovation")


def generate_image(
    image_path: str,
    prompt: str,
    output_path: str,
    mask_path: str | None = None,
    preserve_unmasked: bool = True,
) -> dict:
    backend = (settings.IMAGE_GENERATOR_BACKEND or "replicate").strip().lower()
    fallback_backend = (settings.IMAGE_GENERATOR_FALLBACK_BACKEND or "none").strip().lower()

    if backend == "replicate":
        last_exc = None
        # Retry only transient provider errors (timeouts, 5xx, rate limit). A 4xx
        # like 402 (no credit) / 401 (bad token) won't fix itself, so fail fast.
        for attempt in range(2):
            try:
                return generate_image_replicate(image_path, prompt, output_path, mask_path)
            except Exception as exc:
                last_exc = exc
                logger.warning("Replicate generation attempt %d failed: %s", attempt + 1, exc)
                status = getattr(exc, "status", None)
                transient = status is None or status == 429 or status >= 500
                if not transient:
                    break
        if fallback_backend == "local":
            logger.info("Falling back to local image generation")
            return generate_image_local(image_path, prompt, output_path, mask_path, preserve_unmasked)
        raise AIServiceError(_friendly_replicate_error(last_exc))

    if backend == "local":
        return generate_image_local(image_path, prompt, output_path, mask_path, preserve_unmasked)

    raise ValueError(f"Unsupported IMAGE_GENERATOR_BACKEND: {backend}")


def _friendly_replicate_error(exc: Exception) -> str:
    status = getattr(exc, "status", None)
    if status == 402:
        return (
            "Image generation is unavailable: the Replicate account is out of credit. "
            "Add credit at replicate.com/account/billing, or set "
            "IMAGE_GENERATOR_BACKEND=local in backend/.env to generate offline."
        )
    if status == 401:
        return "Image generation failed: invalid REPLICATE_API_TOKEN. Check backend/.env."
    return f"Image generation failed: {exc}"
