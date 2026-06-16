# House Renovation AI

AI-powered exterior house renovation planning: upload a photo, detect zones, choose materials, generate a renovated preview, estimate costs, and download a PDF report.

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- [Groq API key](https://console.groq.com/keys)
- [Replicate API token](https://replicate.com/account/api-tokens)

## Backend setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in GROQ_API_KEY and REPLICATE_API_TOKEN
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Celery worker

In a separate terminal (with venv activated):

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173

## API docs

http://localhost:8000/docs

## Project structure

- `backend/app/api/` — FastAPI routers (thin layer)
- `backend/app/crud/` — business logic
- `backend/app/ai/` — Groq vision, OpenCV, Replicate integrations
- `frontend/src/` — React 5-step wizard

## Environment variables

See `backend/.env.example` and `frontend/.env.example`.

# house-renovation
