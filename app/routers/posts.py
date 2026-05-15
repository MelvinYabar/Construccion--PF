from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_roles
from app.database import get_db


router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=list[schemas.PostResponse])
def list_posts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(models.Post)
        .filter(models.Post.is_published.is_(True))
        .order_by(func.coalesce(models.Post.published_at, models.Post.created_at).desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_in: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
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
