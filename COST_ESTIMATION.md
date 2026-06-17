# Cost Estimation — How It Works

This document explains, in detail, how the House Renovation AI system turns a photo of
a house into a transparent, per-zone cost estimate. It maps directly to requirements
**5.5 (surface area), 5.6 (material quantity), and 5.7 (cost)** and serves as the
"documentation explaining how the estimation works" deliverable.

> **Advisory only.** Every number here is a pre-construction planning aid, not a surveyed
> measurement or a binding quotation.

---

## 1. The pipeline (per zone)

For each detected zone (upper wall, balcony, railing, …) the system runs four steps:

```
 detected zone ──► (5.5) surface area ──► (5.6) quantity + wastage ──► (5.7) cost
```

1. **Surface area** of the zone is estimated (sqft) — see §3.
2. The zone's assigned **material** (from the catalog) defines coverage, wastage, rates.
3. **Quantity** to purchase is computed (incl. wastage) — see §4.
4. **Material + labour cost** is computed, then rolled up with GST — see §5.

Code: [`app/utils/cost_calculator.py`](backend/app/utils/cost_calculator.py),
[`app/utils/area_estimator.py`](backend/app/utils/area_estimator.py),
[`app/crud/estimation_crud.py`](backend/app/crud/estimation_crud.py).

---

## 2. Material catalog

The catalog ([`app/catalog/materials.json`](backend/app/catalog/materials.json)) is the
single source of rates. Each material defines:

| Field | Meaning |
|-------|---------|
| `unit` | how the material is bought (litre / tiles / sqft / rft) |
| `unit_price_inr` | price per unit |
| `coverage_sqft_per_unit` | sqft covered by one unit (e.g. 80 sqft per litre of paint) |
| `coats_required` | number of coats/layers |
| `wastage_factor` | wastage allowance (0.10 = 10%) |
| `count_based` | `true` for countable items (tiles) → rounded up to whole units |
| `labour_rate_per_sqft_inr` | labour charge per sqft of surface |
| `prompt_keyword` | used by the image generator (not costing) |

Current catalog:

| Material | Category | Unit | Price ₹ | Coverage | Coats | Wastage | Labour ₹/sqft |
|----------|----------|------|--------:|---------:|------:|--------:|--------------:|
| Exterior smooth paint | paint | litre | 320 | 80 sqft/L | 2 | 10% | 18 |
| Sand texture finish | texture | litre | 450 | 60 sqft/L | 2 | 12% | 25 |
| Terracotta brick cladding | cladding | sqft | 180 | 1 | 1 | 8% | 45 |
| Vitrified exterior tiles | tile | **tiles** | 190 | **2 sqft/tile** | 1 | 10% | 35 |
| Glass railing | railing | rft | 1200 | 1 | 1 | 5% | 200 |
| Metal railing | railing | rft | 650 | 1 | 1 | 5% | 120 |
| Natural stone cladding | cladding | sqft | 350 | 1 | 1 | 10% | 55 |
| Aluminium composite panel | panel | sqft | 220 | 1 | 1 | 8% | 40 |

Covers every material type the spec lists: paint, texture, stone/brick cladding, tiles,
glass & metal railing, panel.

---

## 3. Surface area estimation (5.5)

Each zone's area (`area_sqft`) is derived in priority order, and the **basis + confidence**
are recorded and shown so the figure is transparently advisory:

| Priority | Basis (`dimension_anchor_used`) | When | Confidence |
|----------|-------------------------------|------|-----------|
| 1 | `user_measurement` | user entered the real front width → all areas scale linearly | 0.95 |
| 2 | `reference:<object>` | vision model anchored the width to a known object (car ≈ 15 ft, door ≈ 3.5 ft…) | ~0.6 |
| 3 | `vision_estimate` | proportions inferred from the image alone | ~0.5 |
| 4 | `architectural_prior` | zone had no usable area → `width × floor_height × floors × 0.75` | ~0.35 |

The **user front width** (optional, Step 2) sets `scale_factor = user_width / detected_width`,
applied to every zone — the system's most reliable calibration.

---

## 4. Quantity & wastage (5.6)

```
base_qty     = (area_sqft / coverage_sqft_per_unit) × coats_required   # net material
wastage_qty  = base_qty × wastage_factor                               # allowance
qty_required = base_qty + wastage_qty                                  # what you order
# countable items (tiles): qty_required = ceil(qty_required)           # whole units only
```

- **Wastage** is added on top of the net quantity (cutting/breakage/spillage), and the cost
  is charged on `qty_required` — i.e. you pay for the wastage too, as in real quotations.
- **Coverage** converts surface area into purchase units (paint litres, tiles, …).
- Quantity is shown in the **correct unit per material**, matching the spec examples:
  - Paint / texture → **litres**
  - Tiles → **number of tiles** (whole count)
  - Stone / brick cladding, panel → **sqft** (these are genuinely sold by the square foot, so
    a sqft *quantity* is valid here — it is the purchase unit, not a duplicate of the area)
  - Railing → **running feet (rft)**

---

## 5. Cost, rate overrides & totals (5.7)

```
material_cost = qty_required × unit_price        # unit_price is user-overridable
labour_cost   = area_sqft     × labour_rate      # labour_rate is user-overridable
line_total    = material_cost + labour_cost
```

Roll-up (summary):

```
material_subtotal = Σ material_cost
labour_subtotal   = Σ labour_cost
gst_amount        = (material_subtotal + labour_subtotal) × 18%   # works-contract composite GST
grand_total       = material_subtotal + labour_subtotal + gst_amount   # GST-INCLUSIVE
```

The headline figure shown to the user (UI and report) is the **Grand Total (incl. GST)** —
i.e. material + labour + GST. The material and labour subtotals and the GST line are shown
above it for transparency.

**Rate overrides.** The user can edit any line's **unit rate** and **labour rate**; the
estimate recalculates live. An override applies only when it's a positive number; clearing
the field (or 0) restores the catalog rate. GST % is a constant
([`app/core/constants.py`](backend/app/core/constants.py) `GST_RATE_PCT = 18.0`) and never
alters the per-line rates — it's a separate, transparent line.

---

## 6. Worked example

**Upper wall, 240 sqft, Exterior smooth paint** (coverage 80, coats 2, wastage 10%,
₹320/L, labour ₹18/sqft):

```
base_qty     = (240 / 80) × 2 = 6 litre
qty_required = 6 × 1.10       = 6.6 litre
material     = 6.6 × 320      = ₹2,112
labour       = 240 × 18       = ₹4,320
line total                    = ₹6,432
```

**A wall in tiles, 100 sqft** (2 sqft/tile, wastage 10%, ₹190/tile):

```
base_qty     = (100 / 2) × 1  = 50 tiles
qty_required = ceil(50 × 1.10) = 55 tiles
material     = 55 × 190        = ₹10,450   (≡ ₹95/sqft effective)
labour       = 100 × 35        = ₹3,500
line total                     = ₹13,950
```

---

## 7. Where it appears

- **Estimate step (UI):** one row per detected zone — Zone · Material/Coverage · Surface
  Area (with derivation basis) · Quantity Required · Unit Rate (editable) · Material ·
  Labour rate (editable) · Labour · Total; then Material/Labour subtotals → Subtotal →
  GST → Total Payable.
- **PDF report:** a "Detected Zones & Surface Areas" table (area + coverage + basis) and a
  "Cost Breakdown (Bill of Quantities)" table with the same per-line figures and the
  subtotal/GST/total payable roll-up.

Per design **variant**, the estimate is independent (different materials → different cost),
and `/variants/compare` shows headline totals side by side.

---

## 8. Relevant API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/projects/{id}/estimation/run` | Compute the estimate for a variant |
| GET  | `/projects/{id}/estimation/` | Fetch the saved estimate |
| POST | `/projects/{id}/estimation/recalculate` | Recompute with rate overrides |

All accept an optional `?variant_id=` (defaults to the active design).

---

## 9. Limitations

- Areas are AI/vision-derived or user-calibrated — **approximate**, not surveyed; no
  pixel-accurate perspective geometry.
- Rates are catalog defaults (editable) — not live market prices.
- GST is a single composite 18%; real projects may split CGST/SGST or vary by item.
- **Duration/working days is intentionally not shown** — the requirement does not ask for
  it; it is computed internally only. (Easy to surface if ever required.)
- Estimates are advisory and not a legally binding quotation.
