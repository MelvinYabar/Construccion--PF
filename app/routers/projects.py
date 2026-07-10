from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import can_access_project, get_current_user, is_admin, is_project_member, is_project_mentor, require_roles
from app.database import get_db


router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_or_404(db: Session, project_id: UUID) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


# ---------------------------------------------------------------------------
# MY STATS — debe ir ANTES de las rutas con {project_id} para que FastAPI
# no interprete "my-stats" como un UUID
# ---------------------------------------------------------------------------

@router.get("/my-stats", response_model=schemas.EntrepreneurStats)
def get_my_stats(
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Estadísticas del emprendedor: proyecto, fase, entregables, inscripciones."""
    project = db.query(models.Project).filter(models.Project.leader_id == current_user.id).first()

    total_phases = db.query(models.Phase).count() or 1
    current_order = 0
    current_phase_name = None
    project_name = None

    if project:
        project_name = project.name
        if project.current_phase:
            current_phase_name = project.current_phase.name
            current_order = project.current_phase.order or 0

    progress = min(100.0, round((current_order / total_phases) * 100, 1))

    deliverables_uploaded = 0
    deliverables_approved = 0
    if project:
        deliverables_uploaded = db.query(models.Deliverable).filter(models.Deliverable.project_id == project.id).count()
        deliverables_approved = (
            db.query(models.DeliverableReview)
            .join(models.Deliverable)
            .filter(models.Deliverable.project_id == project.id, models.DeliverableReview.status == models.ReviewStatus.aprobado)
            .count()
        )

    enrollments_total = db.query(models.Enrollment).filter(models.Enrollment.user_id == current_user.id).count()
    enrollments_accepted = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id, models.Enrollment.status == models.EnrollmentStatus.aceptada
    ).count()

    return schemas.EntrepreneurStats(
        project_name=project_name,
        current_phase=current_phase_name,
        total_phases=total_phases,
        current_phase_order=current_order,
        progress_percentage=progress,
        deliverables_uploaded=deliverables_uploaded,
        deliverables_approved=deliverables_approved,
        deliverables_pending=deliverables_uploaded - deliverables_approved,
        enrollments_total=enrollments_total,
        enrollments_accepted=enrollments_accepted,
    )


# ===========================================================================
# PROJECTS CRUD
# ===========================================================================

# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@router.post("/", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Crea un nuevo proyecto. Emprendedores crean sus proyectos; admin tambien puede hacerlo."""
    require_roles(current_user, [models.UserRole.admin, models.UserRole.emprendedor])

    if project_in.cohort_id:
        cohort = db.query(models.Cohort).filter(models.Cohort.id == project_in.cohort_id).first()
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")

    first_phase = db.query(models.Phase).order_by(models.Phase.order.asc()).first()
    project = models.Project(
        name=project_in.name,
        description=project_in.description,
        cohort_id=project_in.cohort_id,
        leader_id=current_user.id,
        current_phase_id=first_phase.id if first_phase else None,
    )

    try:
        db.add(project)
        db.flush()
        db.add(models.ProjectMember(project_id=project.id, user_id=current_user.id))
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# READ – List
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[schemas.ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista proyectos. Los emprendedores ven sus proyectos, los mentores los suyos, los admins todos."""
    query = db.query(models.Project)

    if current_user.role == models.UserRole.emprendedor:
        query = query.join(models.ProjectMember).filter(models.ProjectMember.user_id == current_user.id)
    elif current_user.role == models.UserRole.mentor:
        query = query.join(models.ProjectMentor).filter(models.ProjectMentor.mentor_id == current_user.id)

    return query.offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# READ – Get by ID
# ---------------------------------------------------------------------------

@router.get("/{project_id}", response_model=schemas.ProjectDetailResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Obtiene el detalle de un proyecto con miembros y mentores."""
    project = get_project_or_404(db, project_id)
    if not can_access_project(db, project_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project access denied")

    return schemas.ProjectDetailResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        cohort_id=project.cohort_id,
        leader_id=project.leader_id,
        current_phase=project.current_phase,
        members=[
            schemas.UserSummary(user_id=member.user_id, full_name=member.user.full_name)
            for member in project.members
        ],
        mentors=[
            schemas.UserSummary(user_id=mentor.mentor_id, full_name=mentor.mentor.full_name)
            for mentor in project.mentors
        ],
    )


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

@router.put("/{project_id}", response_model=schemas.ProjectResponse)
def update_project(
    project_id: UUID,
    project_in: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Actualiza un proyecto. Solo el líder del proyecto o un administrador pueden editarlo."""
    project = get_project_or_404(db, project_id)

    if not is_admin(current_user) and project.leader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el lider del proyecto o un admin pueden actualizar este proyecto",
        )

    update_data = project_in.model_dump(exclude_unset=True)
    if not is_admin(current_user):
        update_data.pop("current_phase_id", None)

    if "cohort_id" in update_data and update_data["cohort_id"]:
        cohort = db.query(models.Cohort).filter(models.Cohort.id == update_data["cohort_id"]).first()
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")

    if "current_phase_id" in update_data and update_data["current_phase_id"]:
        phase = db.query(models.Phase).filter(models.Phase.id == update_data["current_phase_id"]).first()
        if not phase:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete("/{project_id}", response_model=schemas.MessageResponse)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina un proyecto. Solo administradores pueden eliminar proyectos."""
    require_roles(current_user, [models.UserRole.admin])

    project = get_project_or_404(db, project_id)
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}


# ===========================================================================
# PROJECT MEMBERS
# ===========================================================================

@router.post("/{project_id}/members", response_model=schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: UUID,
    member_in: schemas.ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Agrega un miembro al proyecto. Solo el líder del proyecto o un admin pueden agregar miembros."""
    project = get_project_or_404(db, project_id)
    if not is_admin(current_user) and project.leader_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el lider del proyecto o admin pueden agregar miembros")

    # Convertir string a UUID para la consulta
    try:
        member_uuid = UUID(str(member_in.user_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user_id format")

    user = db.query(models.Profile).filter(models.Profile.id == member_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

    if is_project_member(db, project_id, member_uuid):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a project member")

    db.add(models.ProjectMember(project_id=project_id, user_id=member_uuid))
    db.commit()
    return {"message": "Project member added"}


@router.get("/{project_id}/members")
def list_project_members(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista los miembros de un proyecto con datos completos del usuario."""
    project = get_project_or_404(db, project_id)
    if not can_access_project(db, project_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project access denied")

    result = []
    for member in project.members:
        profile = db.query(models.Profile).filter(models.Profile.id == member.user_id).first()
        result.append({
            "user_id": str(member.user_id),
            "full_name": profile.full_name if profile else None,
            "email": profile.email if profile else None,
            "role": profile.role.value if profile and profile.role else None,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        })
    return result


@router.delete("/{project_id}/members/{user_id}", response_model=schemas.MessageResponse)
def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Elimina un miembro del proyecto. Solo el líder o un admin pueden remover miembros."""
    project = get_project_or_404(db, project_id)

    if not is_admin(current_user) and project.leader_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el lider del proyecto o admin pueden remover miembros")

    if project.leader_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the project leader")

    member = (
        db.query(models.ProjectMember)
        .filter(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in this project")

    db.delete(member)
    db.commit()
    return {"message": "Project member removed"}


# ===========================================================================
# PROJECT MENTORS
# ===========================================================================

@router.post("/{project_id}/mentors", response_model=schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
def add_project_mentor(
    project_id: UUID,
    mentor_in: schemas.ProjectMentorCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Asigna un mentor al proyecto. Solo administradores pueden asignar mentores."""
    require_roles(current_user, [models.UserRole.admin])
    get_project_or_404(db, project_id)

    try:
        mentor_uuid = UUID(str(mentor_in.mentor_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mentor_id format")

    mentor = db.query(models.Profile).filter(models.Profile.id == mentor_uuid).first()
    if not mentor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor profile not found")
    if mentor.role != models.UserRole.mentor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not a mentor")

    existing = (
        db.query(models.ProjectMentor)
        .filter(models.ProjectMentor.project_id == project_id, models.ProjectMentor.mentor_id == mentor_uuid)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mentor is already assigned to this project")

    db.add(models.ProjectMentor(project_id=project_id, mentor_id=mentor_uuid))
    db.commit()
    return {"message": "Project mentor assigned"}


@router.get("/{project_id}/mentors")
def list_project_mentors(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista los mentores de un proyecto con datos completos."""
    project = get_project_or_404(db, project_id)
    if not can_access_project(db, project_id, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project access denied")

    result = []
    for mentor in project.mentors:
        profile = db.query(models.Profile).filter(models.Profile.id == mentor.mentor_id).first()
        result.append({
            "mentor_id": str(mentor.mentor_id),
            "full_name": profile.full_name if profile else None,
            "email": profile.email if profile else None,
            "role": profile.role.value if profile and profile.role else None,
            "assigned_at": mentor.assigned_at.isoformat() if mentor.assigned_at else None,
        })
    return result


@router.delete("/{project_id}/mentors/{mentor_id}", response_model=schemas.MessageResponse)
def remove_project_mentor(
    project_id: UUID,
    mentor_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Desasigna un mentor del proyecto. Solo administradores pueden desasignar mentores."""
    require_roles(current_user, [models.UserRole.admin])

    assignment = (
        db.query(models.ProjectMentor)
        .filter(
            models.ProjectMentor.project_id == project_id,
            models.ProjectMentor.mentor_id == mentor_id,
        )
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor assignment not found")

    db.delete(assignment)
    db.commit()
    return {"message": "Project mentor removed"}


# ---------------------------------------------------------------------------
# PROJECT PUBLIC DETAIL
# ---------------------------------------------------------------------------

@router.get("/{project_id}/public-detail", response_model=schemas.ProjectPublicDetail)
def get_project_public_detail(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Detalle público de un proyecto con stats agregadas."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    member_count = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project_id).count()
    mentor_count = db.query(models.ProjectMentor).filter(models.ProjectMentor.project_id == project_id).count()

    total_phases = db.query(models.Phase).count() or 1
    current_order = project.current_phase.order if project.current_phase else 0
    progress = min(100.0, round((current_order / total_phases) * 100, 1))

    return schemas.ProjectPublicDetail(
        id=project.id,
        name=project.name,
        description=project.description,
        cohort_name=project.cohort.name if project.cohort else None,
        current_phase_name=project.current_phase.name if project.current_phase else None,
        leader_name=project.leader.full_name if project.leader else None,
        member_count=member_count,
        mentor_count=mentor_count,
        progress_percentage=progress,
    )


# ---------------------------------------------------------------------------
# ADMIN: Change project phase manually
# ---------------------------------------------------------------------------

@router.put("/{project_id}/phase", response_model=schemas.ProjectResponse)
def change_project_phase(
    project_id: UUID,
    phase_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Cambia manualmente la fase de un proyecto. Solo admin."""
    require_roles(current_user, [models.UserRole.admin])

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    phase = db.query(models.Phase).filter(models.Phase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found")

    project.current_phase_id = phase_id
    db.commit()
    db.refresh(project)

    # Notificar a los miembros
    from app.routers.notifications import create_notification
    members = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project_id).all()
    for m in members:
        create_notification(db, m.user_id, "Fase actualizada", f"Tu proyecto '{project.name}' avanzó a la fase: {phase.name}", "info", project_id)
    db.commit()

    return project

