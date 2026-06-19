from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, decode_token
from app.models.core import User
from app.schemas.auth import (
    AccessToken,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.schemas.base import Message
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair, summary="Authenticate and receive tokens")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    user = auth_service.authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    access, refresh = auth_service.issue_tokens(user)
    audit_log(db, action="login", entity="user", entity_id=user.id, user_id=user.id, request=request)
    db.commit()
    return TokenPair(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=AccessToken, summary="Exchange a refresh token for a new access token")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AccessToken:
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )
    user = db.get(User, int(claims["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    access = create_access_token(str(user.id), {"role": user.role.value})
    return AccessToken(access_token=access)


@router.post("/logout", response_model=Message, summary="Log out (client discards tokens)")
def logout(current_user: User = Depends(get_current_user)) -> Message:
    # Stateless JWT: logout is a client-side token discard. Endpoint exists for symmetry.
    return Message(message="Logged out. Discard your tokens client-side.")


@router.post("/forgot-password", response_model=Message, summary="Request a password reset email (stub)")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> Message:
    user = db.scalar(select(User).where(User.email == payload.email))
    auth_service.send_password_reset(user, payload.email)
    return Message(message="If that email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=Message, summary="Reset password using a reset token")
def reset_password(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)) -> Message:
    try:
        claims = decode_token(payload.token, expected_type="access")
        if claims.get("scope") != "reset":
            raise JWTError("Not a reset token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user = db.get(User, int(claims["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")
    auth_service.reset_password(db, user, payload.new_password)
    audit_log(db, action="reset_password", entity="user", entity_id=user.id, user_id=user.id, request=request)
    db.commit()
    return Message(message="Password updated. You can now log in.")


@router.get("/me", response_model=UserOut, summary="Get the current authenticated user")
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
