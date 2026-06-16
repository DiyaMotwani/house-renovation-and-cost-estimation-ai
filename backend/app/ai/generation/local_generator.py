import os
import threading
import time
from pathlib import Path

import torch
from diffusers import AutoPipelineForImage2Image
from PIL import Image

from app.core.config import settings

_pipe = None
_lock = threading.Lock()


def _build_pipeline(model_id: str):
    try:
        pipe = AutoPipelineForImage2Image.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            variant="fp16",
            safety_checker=None,
            requires_safety_checker=False,
        )
    except Exception:
        pipe = AutoPipelineForImage2Image.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
        )
    pipe.to("cpu")
    pipe.set_progress_bar_config(disable=True)
    return pipe


def _select_backend_model() -> str:
    backend = (settings.IMAGE_GENERATOR_BACKEND or "local").strip().lower()
    if backend == "tiny_sd":
        return "segmind/tiny-sd"
    return settings.HF_IMAGE_MODEL


def _get_pipeline():
    global _pipe
    if _pipe is not None:
        return _pipe
    with _lock:
        if _pipe is None:
            threads = int(os.getenv("IMAGE_NUM_THREADS", "0"))
            if threads > 0:
                torch.set_num_threads(threads)
            model_id = _select_backend_model()
            try:
                _pipe = _build_pipeline(model_id)
            except Exception:
                _pipe = _build_pipeline(settings.HF_IMAGE_MODEL)
    return _pipe


def _prepare_image(path: str, target: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    scale = target / max(w, h)
    nw = max(8, int(w * scale) - (int(w * scale) % 8))
    nh = max(8, int(h * scale) - (int(h * scale) % 8))
    return img.resize((nw, nh), Image.LANCZOS)


def _load_mask(mask_path: str | None, target_size: tuple[int, int]) -> Image.Image | None:
    if not mask_path:
        return None
    mask_img = Image.open(mask_path).convert("L")
    if mask_img.size != target_size:
        mask_img = mask_img.resize(target_size, Image.NEAREST)
    return mask_img


def generate_image_local(
    image_path: str,
    prompt: str,
    output_path: str,
    mask_path: str | None = None,
    preserve_unmasked: bool = True,
) -> dict:
    t0 = time.time()
    pipe = _get_pipeline()
    init_image = _prepare_image(image_path, settings.IMAGE_MAX_SIZE)
    mask_img = _load_mask(mask_path, init_image.size)

    full_prompt = (
        f"{prompt}, photorealistic exterior of a residential house, "
        "preserve the original building structure and layout, "
        "realistic materials and lighting, high quality"
    )

    kwargs = dict(
        prompt=full_prompt,
        image=init_image,
        num_inference_steps=settings.IMAGE_STEPS,
        strength=settings.IMAGE_STRENGTH,
        guidance_scale=0.0,
    )
    if mask_img is not None:
        kwargs["mask_image"] = mask_img
    result = pipe(**kwargs).images[0]
    if mask_img is not None and preserve_unmasked:
        result = Image.composite(result, init_image, mask_img)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.save(out)
    elapsed_ms = int((time.time() - t0) * 1000)
    return {"output_path": str(out), "backend": f"local:{_select_backend_model()}", "elapsed_ms": elapsed_ms}
