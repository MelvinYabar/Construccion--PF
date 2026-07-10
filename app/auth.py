import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.database import get_db
from app import models, schemas


load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required. Set it in your .env file.")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Ingresa el JWT obtenido de /auth/login.",
)


# ---------------------------------------------------------------------------
# JWT creation
# ---------------------------------------------------------------------------

def create_access_token(user_id: UUID, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# JWT validation
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> schemas.AuthenticatedUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )

    try:
        profile_id = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        ) from None

    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    return schemas.AuthenticatedUser.model_validate(profile)


# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------

def require_roles(current_user: schemas.AuthenticatedUser, allowed_roles: list[models.UserRole]) -> None:
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")


def is_admin(current_user: schemas.AuthenticatedUser) -> bool:
    return current_user.role == models.UserRole.admin


def is_project_member(db: Session, project_id, user_id) -> bool:
    return (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.project_id == project_id, models.ProjectMember.user_id == user_id)
        .first()
        is not None
    )


def is_project_mentor(db: Session, project_id, user_id) -> bool:
    return (
        db.query(models.ProjectMentor)
        .filter(models.ProjectMentor.project_id == project_id, models.ProjectMentor.mentor_id == user_id)
        .first()
        is not None
    )


def can_access_project(db: Session, project_id, current_user: schemas.AuthenticatedUser) -> bool:
    if current_user.role == models.UserRole.admin:
        return True
    if current_user.role == models.UserRole.emprendedor:
        return is_project_member(db, project_id, current_user.id)
    if current_user.role == models.UserRole.mentor:
        return is_project_mentor(db, project_id, current_user.id)
    return False
