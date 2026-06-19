from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import User, UserRole
from app.schemas.base import ORMModel
from app.services import material_service

router = APIRouter(prefix="/api", tags=["materials"])

staff_only = require_roles(UserRole.super_admin, UserRole.trainer)


class MaterialOut(ORMModel):
    id: int
    session_id: int
    title: str
    filename: str
    content_type: str | None
    uploaded_by: int
    created_at: datetime


@router.post(
    "/sessions/{session_id}/materials",
    response_model=MaterialOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file/resource to a session (staff)",
)
async def upload_material(
    session_id: int,
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    data = await file.read()
    material = material_service.add_material(
        db, session_id, title, file.filename or "file", file.content_type, data, current_user
    )
    audit_log(db, action="upload_material", entity="session", entity_id=session_id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(material)
    return material


@router.get(
    "/sessions/{session_id}/materials",
    response_model=list[MaterialOut],
    summary="List a session's materials (enrolled users or staff)",
)
def list_materials(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return material_service.list_materials(db, session_id, current_user)


@router.get("/materials/{material_id}/download", summary="Download a session material")
def download_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material = material_service.get_material_for_download(db, material_id, current_user)
    return FileResponse(
        material.stored_path,
        filename=material.filename,
        media_type=material.content_type or "application/octet-stream",
    )
