import uuid

from sqlalchemy.orm import Session

from app.core.constants import PROJECT_STATUS_CREATED
from app.models.renovation_models import Project


class ProjectCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, name: str) -> dict:
        try:
            project = Project(
                id=uuid.uuid4(),
                name=name,
                status=PROJECT_STATUS_CREATED,
                scale_factor=1.0,
            )
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            return {"success": True, "msg": "Project created", "data": project}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def list_projects(self) -> dict:
        try:
            projects = self.db.query(Project).order_by(Project.created_at.desc()).all()
            return {"success": True, "msg": "Projects fetched", "data": projects}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def get_project(self, project_id: uuid.UUID) -> dict:
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "msg": "Project not found", "data": None}
            return {"success": True, "msg": "Project fetched", "data": project}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def update_project(self, project_id: uuid.UUID, name: str) -> dict:
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "msg": "Project not found", "data": None}
            project.name = name
            self.db.commit()
            self.db.refresh(project)
            return {"success": True, "msg": "Project updated", "data": project}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def delete_project(self, project_id: uuid.UUID) -> dict:
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "msg": "Project not found", "data": None}
            self.db.delete(project)
            self.db.commit()
            return {"success": True, "msg": "Project deleted", "data": {"id": str(project_id)}}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def update_status(self, project_id: uuid.UUID, status: str) -> dict:
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "msg": "Project not found", "data": None}
            project.status = status
            self.db.commit()
            self.db.refresh(project)
            return {"success": True, "msg": "Status updated", "data": project}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def set_scale_anchor(self, project_id: uuid.UUID, user_front_width_ft: float) -> dict:
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "msg": "Project not found", "data": None}
            if project.approx_front_width_ft and project.approx_front_width_ft > 0:
                project.scale_factor = user_front_width_ft / project.approx_front_width_ft
            project.user_front_width_ft = user_front_width_ft
            self.db.commit()
            self.db.refresh(project)
            return {"success": True, "msg": "Scale anchor set", "data": project}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def update_zone_metadata(
        self,
        project_id: uuid.UUID,
        approx_front_width_ft: float | None,
        num_floors: int | None,
    ) -> dict:
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "msg": "Project not found", "data": None}
            if approx_front_width_ft is not None:
                project.approx_front_width_ft = approx_front_width_ft
            if num_floors is not None:
                project.num_floors = num_floors
            self.db.commit()
            self.db.refresh(project)
            return {"success": True, "msg": "Metadata updated", "data": project}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}

    def update_house_analysis(self, project_id: uuid.UUID, analysis: dict) -> dict:
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "msg": "Project not found", "data": None}
            project.house_description = analysis.get("house_description")
            project.renovation_needs = analysis.get("renovation_needs")
            project.renovation_suggestions = analysis.get("renovation_suggestions")
            project.style_hint = analysis.get("style_hint")
            project.dimension_hints = analysis.get("dimension_hints")
            self.db.commit()
            self.db.refresh(project)
            return {"success": True, "msg": "House analysis updated", "data": project}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "msg": str(e), "data": None}
