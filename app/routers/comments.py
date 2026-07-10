"""Comments router para entregables — chat entre emprendedor y mentor."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, is_admin, is_project_member, is_project_mentor, can_access_project
from app.database import get_db

router = APIRouter(tags=["Comments"])


@router.get("/deliverables/{deliverable_id}/comments", response_model=list[schemas.CommentResponse])
def list_comments(
    deliverable_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista los comentarios de un entregable."""
    deliverable = db.query(models.Deliverable).filter(models.Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
    if not can_access_project(db, deliverable.project_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    comments = (
        db.query(models.DeliverableComment)
        .filter(models.DeliverableComment.deliverable_id == deliverable_id)
        .order_by(models.DeliverableComment.created_at.asc())
        .all()
    )
    result = []
    for c in comments:
        result.append(schemas.CommentResponse(
            id=c.id,
            deliverable_id=c.deliverable_id,
            author_id=c.author_id,
            author_name=c.author.full_name if c.author else None,
            author_role=c.author.role.value if c.author and c.author.role else None,
            content=c.content,
            created_at=c.created_at,
        ))
    return result


@router.post("/deliverables/{deliverable_id}/comments", response_model=schemas.CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    deliverable_id: UUID,
    comment_in: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Crea un comentario en un entregable."""
    deliverable = db.query(models.Deliverable).filter(models.Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
    if not can_access_project(db, deliverable.project_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    comment = models.DeliverableComment(
        deliverable_id=deliverable_id,
        author_id=current_user.id,
        content=comment_in.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Notificar a la otra parte
    project = deliverable.project
    if project:
        if current_user.role == models.UserRole.mentor:
            # Notificar a los miembros del proyecto
            from app.routers.notifications import create_notification
            members = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project.id).all()
            for m in members:
                create_notification(db, m.user_id, "Nuevo comentario", f"El mentor comentó en el entregable de {deliverable.phase.name if deliverable.phase else 'una fase'}.", "deliverable", deliverable.id)
            db.commit()
        else:
            # Notificar a los mentores del proyecto
            from app.routers.notifications import create_notification
            mentors = db.query(models.ProjectMentor).filter(models.ProjectMentor.project_id == project.id).all()
            for m in mentors:
                create_notification(db, m.mentor_id, "Nuevo comentario", f"El emprendedor comentó en el entregable de {deliverable.phase.name if deliverable.phase else 'una fase'}.", "deliverable", deliverable.id)
            db.commit()

    return schemas.CommentResponse(
        id=comment.id,
        deliverable_id=comment.deliverable_id,
        author_id=comment.author_id,
        author_name=comment.author.full_name if comment.author else None,
        author_role=comment.author.role.value if comment.author and comment.author.role else None,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina un comentario. Solo el autor o admin."""
    comment = db.query(models.DeliverableComment).filter(models.DeliverableComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.author_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author or admin can delete")
    db.delete(comment)
    db.commit()
