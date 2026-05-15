from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_roles
from app.database import get_db


router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post("/", response_model=schemas.EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    enrollment_in: schemas.EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    require_roles(current_user, [models.UserRole.emprendedor])

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


@router.patch("/{enrollment_id}/status", response_model=schemas.EnrollmentResponse)
def update_enrollment_status(
    enrollment_id: UUID,
    status_in: schemas.EnrollmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
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
