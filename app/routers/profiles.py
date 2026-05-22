from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_roles
from app.database import get_db


router = APIRouter(prefix="/profiles", tags=["Profiles"])


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@router.post("/", response_model=schemas.ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_in: schemas.ProfileCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Crea un perfil de usuario. Solo administradores pueden crear perfiles."""
    require_roles(current_user, [models.UserRole.admin])

    existing = db.query(models.Profile).filter(models.Profile.email == profile_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email",
        )

    profile = models.Profile(
        email=profile_in.email,
        password=profile_in.password,
        full_name=profile_in.full_name,
        faculty=profile_in.faculty,
        skills=profile_in.skills,
        role=profile_in.role,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# ---------------------------------------------------------------------------
# READ – List
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[schemas.ProfileResponse])
def list_profiles(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista todos los perfiles. Disponible para todos los usuarios autenticados."""
    return db.query(models.Profile).offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# READ – Get by ID
# ---------------------------------------------------------------------------

@router.get("/{profile_id}", response_model=schemas.ProfileResponse)
def get_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Obtiene un perfil por su ID."""
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@router.put("/{profile_id}", response_model=schemas.ProfileResponse)
def update_profile(
    profile_id: UUID,
    profile_in: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Actualiza un perfil. Un usuario solo puede editar su propio perfil, a menos que sea admin."""
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    if current_user.role != models.UserRole.admin and current_user.id != profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/{profile_id}", response_model=schemas.MessageResponse)
def delete_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina un perfil. Solo administradores pueden eliminar perfiles."""
    require_roles(current_user, [models.UserRole.admin])

    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    db.delete(profile)
    db.commit()
    return {"message": "Profile deleted successfully"}
