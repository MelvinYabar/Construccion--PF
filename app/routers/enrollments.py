from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_roles
from app.database import get_db


router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@router.post("/", response_model=schemas.EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    enrollment_in: schemas.EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Un emprendedor se inscribe en una cohorte. Admin tambien puede probar el endpoint."""
    require_roles(current_user, [models.UserRole.admin, models.UserRole.emprendedor])

    cohort = db.query(models.Cohort).filter(models.Cohort.id == enrollment_in.cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")

    existing = (
        db.query(models.Enrollment)
        .filter(
            models.Enrollment.user_id == current_user.id,
            models.Enrollment.cohort_id == enrollment_in.cohort_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already enrolled in this cohort")

    enrollment = models.Enrollment(
        user_id=current_user.id,
        cohort_id=enrollment_in.cohort_id,
        status=models.EnrollmentStatus.pendiente,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


# ---------------------------------------------------------------------------
# READ – List
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[schemas.EnrollmentResponse])
def list_enrollments(
    skip: int = 0,
    limit: int = 20,
    cohort_id: UUID | None = None,
    user_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista inscripciones. Se puede filtrar por cohort_id y user_id. Solo administradores ven todas."""
    query = db.query(models.Enrollment)

    if current_user.role == models.UserRole.emprendedor:
        query = query.filter(models.Enrollment.user_id == current_user.id)
    elif current_user.role == models.UserRole.mentor:
        # Los mentores solo ven inscripciones de las cohortes donde tienen proyectos asignados
        query = query.join(models.Cohort).join(models.Project).join(models.ProjectMentor).filter(
            models.ProjectMentor.mentor_id == current_user.id
        )

    if cohort_id:
        query = query.filter(models.Enrollment.cohort_id == cohort_id)
    if user_id and current_user.role == models.UserRole.admin:
        query = query.filter(models.Enrollment.user_id == user_id)

    return query.offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# READ – Get by ID
# ---------------------------------------------------------------------------

@router.get("/{enrollment_id}", response_model=schemas.EnrollmentResponse)
def get_enrollment(
    enrollment_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Obtiene una inscripción por su ID."""
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    if current_user.role == models.UserRole.emprendedor and enrollment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return enrollment


# ---------------------------------------------------------------------------
# UPDATE – Cambiar estado
# ---------------------------------------------------------------------------

@router.put("/{enrollment_id}/status", response_model=schemas.EnrollmentResponse)
def update_enrollment_status(
    enrollment_id: UUID,
    status_in: schemas.EnrollmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Actualiza el estado de una inscripción (aceptar/rechazar). Solo administradores."""
    require_roles(current_user, [models.UserRole.admin])

    if status_in.status not in [models.EnrollmentStatus.aceptada, models.EnrollmentStatus.rechazada]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be aceptada or rechazada")

    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    enrollment.status = status_in.status
    db.commit()
    db.refresh(enrollment)
    return enrollment


# ---------------------------------------------------------------------------
# UPDATE – General
# ---------------------------------------------------------------------------

@router.put("/{enrollment_id}", response_model=schemas.EnrollmentResponse)
def update_enrollment(
    enrollment_id: UUID,
    enrollment_in: schemas.EnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Actualiza campos de una inscripción. Solo administradores."""
    require_roles(current_user, [models.UserRole.admin])

    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    update_data = enrollment_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(enrollment, field, value)

    db.commit()
    db.refresh(enrollment)
    return enrollment


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/{enrollment_id}", response_model=schemas.MessageResponse)
def delete_enrollment(
    enrollment_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina una inscripción. Solo administradores pueden eliminar inscripciones."""
    require_roles(current_user, [models.UserRole.admin])

    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    db.delete(enrollment)
    db.commit()
    return {"message": "Enrollment deleted successfully"}
