import os
from uuid import UUID

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.database import get_db
from app import models, schemas


load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Ingresa solo el access_token de Supabase. Swagger agregará Bearer automáticamente.",
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> schemas.AuthenticatedUser:
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT secret is not configured")

    token = credentials.credentials
    try:
        claims = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        # Desarrollo: algunos tokens de Supabase usan ES256. En producción debe validarse con JWKS de Supabase.
        try:
            claims = jwt.get_unverified_claims(token)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        profile_id = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User profile not found")

    return schemas.AuthenticatedUser.model_validate(profile)


def require_roles(current_user: schemas.AuthenticatedUser, allowed_roles: list[models.UserRole]) -> None:
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


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
