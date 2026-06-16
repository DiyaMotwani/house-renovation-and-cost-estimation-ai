import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Lightweight per-browser ownership: anonymous session token, no login.
    owner_token = Column(String(64), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="created")
    scale_factor = Column(Float, nullable=False, default=1.0)
    user_front_width_ft = Column(Float, nullable=True)
    approx_front_width_ft = Column(Float, nullable=True)
    num_floors = Column(Integer, nullable=True)
    house_description = Column(Text, nullable=True)
    renovation_needs = Column(JSON, nullable=True)
    renovation_suggestions = Column(JSON, nullable=True)
    style_hint = Column(String(100), nullable=True)
    dimension_hints = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)

    images = relationship("ProjectImage", back_populates="project", cascade="all, delete-orphan")
    zones = relationship("ProjectZone", back_populates="project", cascade="all, delete-orphan")
    estimations = relationship("ProjectEstimation", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("TaskRecord", back_populates="project", cascade="all, delete-orphan")
    report = relationship("RenovationReport", back_populates="project", uselist=False, cascade="all, delete-orphan")
    variants = relationship("DesignVariant", back_populates="project", cascade="all, delete-orphan")


class DesignVariant(Base):
    """A named design option: one set of zone->material choices + its own
    generated preview and estimate. A project can hold several to compare."""

    __tablename__ = "design_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False, default="Design 1")
    is_active = Column(Integer, nullable=False, default=1)  # 1 = currently selected variant
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="variants")


class ProjectImage(Base):
    __tablename__ = "project_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    # Generated previews belong to a specific design variant; original/sketch/mask leave this null.
    variant_id = Column(UUID(as_uuid=True), ForeignKey("design_variants.id", ondelete="CASCADE"), nullable=True)
    image_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(50), nullable=False)
    file_size_kb = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="images")


class ProjectZone(Base):
    __tablename__ = "project_zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    zone_key = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    estimated_sqft = Column(Float, nullable=True)
    box_2d = Column(JSON, nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="zones")
    # One assignment per design variant (was one-to-one before variants existed).
    material_assignments = relationship(
        "ZoneMaterialAssignment", back_populates="zone", cascade="all, delete-orphan"
    )
    estimations = relationship("ProjectEstimation", back_populates="zone", cascade="all, delete-orphan")


class ZoneMaterialAssignment(Base):
    __tablename__ = "zone_material_assignments"
    # One material per (variant, zone) — multiple variants can each assign the same zone.
    __table_args__ = (UniqueConstraint("variant_id", "zone_id", name="uq_variant_zone"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(
        UUID(as_uuid=True),
        ForeignKey("project_zones.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_id = Column(UUID(as_uuid=True), ForeignKey("design_variants.id", ondelete="CASCADE"), nullable=True)
    material_id = Column(String(100), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)

    zone = relationship("ProjectZone", back_populates="material_assignments")


class ProjectEstimation(Base):
    __tablename__ = "project_estimations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("design_variants.id", ondelete="CASCADE"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("project_zones.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(String(100), nullable=False)
    area_sqft = Column(Float, nullable=False)
    qty_required = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    material_cost_inr = Column(Float, nullable=False)
    labour_cost_inr = Column(Float, nullable=False)
    total_cost_inr = Column(Float, nullable=False)
    estimated_days = Column(Float, nullable=False)
    custom_unit_price_inr = Column(Float, nullable=True)
    custom_labour_rate_inr = Column(Float, nullable=True)
    dimension_anchor_used = Column(String(64), nullable=True)
    dimension_confidence = Column(Float, nullable=True)
    dimension_reasoning = Column(Text, nullable=True)
    calculated_at = Column(DateTime, server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="estimations")
    zone = relationship("ProjectZone", back_populates="estimations")


class TaskRecord(Base):
    __tablename__ = "task_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    celery_task_id = Column(String(255), nullable=False, unique=True)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)

    project = relationship("Project", back_populates="tasks")


class RenovationReport(Base):
    __tablename__ = "renovation_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    file_path = Column(String(500), nullable=False)
    grand_total_inr = Column(Float, nullable=False)
    total_days = Column(Float, nullable=False)
    generated_at = Column(DateTime, server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="report")
