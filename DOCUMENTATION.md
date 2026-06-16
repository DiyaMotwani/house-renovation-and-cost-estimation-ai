# House Renovation AI — System Documentation

AI-powered exterior renovation planning. A homeowner uploads a photo of their house,
the system detects renovatable zones, lets them apply materials and generate a
realistic redesigned preview, estimates surface areas and material quantities, and
produces a transparent, contractor-ready cost report — all before any construction
begins.

This single document covers the system architecture, the user workflow, how the
estimation works, and the known limitations (the required project deliverables),
plus setup and the full feature/endpoint reference.

---

## 1. System Architecture

```
┌──────────────┐      REST + X-Owner-Token       ┌─────────────────────────┐
│  React (Vite)│  ───────────────────────────►   │  FastAPI (app/main.py)  │
│  5-step wizard│  ◄───────────────────────────   │  thin routers (api/v1)  │
└──────────────┘        JSON {success,msg,data}   └───────────┬─────────────┘
                                                              │ business logic
                                                  ┌───────────▼─────────────┐
                                                  │  CRUD layer (app/crud)   │
                                                  └───┬───────────┬─────────┘
                                          SQLAlchemy  │           │  enqueue
                                                  ┌───▼────┐  ┌───▼─────────────┐
                                                  │Postgres│  │ Celery + Redis  │
                                                  └────────┘  │ (ai_worker.py)  │
                                                              └───┬─────────────┘
                                                   AI providers   │
                                       ┌───────────────┬──────────┴───────────┐
                                       │ Groq Vision   │  Replicate (Flux)    │
                                       │ validate/zones│  image generation    │
                                       │ analyse/suggest│  (local diffusers    │
                                       └───────────────┘   fallback) + OpenCV  │
```

**Layers**
- **Frontend** (`frontend/src`): a React wizard. `services/api.js` is the single API
  client; it attaches an anonymous `X-Owner-Token` to every request and exposes typed
  helpers. Steps live under `components/{upload,zones,generation,estimation,report}`.
  Shared UI in `components/ui/kit.jsx`; design-variant controls in
  `components/variants/VariantBar.jsx`.
- **API** (`app/api/v1/endpoints`): thin FastAPI routers that validate input (Pydantic
  schemas in `app/schemas`) and delegate to CRUD. Sub-resource routers enforce ownership
  via the `verify_project_owner` dependency (`app/api/deps.py`).
- **CRUD / business logic** (`app/crud`): project, image, zone, variant, estimation,
  generation, report, task.
- **Workers** (`app/workers/ai_worker.py`): long-running AI work (image validation,
  zone detection, analysis, suggestions, renovation generation) runs in Celery so the
  API stays responsive.
- **AI integrations** (`app/ai`): Groq vision client, OpenCV edge sketch, Replicate /
  local-diffusers image generation.
- **Persistence**: PostgreSQL via SQLAlchemy; schema migrations via Alembic.
- **Files**: uploaded/generated/report files under `backend/storage`, served at
  `/storage`.

**Response convention.** Every endpoint returns `{ "success": bool, "msg": str, "data": ... }`.
Expected business problems return `success:false` with a message; unexpected errors are
caught by a global handler that logs the traceback server-side and returns a clean
`500` (`AppError` subclasses map to specific codes, e.g. AI-unavailable → `503`).

---

## 2. User Workflow (5-step wizard)

1. **Upload** — name the project and upload a clear exterior photo (JPG/PNG). The image
   is validated (a real house, sharp, sufficient resolution); poor images are rejected
   with guidance. On success the backend detects zones, sketches edges, analyses the
   house and suggests materials.
2. **Zones & Materials** — review the detected zones and **correct anything**: rename a
   zone, change its area, delete a wrong one, or **add** a missed one. Assign a material
   to each zone. Optionally enter the real front width to calibrate areas. All material
   choices belong to the **active design variant**.
3. **Preview** — generate a redesigned image that keeps the original structure and
   applies the chosen materials. Each design is generated **once** (create another design
   to try a different combination). Create additional **designs** (variants) and generate
   a preview for each; **Compare** shows them side by side with costs.
4. **Estimate** — an itemised Bill of Quantities for the active design: area, quantity
   (incl. wastage), unit rate, material cost, labour rate, labour cost, line total, then
   subtotals, GST and total payable. Unit/labour rates are editable and recalculate live.
5. **Report** — a downloadable PDF (before/after images, materials, quantities, full cost
   breakdown) for the **active design**, suitable for discussing with contractors. Switch
   the active design in the Designs bar to report a different one. (One report PDF is kept
   per project at a time — regenerating for another design replaces it.)

Progress is saved per browser (resume on refresh); **New project** starts fresh.

---

## 3. Design Variants (compare combinations)

A project holds one or more **design variants**, each a complete set of zone→material
choices with its **own** generated preview and its **own** estimate.

- Switch/create/rename/delete variants from the **Designs** bar on the Zones, Preview and
  Estimate steps. A new design copies the active design's materials as a starting point.
- The currently selected variant is the **active** one; all step actions default to it.
- **Compare** (`GET /variants/compare`) returns each variant's preview image and headline
  totals for side-by-side evaluation.

Backward compatibility: projects created before variants existed are migrated lazily —
the first variant-aware call creates a default "Design 1" and attaches the existing
materials, estimate and preview to it.

---

## 4. How the Estimation Works

### 4.1 Surface-area basis (`app/utils/area_estimator.py`)
Areas are advisory and derived in priority order:
1. **User measurement** — if the homeowner entered the real front width, every zone area
   is scaled linearly to it (`scale_factor = user_width / detected_width`). Confidence ≈ 0.95.
2. **Reference object** — if the vision model spotted a known-size object (car ≈ 15 ft,
   door ≈ 3.5 ft, window ≈ 4 ft, …), the detected front-width estimate is treated as
   reference-anchored. Confidence from the model (~0.6).
3. **Vision estimate** — proportions inferred from the image alone. Confidence ~0.5.
4. **Architectural prior** — if a zone has no usable area, fall back to
   `front_width × floor_height × floors × 0.75` (min 120 sqft).

Each line records which basis (`dimension_anchor_used`) and `dimension_confidence` were
used, surfaced in the UI and report so numbers are clearly **advisory, not surveyed**.

### 4.2 Quantity & cost (`app/utils/cost_calculator.py`)
Per zone, using the material catalog (`app/catalog/materials.json`):

```
base_qty      = (area_sqft / coverage_sqft_per_unit) × coats_required
wastage_qty   = base_qty × wastage_factor
qty_required  = base_qty + wastage_qty
material_cost = qty_required × unit_price        (unit_price overridable)
labour_cost   = area_sqft   × labour_rate        (labour_rate overridable)
total_cost    = material_cost + labour_cost
estimated_days= area_sqft × days_per_100_sqft / 100
```

**Rate overrides.** A user can edit the unit rate and labour rate per line. An override
applies only when it is a positive number; clearing it (or 0) restores the catalog rate.

### 4.3 Summary & GST
The summary sums material and labour subtotals, then applies GST
(`GST_RATE_PCT = 18%`, the works-contract composite rate; `app/core/constants.py`) on top
to present a realistic **total payable**. The catalog rates and per-line math are never
altered by GST — it is a separate, transparent line.

### 4.4 Materials catalog
Eight materials covering every required category: smooth paint, sand texture, terracotta
brick cladding, natural stone cladding, vitrified tiles, glass railing, metal railing,
aluminium composite panel. Each defines `unit`, `unit_price_inr`, `coverage_sqft_per_unit`,
`coats_required`, `wastage_factor`, `labour_rate_per_sqft_inr`, `days_per_100_sqft` and a
`prompt_keyword` used during image generation.

---

## 5. Renovation Visualization

`app/workers/ai_worker.py::task_generate_renovation` builds a prompt from each zone's
material `prompt_keyword`, wraps it with structure-preservation instructions
(`masked_generation_prompt`) and calls the configured backend:
- **Replicate** (default, `black-forest-labs/flux-2-pro`) — img2img preserving geometry;
- **Local diffusers** fallback (`stabilityai/sd-turbo`) — composites unmasked regions to
  keep them unchanged.

A **mask** can restrict edits to specific areas — this is supported by the backend
(`mask_image_path`) but is not exposed in the current UI. On Replicate it nudges the
prompt; locally it composites the unmasked regions back. The result is saved as a
generated image tagged with its variant, so each design keeps its own preview, and a
design is generated once (regenerate is not offered — create a new design instead).

---

## 6. Multi-user (lightweight, anonymous)

There is no login. The frontend generates a random token per browser
(`localStorage: hra_owner_token`) and sends it as `X-Owner-Token`. Projects are stamped
with that token on creation; `GET /projects` only lists the caller's projects, and every
project sub-resource is guarded by `verify_project_owner` (403 on mismatch, 404 if
missing). Legacy projects with no token remain open for backward compatibility.

> This isolates concurrent users without account management. For production, replace the
> token with authenticated user accounts.

---

## 7. API Reference (prefix `/api/v1`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/projects/` | Create project (stamps owner token) |
| GET | `/projects/` | List the caller's projects |
| GET/PUT/DELETE | `/projects/{id}` | Get / rename / delete (owner-guarded) |
| GET | `/projects/{id}/analysis` | House analysis + dimension hints |
| PUT | `/projects/{id}/scale-anchor` | Set real front width (calibration) |
| POST | `/projects/{id}/images/upload` | Upload & validate photo (replaces previous) |
| GET | `/projects/{id}/images/` | List images |
| POST | `/projects/{id}/images/mask` | Upload edit mask |
| GET | `/projects/{id}/zones/` | List zones (`?variant_id=`) |
| POST | `/projects/{id}/zones/` | **Add** a zone |
| PUT | `/projects/{id}/zones/{zid}` | Edit label/description/area/box |
| DELETE | `/projects/{id}/zones/{zid}` | **Delete** a zone |
| POST | `/projects/{id}/zones/assign` | Assign materials (`?variant_id=`) |
| GET | `/projects/{id}/variants/` | List design variants |
| POST | `/projects/{id}/variants/` | Create variant (copies active) |
| PUT | `/projects/{id}/variants/{vid}/activate` | Switch active variant |
| PUT/DELETE | `/projects/{id}/variants/{vid}` | Rename / delete variant |
| GET | `/projects/{id}/variants/compare` | Side-by-side previews + costs |
| GET | `/catalog/materials/` | Material catalog |
| POST | `/projects/{id}/generate/` | Trigger preview (`variant_id` in body) |
| GET | `/projects/{id}/generate/status` | Generation status |
| POST | `/projects/{id}/estimation/run` | Run estimate (`?variant_id=`) |
| GET | `/projects/{id}/estimation/` | Fetch saved estimate (`?variant_id=`) |
| POST | `/projects/{id}/estimation/recalculate` | Recalc with rate overrides |
| POST | `/projects/{id}/report/generate` | Build PDF (`?variant_id=`) |
| GET | `/projects/{id}/report/download` | Download PDF |
| GET | `/tasks/{task_id}/status` | Async task status |

Interactive docs: `http://localhost:8000/docs`.

---

## 8. Data Model (key tables)

- **projects** — name, status, `owner_token`, scale/dimension metadata, AI analysis.
- **design_variants** — `project_id`, `name`, `is_active`.
- **project_images** — original / sketch / generated / mask; generated rows carry `variant_id`.
- **project_zones** — `zone_key`, `label`, `description`, `estimated_sqft`, `box_2d` (normalized %).
- **zone_material_assignments** — `(variant_id, zone_id)` unique → one material per zone per design.
- **project_estimations** — per-line costs, `variant_id`, override rates, dimension provenance.
- **renovation_reports** — generated PDF metadata.

---

## 9. Setup & Run

**Prerequisites:** Python 3.10+, Node 18+, PostgreSQL 14+, Redis 6+, a Groq API key and a
Replicate token.

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill GROQ_API_KEY, REPLICATE_API_TOKEN, DATABASE_URL
alembic upgrade head            # create/upgrade schema
uvicorn app.main:app --reload --port 8000

# Celery worker (separate terminal, venv active)
celery -A app.workers.celery_app worker --loglevel=info

# Frontend (separate terminal)
cd frontend && npm install && cp .env.example .env && npm run dev   # http://localhost:5173
```

---

## 10. Limitations (important)

- **Estimates are advisory, not a quotation.** Areas come from AI/vision proportions and
  optional user calibration — not surveyed measurements.
- **No true pixel geometry.** Reference objects calibrate confidence and front-width, but
  the system does not extract reference-object pixel boxes; scaling is linear, not
  perspective-corrected.
- **AI dependence.** Validation, zone detection, analysis and suggestions require a valid
  `GROQ_API_KEY`; image generation requires `REPLICATE_API_TOKEN` (or the slower local
  diffusers fallback). When a provider is unconfigured/unavailable the affected step
  reports an AI-service error (HTTP 503 / task failure) rather than crashing.
- **Zone geometry is approximate.** The vision model returns a `box_2d` bounding box per
  zone (stored, not currently shown in the UI); it is not a pixel-accurate segmentation
  mask. Zones are reviewed/corrected as a text list (label, area, add/remove).
- **One report per project.** A single report PDF is stored per project at a time, for
  the active design; regenerating for another design replaces it.
- **Lightweight multi-user (no login).** A random per-browser token (sent as
  `X-Owner-Token`, or `?token=` for direct downloads) isolates each session's projects.
  It is isolation, not authentication — anyone with a project's token can access it, and
  clearing browser storage or switching device starts a new empty session.
- **Residential, low-rise, exterior only.** No interior design and no structural
  engineering; matches the project assumptions.
- **Generation fidelity** depends on the third-party model; structure preservation is
  guided by prompt + mask, not guaranteed pixel-for-pixel.
