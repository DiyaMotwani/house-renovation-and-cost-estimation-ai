from typing import Any


def build_prompt(zone_assignments: list[dict[str, Any]]) -> str:
    parts = [
        "photorealistic renovated house exterior, architectural photography, daylight, high detail"
    ]
    for assignment in zone_assignments:
        zone_label = assignment.get("zone_label", assignment.get("zone_key", "zone"))
        keyword = assignment.get("prompt_keyword", "")
        if keyword:
            parts.append(f"{zone_label}: {keyword}")
    return ", ".join(parts)
