import json
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parent / "materials.json"


def load_catalog() -> list[dict[str, Any]]:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_material_by_id(material_id: str) -> dict[str, Any] | None:
    for material in load_catalog():
        if material["id"] == material_id:
            return material
    return None
