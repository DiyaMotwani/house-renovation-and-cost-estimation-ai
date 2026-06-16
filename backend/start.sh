#!/bin/bash
set -e

# Run migrations
alembic upgrade head

# Start web server in background
uvicorn app.main:app --host 0.0.0.0 --port $PORT &
WEB_PID=$!

# Start worker in foreground
celery -A app.workers.celery_app worker --loglevel=info &
WORKER_PID=$!

# Keep container running
wait $WEB_PID $WORKER_PID
