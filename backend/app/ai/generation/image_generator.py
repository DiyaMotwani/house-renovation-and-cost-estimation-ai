from app.ai.generation.local_generator import generate_image_local
from app.ai.generation.replicate_generator import generate_image_replicate
from app.core.config import settings


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
        try:
            return generate_image_replicate(image_path, prompt, output_path, mask_path)
        except Exception as exc:
            if fallback_backend == "local":
                return generate_image_local(
                    image_path, prompt, output_path, mask_path, preserve_unmasked
                )
            raise RuntimeError("Replicate image generation failed; local fallback is disabled") from exc

    if backend == "local":
        return generate_image_local(image_path, prompt, output_path, mask_path, preserve_unmasked)

    raise ValueError(f"Unsupported IMAGE_GENERATOR_BACKEND: {backend}")
