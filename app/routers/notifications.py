"""Notifications router — lista, marca como leídas, cuenta no leídas."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[schemas.NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista las notificaciones del usuario actual."""
    query = db.query(models.Notification).filter(models.Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(models.Notification.is_read.is_(False))
    return query.order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Devuelve el contador de notificaciones no leídas."""
    count = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id, models.Notification.is_read.is_(False))
        .count()
    )
    return {"unread": count}


@router.put("/{notification_id}/read", response_model=schemas.NotificationResponse)
def mark_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Marca una notificación como leída."""
    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.put("/read-all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Marca todas las notificaciones del usuario como leídas."""
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read.is_(False),
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


# ─── Helper para crear notificaciones desde otros routers ───
def create_notification(db: Session, user_id, title: str, message: str, type: str = "info", related_id=None):
    """Crea una notificación para un usuario específico."""
    notif = models.Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        related_id=related_id,
    )
    db.add(notif)
    db.flush()
    return notif
