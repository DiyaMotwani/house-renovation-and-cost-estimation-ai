import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.renovation_models import (
    DesignVariant,
    ProjectEstimation,
    ProjectImage,
    ProjectZone,
    ZoneMaterialAssignment,
)


class VariantCRUD:
    def __init__(self, db: Session):
        self.db = db

    # ----- internal helpers -------------------------------------------------

    def _backfill_legacy(self, project_id: uuid.UUID, variant_id: uuid.UUID) -> None:
        """Attach pre-variant rows (created before this feature) to the default
        variant so existing projects keep their materials/estimate/preview."""
        zone_ids = [
            z.id for z in self.db.query(ProjectZone.id).filter(ProjectZone.project_id == project_id).all()
        ]
        if zone_ids:
            self.db.execute(
                update(ZoneMaterialAssignment)
                .where(
                    ZoneMaterialAssignment.zone_id.in_(zone_ids),
                    ZoneMaterialAssignment.variant_id.is_(None),
                )
                .values(variant_id=variant_id)
            )
        self.db.execute(
            update(ProjectEstimation)
            .where(ProjectEstimation.project_id == project_id, ProjectEstimation.variant_id.is_(None))
            .values(variant_id=variant_id)
        )
        self.db.execute(
            update(ProjectImage)
            .where(
                ProjectImage.project_id == project_id,
                ProjectImage.image_type == "generated",
                ProjectImage.variant_id.is_(None),
            )
            .values(variant_id=variant_id)
        )

    def get_or_create_active_variant(self, project_id: uuid.UUID) -> DesignVariant:
        active = (
            self.db.query(DesignVariant)
            .filter(DesignVariant.project_id == project_id, DesignVariant.is_active == 1)
            .first()
        )
        if active:
            return active

        any_variant = (
            self.db.query(DesignVariant)
            .filter(DesignVariant.project_id == project_id)
            .order_by(DesignVariant.created_at)
            .first()
        )
        if any_variant:
            any_variant.is_active = 1
            self.db.commit()
            return any_variant

        variant = DesignVariant(id=uuid.uuid4(), project_id=project_id, name="Design 1", is_active=1)
        self.db.add(variant)
        self.db.flush()
        self._backfill_legacy(project_id, variant.id)
        self.db.commit()
        self.db.refresh(variant)
        return variant

    # ----- public API -------------------------------------------------------

    def list_variants(self, project_id: uuid.UUID) -> dict:
        try:
            self.get_or_create_active_variant(project_id)
            variants = (
                self.db.query(DesignVariant)
                .filter(DesignVariant.project_id == project_id)
                .order_by(DesignVariant.created_at)
                .all()
            )
            return {"success": True, "msg": "Variants fetched", "data": variants}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def create_variant(self, project_id: uuid.UUID, name: str | None, copy_from_active: bool = True) -> dict:
        try:
            source = self.get_or_create_active_variant(project_id) if copy_from_active else None
            count = self.db.query(DesignVariant).filter(DesignVariant.project_id == project_id).count()
            variant = DesignVariant(
                id=uuid.uuid4(),
                project_id=project_id,
                name=name or f"Design {count + 1}",
                is_active=0,
            )
            self.db.add(variant)
            self.db.flush()

            # Seed the new variant with the active variant's material choices so
            # the user starts from the current design and tweaks one section.
            if source:
                src_assignments = (
                    self.db.query(ZoneMaterialAssignment)
                    .filter(ZoneMaterialAssignment.variant_id == source.id)
                    .all()
                )
                for a in src_assignments:
                    self.db.add(
                        ZoneMaterialAssignment(
                            id=uuid.uuid4(), zone_id=a.zone_id, variant_id=variant.id, material_id=a.material_id
                        )
                    )
            self.db.commit()
            self.db.refresh(variant)
            return {"success": True, "msg": "Variant created", "data": variant}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def activate_variant(self, project_id: uuid.UUID, variant_id: uuid.UUID) -> dict:
        try:
            target = (
                self.db.query(DesignVariant)
                .filter(DesignVariant.id == variant_id, DesignVariant.project_id == project_id)
                .first()
            )
            if not target:
                return {"success": False, "msg": "Variant not found", "data": None}
            self.db.execute(
                update(DesignVariant)
                .where(DesignVariant.project_id == project_id)
                .values(is_active=0)
            )
            target.is_active = 1
            self.db.commit()
            self.db.refresh(target)
            return {"success": True, "msg": "Variant activated", "data": target}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def rename_variant(self, project_id: uuid.UUID, variant_id: uuid.UUID, name: str) -> dict:
        try:
            variant = (
                self.db.query(DesignVariant)
                .filter(DesignVariant.id == variant_id, DesignVariant.project_id == project_id)
                .first()
            )
            if not variant:
                return {"success": False, "msg": "Variant not found", "data": None}
            variant.name = name
            self.db.commit()
            self.db.refresh(variant)
            return {"success": True, "msg": "Variant renamed", "data": variant}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def delete_variant(self, project_id: uuid.UUID, variant_id: uuid.UUID) -> dict:
        try:
            count = self.db.query(DesignVariant).filter(DesignVariant.project_id == project_id).count()
            if count <= 1:
                return {"success": False, "msg": "Cannot delete the only design variant", "data": None}
            variant = (
                self.db.query(DesignVariant)
                .filter(DesignVariant.id == variant_id, DesignVariant.project_id == project_id)
                .first()
            )
            if not variant:
                return {"success": False, "msg": "Variant not found", "data": None}
            was_active = variant.is_active
            self.db.delete(variant)
            self.db.commit()
            if was_active:
                self.get_or_create_active_variant(project_id)
            return {"success": True, "msg": "Variant deleted", "data": {"id": str(variant_id)}}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def resolve_variant_id(self, project_id: uuid.UUID, variant_id) -> uuid.UUID:
        """Return the requested variant (coerced to UUID) if valid, else the active one."""
        if variant_id:
            try:
                vid = variant_id if isinstance(variant_id, uuid.UUID) else uuid.UUID(str(variant_id))
            except (ValueError, TypeError, AttributeError):
                vid = None
            if vid:
                exists = (
                    self.db.query(DesignVariant.id)
                    .filter(DesignVariant.id == vid, DesignVariant.project_id == project_id)
                    .first()
                )
                if exists:
                    return vid
        return self.get_or_create_active_variant(project_id).id
