from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_roles
from app.database import get_db


router = APIRouter(prefix="/phases", tags=["Phases"])


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@router.post("/", response_model=schemas.PhaseResponse, status_code=status.HTTP_201_CREATED)
def create_phase(
    phase_in: schemas.PhaseCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Crea una nueva fase. Solo administradores pueden crear fases."""
    require_roles(current_user, [models.UserRole.admin])

    existing = db.query(models.Phase).filter(models.Phase.order == phase_in.order).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A phase with this order already exists",
        )

    phase = models.Phase(name=phase_in.name, order=phase_in.order)
    db.add(phase)
    db.commit()
    db.refresh(phase)
    return phase


# ---------------------------------------------------------------------------
# READ – List
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[schemas.PhaseResponse])
def list_phases(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista todas las fases ordenadas por el campo order."""
    return (
        db.query(models.Phase)
        .order_by(models.Phase.order.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# READ – Get by ID
# ---------------------------------------------------------------------------

@router.get("/{phase_id}", response_model=schemas.PhaseResponse)
def get_phase(
    phase_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Obtiene una fase por su ID."""
    phase = db.query(models.Phase).filter(models.Phase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")
    return phase


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@router.put("/{phase_id}", response_model=schemas.PhaseResponse)
def update_phase(
    phase_id: int,
    phase_in: schemas.PhaseUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Actualiza una fase. Solo administradores pueden actualizar fases."""
    require_roles(current_user, [models.UserRole.admin])

    phase = db.query(models.Phase).filter(models.Phase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")

    update_data = phase_in.model_dump(exclude_unset=True)

    if "order" in update_data and update_data["order"] != phase.order:
        existing = db.query(models.Phase).filter(models.Phase.order == update_data["order"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A phase with this order already exists",
            )

    for field, value in update_data.items():
        setattr(phase, field, value)

    db.commit()
    db.refresh(phase)
    return phase


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/{phase_id}", response_model=schemas.MessageResponse)
def delete_phase(
    phase_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina una fase. Solo administradores pueden eliminar fases."""
    require_roles(current_user, [models.UserRole.admin])

    phase = db.query(models.Phase).filter(models.Phase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")

    db.delete(phase)
    db.commit()
    return {"message": "Phase deleted successfully"}
