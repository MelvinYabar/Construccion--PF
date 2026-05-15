from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import can_access_project, get_current_user, is_project_member, is_project_mentor, require_roles
from app.database import get_db


router = APIRouter(tags=["Deliverables"])


def get_project_or_404(db: Session, project_id: UUID) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


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
    get_project_or_404(db, project_id)

    phase = db.query(models.Phase).filter(models.Phase.id == deliverable_in.phase_id).first()
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")

    if not is_project_member(db, project_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only project members can upload deliverables")

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


@router.get("/projects/{project_id}/deliverables", response_model=list[schemas.DeliverableWithReviewResponse])
def list_deliverables(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
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
    require_roles(current_user, [models.UserRole.mentor])

    if review_in.status not in [models.ReviewStatus.aprobado, models.ReviewStatus.rechazado]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be aprobado or rechazado")

    deliverable = db.query(models.Deliverable).filter(models.Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")

    if not is_project_mentor(db, deliverable.project_id, current_user.id):
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
