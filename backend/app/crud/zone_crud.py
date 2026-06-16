import uuid

from sqlalchemy.orm import Session, joinedload

from app.catalog.loader import get_material_by_id
from app.crud.variant_crud import VariantCRUD
from app.models.renovation_models import ProjectZone, ZoneMaterialAssignment


class ZoneCRUD:
    def __init__(self, db: Session):
        self.db = db
        self.variants = VariantCRUD(db)

    def _attach_assignment(self, zones: list[ProjectZone], variant_id: uuid.UUID) -> None:
        """Expose the assignment for the chosen variant as `zone.material_assignment`
        so the response schema keeps its simple single-assignment shape."""
        for zone in zones:
            match = next((a for a in zone.material_assignments if a.variant_id == variant_id), None)
            zone.material_assignment = match

    def list_zones(self, project_id: uuid.UUID, variant_id: uuid.UUID | None = None) -> dict:
        try:
            variant_id = self.variants.resolve_variant_id(project_id, variant_id)
            zones = (
                self.db.query(ProjectZone)
                .options(joinedload(ProjectZone.material_assignments))
                .filter(ProjectZone.project_id == project_id)
                .order_by(ProjectZone.display_order)
                .all()
            )
            self._attach_assignment(zones, variant_id)
            return {"success": True, "msg": "Zones fetched", "data": zones}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def update_zone(self, project_id: uuid.UUID, zone_id: uuid.UUID, fields: dict) -> dict:
        try:
            zone = (
                self.db.query(ProjectZone)
                .filter(ProjectZone.id == zone_id, ProjectZone.project_id == project_id)
                .first()
            )
            if not zone:
                return {"success": False, "msg": "Zone not found", "data": None}
            for attr in ("label", "description", "estimated_sqft", "box_2d"):
                if attr in fields and fields[attr] is not None:
                    setattr(zone, attr, fields[attr])
            self.db.commit()
            self.db.refresh(zone)
            zone.material_assignment = None
            return {"success": True, "msg": "Zone updated", "data": zone}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def create_zone(self, project_id: uuid.UUID, data: dict) -> dict:
        """Manually add a zone the detector missed (requirement 5.2)."""
        try:
            max_order = (
                self.db.query(ProjectZone)
                .filter(ProjectZone.project_id == project_id)
                .count()
            )
            label = data.get("label") or "New zone"
            zone = ProjectZone(
                id=uuid.uuid4(),
                project_id=project_id,
                zone_key=data.get("zone_key") or f"custom_{uuid.uuid4().hex[:6]}",
                label=label,
                description=data.get("description"),
                estimated_sqft=data.get("estimated_sqft"),
                box_2d=data.get("box_2d"),
                display_order=max_order,
            )
            self.db.add(zone)
            self.db.commit()
            self.db.refresh(zone)
            zone.material_assignment = None
            return {"success": True, "msg": "Zone created", "data": zone}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def delete_zone(self, project_id: uuid.UUID, zone_id: uuid.UUID) -> dict:
        try:
            zone = (
                self.db.query(ProjectZone)
                .filter(ProjectZone.id == zone_id, ProjectZone.project_id == project_id)
                .first()
            )
            if not zone:
                return {"success": False, "msg": "Zone not found", "data": None}
            self.db.delete(zone)
            self.db.commit()
            return {"success": True, "msg": "Zone deleted", "data": {"id": str(zone_id)}}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def save_zones_from_detection(self, project_id: uuid.UUID, zones_data: list[dict]) -> dict:
        try:
            self.db.query(ProjectZone).filter(ProjectZone.project_id == project_id).delete()
            self.db.flush()

            created = []
            for idx, z in enumerate(zones_data):
                zone = ProjectZone(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    zone_key=z["zone_key"],
                    label=z["label"],
                    description=z.get("description"),
                    estimated_sqft=z.get("estimated_sqft"),
                    box_2d=z.get("box_2d"),
                    display_order=idx,
                )
                self.db.add(zone)
                created.append(zone)
            self.db.commit()
            for zone in created:
                self.db.refresh(zone)
            return {"success": True, "msg": "Zones saved", "data": created}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def bulk_assign_materials(
        self, project_id: uuid.UUID, assignments: list[dict], variant_id: uuid.UUID | None = None
    ) -> dict:
        try:
            variant_id = self.variants.resolve_variant_id(project_id, variant_id)
            results = []
            for item in assignments:
                zone_id = item["zone_id"]
                material_id = item["material_id"]
                if not get_material_by_id(material_id):
                    return {"success": False, "msg": f"Invalid material: {material_id}", "data": None}

                zone = (
                    self.db.query(ProjectZone)
                    .filter(ProjectZone.id == zone_id, ProjectZone.project_id == project_id)
                    .first()
                )
                if not zone:
                    return {"success": False, "msg": f"Zone not found: {zone_id}", "data": None}

                existing = (
                    self.db.query(ZoneMaterialAssignment)
                    .filter(
                        ZoneMaterialAssignment.zone_id == zone_id,
                        ZoneMaterialAssignment.variant_id == variant_id,
                    )
                    .first()
                )
                if existing:
                    existing.material_id = material_id
                    results.append(existing)
                else:
                    assignment = ZoneMaterialAssignment(
                        id=uuid.uuid4(),
                        zone_id=zone_id,
                        variant_id=variant_id,
                        material_id=material_id,
                    )
                    self.db.add(assignment)
                    results.append(assignment)

            self.db.commit()
            for r in results:
                self.db.refresh(r)
            return {"success": True, "msg": "Materials assigned", "data": results}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def assign_material(
        self, project_id: uuid.UUID, zone_id: uuid.UUID, material_id: str, variant_id: uuid.UUID | None = None
    ) -> dict:
        return self.bulk_assign_materials(
            project_id, [{"zone_id": zone_id, "material_id": material_id}], variant_id
        )

    def remove_material(
        self, project_id: uuid.UUID, zone_id: uuid.UUID, variant_id: uuid.UUID | None = None
    ) -> dict:
        try:
            variant_id = self.variants.resolve_variant_id(project_id, variant_id)
            zone = (
                self.db.query(ProjectZone)
                .filter(ProjectZone.id == zone_id, ProjectZone.project_id == project_id)
                .first()
            )
            if not zone:
                return {"success": False, "msg": "Zone not found", "data": None}

            assignment = (
                self.db.query(ZoneMaterialAssignment)
                .filter(
                    ZoneMaterialAssignment.zone_id == zone_id,
                    ZoneMaterialAssignment.variant_id == variant_id,
                )
                .first()
            )
            if not assignment:
                return {"success": False, "msg": "No material assigned", "data": None}

            self.db.delete(assignment)
            self.db.commit()
            return {"success": True, "msg": "Material removed", "data": {"zone_id": str(zone_id)}}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def get_zone_assignments_for_generation(
        self, project_id: uuid.UUID, variant_id: uuid.UUID | None = None
    ) -> dict:
        try:
            variant_id = self.variants.resolve_variant_id(project_id, variant_id)
            zones = (
                self.db.query(ProjectZone)
                .options(joinedload(ProjectZone.material_assignments))
                .filter(ProjectZone.project_id == project_id)
                .all()
            )
            assignments = []
            for zone in zones:
                assignment = next(
                    (a for a in zone.material_assignments if a.variant_id == variant_id), None
                )
                if not assignment:
                    return {
                        "success": False,
                        "msg": f"No material assigned for zone: {zone.label}",
                        "data": None,
                    }
                material = get_material_by_id(assignment.material_id)
                if not material:
                    return {
                        "success": False,
                        "msg": f"Material not found: {assignment.material_id}",
                        "data": None,
                    }
                assignments.append(
                    {
                        "zone_id": str(zone.id),
                        "zone_key": zone.zone_key,
                        "zone_label": zone.label,
                        "material_id": material["id"],
                        "prompt_keyword": material["prompt_keyword"],
                    }
                )
            return {"success": True, "msg": "Assignments fetched", "data": assignments}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}
