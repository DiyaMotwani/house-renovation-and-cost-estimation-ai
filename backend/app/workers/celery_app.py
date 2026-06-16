from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "house_renovation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    imports=("app.workers.ai_worker",),
    # Each generation worker loads a ~3-4 GB SD pipeline into RAM; cap concurrency
    # so a CPU-only box doesn't fan out 12 copies and OOM.
    worker_concurrency=2,
)
