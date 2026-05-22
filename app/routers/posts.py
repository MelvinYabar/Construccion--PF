from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_roles
from app.database import get_db


router = APIRouter(prefix="/posts", tags=["Posts"])


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@router.post("/", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_in: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Crea una nueva publicación. Solo administradores y mentores pueden crear posts."""
    require_roles(current_user, [models.UserRole.admin, models.UserRole.mentor])

    post = models.Post(
        author_id=current_user.id,
        title=post_in.title,
        content=post_in.content,
        image_url=post_in.image_url,
        is_published=post_in.is_published,
        published_at=datetime.now(timezone.utc) if post_in.is_published else None,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


# ---------------------------------------------------------------------------
# READ – List
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[schemas.PostResponse])
def list_posts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista publicaciones. Usuarios autenticados ven solo las publicadas; admins ven todas."""
    query = db.query(models.Post)

    if current_user.role != models.UserRole.admin:
        query = query.filter(models.Post.is_published.is_(True))

    return (
        query.order_by(func.coalesce(models.Post.published_at, models.Post.created_at).desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# READ – Get by ID
# ---------------------------------------------------------------------------

@router.get("/{post_id}", response_model=schemas.PostResponse)
def get_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Obtiene una publicación por su ID."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if not post.is_published and current_user.role != models.UserRole.admin and post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    return post


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@router.put("/{post_id}", response_model=schemas.PostResponse)
def update_post(
    post_id: UUID,
    post_in: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Actualiza una publicación. Solo el autor o un administrador pueden editarla."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if current_user.role != models.UserRole.admin and post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author or an admin can update this post",
        )

    update_data = post_in.model_dump(exclude_unset=True)

    # Si se está publicando por primera vez, establecer published_at
    if update_data.get("is_published") is True and not post.is_published and not post.published_at:
        update_data["published_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/{post_id}", response_model=schemas.MessageResponse)
def delete_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina una publicación. Solo el autor o un administrador pueden eliminarla."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if current_user.role != models.UserRole.admin and post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author or an admin can delete this post",
        )

    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}
