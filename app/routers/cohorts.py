from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_roles
from app.database import get_db


router = APIRouter(prefix="/cohorts", tags=["Cohorts"])


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@router.post("/", response_model=schemas.CohortResponse, status_code=status.HTTP_201_CREATED)
def create_cohort(
    cohort_in: schemas.CohortCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Crea una nueva cohorte. Solo administradores pueden crear cohortes."""
    require_roles(current_user, [models.UserRole.admin])

    cohort = models.Cohort(
        name=cohort_in.name,
        description=cohort_in.description,
        start_date=cohort_in.start_date,
        end_date=cohort_in.end_date,
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)
    return cohort


# ---------------------------------------------------------------------------
# READ – List
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[schemas.CohortResponse])
def list_cohorts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista todas las cohortes."""
    return db.query(models.Cohort).offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# READ – Get by ID
# ---------------------------------------------------------------------------

@router.get("/{cohort_id}", response_model=schemas.CohortResponse)
def get_cohort(
    cohort_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Obtiene una cohorte por su ID."""
    cohort = db.query(models.Cohort).filter(models.Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")
    return cohort


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@router.put("/{cohort_id}", response_model=schemas.CohortResponse)
def update_cohort(
    cohort_id: UUID,
    cohort_in: schemas.CohortUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Actualiza una cohorte. Solo administradores pueden actualizar cohortes."""
    require_roles(current_user, [models.UserRole.admin])

    cohort = db.query(models.Cohort).filter(models.Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")

    update_data = cohort_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cohort, field, value)

    db.commit()
    db.refresh(cohort)
    return cohort


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/{cohort_id}", response_model=schemas.MessageResponse)
def delete_cohort(
    cohort_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina una cohorte. Solo administradores pueden eliminar cohortes."""
    require_roles(current_user, [models.UserRole.admin])

    cohort = db.query(models.Cohort).filter(models.Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")

    db.delete(cohort)
    db.commit()
    return {"message": "Cohort deleted successfully"}
