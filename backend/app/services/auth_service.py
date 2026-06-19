import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.core import User

logger = logging.getLogger("tapms.auth")


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def issue_tokens(user: User) -> tuple[str, str]:
    claims = {"role": user.role.value}
    access = create_access_token(str(user.id), claims)
    refresh = create_refresh_token(str(user.id))
    return access, refresh


def send_password_reset(user: User | None, email: str) -> None:
    """Stub email delivery — logs a reset token to the console.

    Always succeeds regardless of whether the email exists, so we never leak
    which addresses are registered.
    """
    if user is None:
        logger.info("Password reset requested for unknown email %s — ignoring.", email)
        return
    from app.core.security import _create_token  # local import to avoid cycle
    from datetime import timedelta

    reset_token = _create_token(str(user.id), "access", timedelta(minutes=30), {"scope": "reset"})
    logger.info(
        "[PASSWORD RESET] Email to %s: use this token to reset your password:\n%s",
        email,
        reset_token,
    )


def reset_password(db: Session, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    db.add(user)
