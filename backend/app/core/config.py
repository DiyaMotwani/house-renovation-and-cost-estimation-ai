from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/house_renovation"
    REDIS_URL: str = "redis://localhost:6379/0"
    GROQ_API_KEY: str = ""
    GROQ_VISION_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    DEBUG: bool = True
    STORAGE_UPLOAD_DIR: str = "storage/uploads"
    STORAGE_GENERATED_DIR: str = "storage/generated"
    STORAGE_REPORTS_DIR: str = "storage/reports"
    # Image generation via Replicate (fast cloud GPU) or local CPU diffusion.
    REPLICATE_API_TOKEN: str = ""
    REPLICATE_MODEL: str = "black-forest-labs/flux-2-pro"
    REPLICATE_RESOLUTION: str = "1 MP"
    REPLICATE_ASPECT_RATIO: str = "4:3"
    REPLICATE_OUTPUT_FORMAT: str = "webp"
    REPLICATE_OUTPUT_QUALITY: int = 85
    REPLICATE_SAFETY_TOLERANCE: int = 2
    REPLICATE_STEPS: int = 20
    HF_IMAGE_MODEL: str = "stabilityai/sd-turbo"
    IMAGE_GENERATOR_BACKEND: str = "replicate"
    IMAGE_GENERATOR_FALLBACK_BACKEND: str = "none"
    IMAGE_MAX_SIZE: int = 384
    IMAGE_STEPS: int = 2
    IMAGE_STRENGTH: float = 0.55

    @property
    def upload_dir(self) -> Path:
        return BASE_DIR / self.STORAGE_UPLOAD_DIR

    @property
    def generated_dir(self) -> Path:
        return BASE_DIR / self.STORAGE_GENERATED_DIR

    @property
    def reports_dir(self) -> Path:
        return BASE_DIR / self.STORAGE_REPORTS_DIR


settings = Settings()
