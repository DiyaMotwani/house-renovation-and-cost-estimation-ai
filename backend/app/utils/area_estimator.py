"""Surface-area basis estimation (requirement 5.5).

We do not have pixel-accurate geometry, so areas are derived from three sources,
in order of trust:

  1. User measurement   — the homeowner entered the real front width; we scale
                          all zone areas linearly to it (most reliable).
  2. Reference object   — the vision model spotted a known-size object (car, door,
                          window…) and estimated the front width against it.
  3. Vision estimate    — proportions inferred from the image alone (least reliable).

Every estimate records which basis was used and a confidence score so the report
can present the numbers as *advisory*, never as surveyed measurements.
"""

# Typical real-world widths (ft) of common reference objects, used to sanity-check
# the vision model's front-width estimate.
REFERENCE_OBJECT_WIDTHS_FT = {
    "car": 15.0,
    "bike": 6.0,
    "motorbike": 6.0,
    "door": 3.5,
    "window": 4.0,
    "person": 1.5,
}


def derive_area_basis(project, zone) -> tuple[float, str, float, str]:
    """Return (area_sqft, anchor, confidence, reasoning) for one zone."""
    hints = project.dimension_hints or {}
    ref = (hints.get("detected_reference_object") or "none").lower()
    vision_conf = hints.get("confidence")
    base_area = (zone.estimated_sqft or 0) * (project.scale_factor or 1.0)

    if base_area > 0:
        if project.user_front_width_ft:
            return (
                base_area,
                "user_measurement",
                0.95,
                f"Area calibrated to your measured front width of {project.user_front_width_ft:g} ft.",
            )
        if ref in REFERENCE_OBJECT_WIDTHS_FT:
            ref_ft = REFERENCE_OBJECT_WIDTHS_FT[ref]
            return (
                base_area,
                f"reference:{ref}",
                float(vision_conf) if vision_conf is not None else 0.6,
                f"Area scaled using a detected {ref} (~{ref_ft:g} ft) as a size reference. "
                f"{hints.get('reasoning', '')}".strip(),
            )
        return (
            base_area,
            "vision_estimate",
            float(vision_conf) if vision_conf is not None else 0.5,
            "Area estimated from image proportions; no reference object detected (advisory).",
        )

    # No usable zone area — fall back to architectural priors.
    estimated_width = float(hints.get("estimated_front_width_ft") or 24)
    floor_height = float(hints.get("estimated_floor_height_ft") or 10)
    floors = max(1, int(project.num_floors or 2))
    area = max(120.0, estimated_width * floor_height * floors * 0.75)
    return (
        area,
        ref if ref in REFERENCE_OBJECT_WIDTHS_FT else "architectural_prior",
        float(vision_conf) if vision_conf is not None else 0.35,
        hints.get("reasoning") or "Estimated via typical low-rise residential proportions (advisory).",
    )
