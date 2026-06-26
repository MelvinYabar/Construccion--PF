from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import can_access_project, get_current_user, is_admin, is_project_member, is_project_mentor, require_roles
from app.database import get_db


router = APIRouter(tags=["Deliverables & Reviews"])


def get_project_or_404(db: Session, project_id: UUID) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def get_deliverable_or_404(db: Session, deliverable_id: UUID) -> models.Deliverable:
    deliverable = db.query(models.Deliverable).filter(models.Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
    return deliverable


# ===========================================================================
# DELIVERABLES CRUD
# ===========================================================================

# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/deliverables",
    response_model=schemas.DeliverableResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deliverable(
    project_id: UUID,
    deliverable_in: schemas.DeliverableCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Sube un entregable a un proyecto. Solo miembros del proyecto pueden subir entregables."""
    get_project_or_404(db, project_id)

    phase = db.query(models.Phase).filter(models.Phase.id == deliverable_in.phase_id).first()
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")

    if not is_admin(current_user) and not is_project_member(db, project_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo miembros del proyecto o admin pueden subir entregables")

    deliverable = models.Deliverable(
        project_id=project_id,
        phase_id=deliverable_in.phase_id,
        uploaded_by=current_user.id,
        file_url=deliverable_in.file_url,
    )
    db.add(deliverable)
    db.commit()
    db.refresh(deliverable)
    return deliverable


# ---------------------------------------------------------------------------
# READ – List by project
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/deliverables", response_model=list[schemas.DeliverableWithReviewResponse])
def list_deliverables(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista los entregables de un proyecto con su última revisión."""
    get_project_or_404(db, project_id)
    if not can_access_project(db, project_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project access denied")

    deliverables = (
        db.query(models.Deliverable)
        .filter(models.Deliverable.project_id == project_id)
        .order_by(models.Deliverable.created_at.desc())
        .all()
    )

    response = []
    for deliverable in deliverables:
        review = (
            db.query(models.DeliverableReview)
            .filter(models.DeliverableReview.deliverable_id == deliverable.id)
            .order_by(models.DeliverableReview.reviewed_at.desc())
            .first()
        )
        response.append(
            schemas.DeliverableWithReviewResponse(
                id=deliverable.id,
                project_id=deliverable.project_id,
                phase_id=deliverable.phase_id,
                uploaded_by=deliverable.uploaded_by,
                file_url=deliverable.file_url,
                created_at=deliverable.created_at,
                review=review,
            )
        )
    return response


# ---------------------------------------------------------------------------
# READ – Get by ID
# ---------------------------------------------------------------------------

@router.get("/deliverables/{deliverable_id}", response_model=schemas.DeliverableWithReviewResponse)
def get_deliverable(
    deliverable_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Obtiene un entregable por su ID con su última revisión."""
    deliverable = get_deliverable_or_404(db, deliverable_id)

    if not can_access_project(db, deliverable.project_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project access denied")

    review = (
        db.query(models.DeliverableReview)
        .filter(models.DeliverableReview.deliverable_id == deliverable.id)
        .order_by(models.DeliverableReview.reviewed_at.desc())
        .first()
    )

    return schemas.DeliverableWithReviewResponse(
        id=deliverable.id,
        project_id=deliverable.project_id,
        phase_id=deliverable.phase_id,
        uploaded_by=deliverable.uploaded_by,
        file_url=deliverable.file_url,
        created_at=deliverable.created_at,
        review=review,
    )


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@router.put("/deliverables/{deliverable_id}", response_model=schemas.DeliverableResponse)
def update_deliverable(
    deliverable_id: UUID,
    deliverable_in: schemas.DeliverableUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Actualiza un entregable. Solo el miembro que lo subió o un admin pueden editarlo."""
    deliverable = get_deliverable_or_404(db, deliverable_id)

    if not is_admin(current_user) and deliverable.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo quien subio el entregable o admin pueden actualizarlo",
        )

    update_data = deliverable_in.model_dump(exclude_unset=True)

    if "phase_id" in update_data:
        phase = db.query(models.Phase).filter(models.Phase.id == update_data["phase_id"]).first()
        if not phase:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")

    for field, value in update_data.items():
        setattr(deliverable, field, value)

    db.commit()
    db.refresh(deliverable)
    return deliverable


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/deliverables/{deliverable_id}", response_model=schemas.MessageResponse)
def delete_deliverable(
    deliverable_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina un entregable. Solo el miembro que lo subió o un admin pueden eliminarlo."""
    deliverable = get_deliverable_or_404(db, deliverable_id)

    if not is_admin(current_user) and deliverable.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo quien subio el entregable o admin pueden eliminarlo",
        )

    db.delete(deliverable)
    db.commit()
    return {"message": "Deliverable deleted successfully"}


# ===========================================================================
# DELIVERABLE REVIEWS CRUD
# ===========================================================================

# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@router.post(
    "/deliverables/{deliverable_id}/reviews",
    response_model=schemas.DeliverableReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deliverable_review(
    deliverable_id: UUID,
    review_in: schemas.DeliverableReviewCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Crea una revisión de entregable. Solo mentores pueden revisar. Si se aprueba, avanza la fase automáticamente."""
    require_roles(current_user, [models.UserRole.admin, models.UserRole.mentor])

    if review_in.status not in [models.ReviewStatus.aprobado, models.ReviewStatus.rechazado]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be aprobado or rechazado")

    deliverable = db.query(models.Deliverable).filter(models.Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")

    if not is_admin(current_user) and not is_project_mentor(db, deliverable.project_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mentor is not assigned to this project")

    review = models.DeliverableReview(
        deliverable_id=deliverable_id,
        mentor_id=current_user.id,
        status=review_in.status,
        feedback=review_in.feedback,
    )

    try:
        db.add(review)

        if review_in.status == models.ReviewStatus.aprobado:
            project = deliverable.project
            base_phase = project.current_phase or deliverable.phase
            if base_phase:
                next_phase = (
                    db.query(models.Phase)
                    .filter(models.Phase.order > base_phase.order)
                    .order_by(models.Phase.order.asc())
                    .first()
                )
                if next_phase:
                    project.current_phase_id = next_phase.id

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(review)
    return review


# ---------------------------------------------------------------------------
# READ – List reviews for a deliverable
# ---------------------------------------------------------------------------

@router.get("/deliverables/{deliverable_id}/reviews", response_model=list[schemas.DeliverableReviewResponse])
def list_deliverable_reviews(
    deliverable_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista todas las revisiones de un entregable."""
    deliverable = get_deliverable_or_404(db, deliverable_id)

    if not can_access_project(db, deliverable.project_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project access denied")

    reviews = (
        db.query(models.DeliverableReview)
        .filter(models.DeliverableReview.deliverable_id == deliverable_id)
        .order_by(models.DeliverableReview.reviewed_at.desc())
        .all()
    )
    return reviews


# ---------------------------------------------------------------------------
# READ – Get review by ID
# ---------------------------------------------------------------------------

@router.get("/reviews/{review_id}", response_model=schemas.DeliverableReviewResponse)
def get_review(
    review_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Obtiene una revisión por su ID."""
    review = db.query(models.DeliverableReview).filter(models.DeliverableReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    deliverable = db.query(models.Deliverable).filter(models.Deliverable.id == review.deliverable_id).first()
    if deliverable and not can_access_project(db, deliverable.project_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return review


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@router.put("/reviews/{review_id}", response_model=schemas.DeliverableReviewResponse)
def update_review(
    review_id: UUID,
    review_in: schemas.DeliverableReviewUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Actualiza una revisión. Solo el mentor que la creó o un admin pueden editarla."""
    review = db.query(models.DeliverableReview).filter(models.DeliverableReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if not is_admin(current_user) and review.mentor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el mentor que reviso o admin pueden actualizar esta revision",
        )

    update_data = review_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)
    return review


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/reviews/{review_id}", response_model=schemas.MessageResponse)
def delete_review(
    review_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina una revisión. Solo administradores pueden eliminar revisiones."""
    require_roles(current_user, [models.UserRole.admin])

    review = db.query(models.DeliverableReview).filter(models.DeliverableReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    db.delete(review)
    db.commit()
    return {"message": "Review deleted successfully"}
