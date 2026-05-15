from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db


router = APIRouter(prefix="/cohorts", tags=["Cohorts"])


@router.get("/", response_model=list[schemas.CohortResponse])
def list_cohorts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    return db.query(models.Cohort).offset(skip).limit(limit).all()
