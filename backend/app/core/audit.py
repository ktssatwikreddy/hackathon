"""Audit logging helper used by every write route."""
from fastapi import Request
from sqlalchemy.orm import Session

from app.models.core import AuditLog


def audit_log(
    db: Session,
    *,
    action: str,
    entity: str,
    entity_id: int | None = None,
    user_id: int | None = None,
    metadata: dict | None = None,
    request: Request | None = None,
) -> None:
    """Record a write action. Caller is responsible for commit().

    Added to the session but NOT committed here, so it participates in the
    same transaction as the action it describes.
    """
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            meta=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )
