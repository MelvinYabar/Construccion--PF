from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import can_access_project, get_current_user, is_project_member, require_roles
from app.database import get_db


router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_or_404(db: Session, project_id: UUID) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    require_roles(current_user, [models.UserRole.emprendedor])

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


@router.get("/", response_model=list[schemas.ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    query = db.query(models.Project)

    if current_user.role == models.UserRole.emprendedor:
        query = query.join(models.ProjectMember).filter(models.ProjectMember.user_id == current_user.id)
    elif current_user.role == models.UserRole.mentor:
        query = query.join(models.ProjectMentor).filter(models.ProjectMentor.mentor_id == current_user.id)

    return query.offset(skip).limit(limit).all()


@router.get("/{project_id}", response_model=schemas.ProjectDetailResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
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


@router.post("/{project_id}/members", response_model=schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: UUID,
    member_in: schemas.ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id)
    if current_user.role != models.UserRole.admin and project.leader_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project leader or admin can add members")

    user = db.query(models.Profile).filter(models.Profile.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

    if is_project_member(db, project_id, member_in.user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a project member")

    db.add(models.ProjectMember(project_id=project_id, user_id=member_in.user_id))
    db.commit()
    return {"message": "Project member added"}


@router.post("/{project_id}/mentors", response_model=schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
def add_project_mentor(
    project_id: UUID,
    mentor_in: schemas.ProjectMentorCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    require_roles(current_user, [models.UserRole.admin])
    get_project_or_404(db, project_id)

    mentor = db.query(models.Profile).filter(models.Profile.id == mentor_in.mentor_id).first()
    if not mentor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor profile not found")
    if mentor.role != models.UserRole.mentor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not a mentor")

    existing = (
        db.query(models.ProjectMentor)
        .filter(models.ProjectMentor.project_id == project_id, models.ProjectMentor.mentor_id == mentor_in.mentor_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mentor is already assigned to this project")

    db.add(models.ProjectMentor(project_id=project_id, mentor_id=mentor_in.mentor_id))
    db.commit()
    return {"message": "Project mentor assigned"}
