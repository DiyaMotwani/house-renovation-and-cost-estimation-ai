"""Shared FastAPI dependencies — lightweight anonymous ownership.

There is no login. The frontend generates a random token per browser and sends
it as the `X-Owner-Token` header. Projects are scoped to that token so users do
not see or mutate each other's work. Legacy projects (token NULL) stay open for
backward compatibility.
"""

from uuid import UUID

from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.renovation_models import Project


def get_owner_token(x_owner_token: str | None = Header(default=None)) -> str | None:
    return x_owner_token


def verify_project_owner(
    project_id: UUID,
    x_owner_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> None:
    """Guard sub-resource routers: the caller must own the project.

    The token normally arrives in the X-Owner-Token header. For direct browser
    navigations (e.g. opening the PDF download URL in a new tab) the header
    cannot be set, so a `?token=` query param is accepted as a fallback.
    """
    effective_token = x_owner_token or token
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_token and project.owner_token != effective_token:
        raise HTTPException(status_code=403, detail="You do not have access to this project")
