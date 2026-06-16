import os
import time
from pathlib import Path
from urllib.request import urlretrieve

import replicate
from PIL import Image

from app.core.config import settings


def _ensure_token() -> None:
    token = (settings.REPLICATE_API_TOKEN or "").strip()
    if not token or token == "your_replicate_api_token_here":
        raise ValueError(
            "REPLICATE_API_TOKEN is missing. Get one at https://replicate.com/account/api-tokens"
        )
    os.environ["REPLICATE_API_TOKEN"] = token


def _save_output(output, output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(output, str):
        url = output
    elif isinstance(output, list) and output:
        url = str(output[0])
    elif hasattr(output, "read"):
        out.write_bytes(output.read())
        return
    else:
        url = str(output)

    tmp = out.with_suffix(out.suffix + ".tmp")
    urlretrieve(url, tmp)
    with Image.open(tmp) as img:
        img.convert("RGB").save(out, format="PNG")
    tmp.unlink(missing_ok=True)


def generate_image_replicate(
    image_path: str,
    prompt: str,
    output_path: str,
    mask_path: str | None = None,
) -> dict:
    _ensure_token()
    t0 = time.time()
    model = settings.REPLICATE_MODEL or "black-forest-labs/flux-2-pro"

    full_prompt = (
        f"{prompt}. Photorealistic exterior house renovation. "
        "Preserve the original building structure, roofline, windows, and perspective. "
        "Realistic materials, natural daylight, high quality."
    )
    if mask_path and Path(mask_path).exists():
        full_prompt += " Apply renovation only to the masked/edit regions described in the prompt."

    with open(image_path, "rb") as house_image:
        output = replicate.run(
            model,
            input={
                "prompt": full_prompt,
                "resolution": settings.REPLICATE_RESOLUTION,
                "aspect_ratio": settings.REPLICATE_ASPECT_RATIO,
                "input_images": [house_image],
                "output_format": settings.REPLICATE_OUTPUT_FORMAT,
                "output_quality": settings.REPLICATE_OUTPUT_QUALITY,
                "safety_tolerance": settings.REPLICATE_SAFETY_TOLERANCE,
            },
        )

    _save_output(output, output_path)
    elapsed_ms = int((time.time() - t0) * 1000)
    return {"output_path": output_path, "backend": f"replicate:{model}", "elapsed_ms": elapsed_ms}
