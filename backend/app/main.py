import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import models  # noqa: F401  (ensures models are registered on Base)
from app.core.config import get_settings
from app.core.database import Base, engine
from app.routers import (
    assessments,
    attendance,
    auth,
    departments,
    sessions,
    trainings,
    users,
)

settings = get_settings()
logger = logging.getLogger("tapms")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Centralized training attendance, assessment, and AI performance management API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers are mounted here as each phase adds them.
app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(users.router)
app.include_router(trainings.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(assessments.router)


@app.on_event("startup")
def create_tables() -> None:
    """Local dev convenience: ensure tables exist on boot.

    Alembic migrations are the source of truth for schema (see alembic/).
    """
    if settings.environment == "local":
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables are ready.")
        except SQLAlchemyError as exc:
            logger.warning("Could not initialise database tables: %s", exc)


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    database_status = "unavailable"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "connected"
    except SQLAlchemyError:
        database_status = "unavailable"
    return {
        "status": "ok",
        "database": database_status,
        "ai_mode": "mock" if settings.mock_ai else "groq",
    }
