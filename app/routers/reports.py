from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_roles
from app.database import get_db


router = APIRouter(prefix="/reports", tags=["Reports"])


# ---------------------------------------------------------------------------
# REPORTE 1: Dashboard general del administrador
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=schemas.DashboardReport)
def dashboard_report(
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """
    Reporte resumen del sistema para el dashboard del administrador.
    Incluye conteos de usuarios por rol, inscripciones por estado,
    proyectos por fase, entregables revisados vs pendientes.
    """
    require_roles(current_user, [models.UserRole.admin])

    # --- Usuarios por rol ---
    users_by_role = (
        db.query(models.Profile.role, func.count(models.Profile.id))
        .group_by(models.Profile.role)
        .all()
    )
    users_map = {str(role): count for role, count in users_by_role}

    # --- Inscripciones por estado ---
    enrollments_by_status = (
        db.query(models.Enrollment.status, func.count(models.Enrollment.id))
        .group_by(models.Enrollment.status)
        .all()
    )
    enrollments_map = {str(status): count for status, count in enrollments_by_status}

    # --- Proyectos por fase ---
    projects_by_phase = (
        db.query(models.Phase.name, func.count(models.Project.id))
        .outerjoin(models.Project, models.Project.current_phase_id == models.Phase.id)
        .group_by(models.Phase.name, models.Phase.order)
        .order_by(models.Phase.order)
        .all()
    )
    projects_by_phase_list = [
        schemas.PhaseCount(phase_name=name, project_count=count)
        for name, count in projects_by_phase
    ]

    # --- Entregables: revisados vs pendientes ---
    total_deliverables = db.query(func.count(models.Deliverable.id)).scalar() or 0
    reviewed_deliverables = (
        db.query(func.count(func.distinct(models.DeliverableReview.deliverable_id)))
        .filter(models.DeliverableReview.status.in_([
            models.ReviewStatus.aprobado,
            models.ReviewStatus.rechazado,
        ]))
        .scalar() or 0
    )
    pending_deliverables = total_deliverables - reviewed_deliverables

    # --- Convocatorias activas ---
    from datetime import date
    active_cohorts = (
        db.query(func.count(models.Cohort.id))
        .filter(models.Cohort.end_date >= date.today())
        .scalar() or 0
    )

    # --- Total publicaciones ---
    total_posts = (
        db.query(func.count(models.Post.id))
        .filter(models.Post.is_published.is_(True))
        .scalar() or 0
    )

    return schemas.DashboardReport(
        total_users=sum(users_map.values()),
        users_by_role=users_map,
        total_enrollments=sum(enrollments_map.values()),
        enrollments_by_status=enrollments_map,
        total_projects=db.query(func.count(models.Project.id)).scalar() or 0,
        projects_by_phase=projects_by_phase_list,
        total_deliverables=total_deliverables,
        reviewed_deliverables=reviewed_deliverables,
        pending_deliverables=pending_deliverables,
        active_cohorts=active_cohorts,
        published_posts=total_posts,
    )


# ---------------------------------------------------------------------------
# REPORTE 2: Progreso de proyectos de una cohorte
# ---------------------------------------------------------------------------

@router.get("/cohort/{cohort_id}/progress", response_model=schemas.CohortProgressReport)
def cohort_progress_report(
    cohort_id: UUID,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """
    Reporte de progreso de todos los proyectos dentro de una cohorte.
    Muestra cada proyecto con su fase actual, cantidad de miembros,
    entregables subidos y estado de revisiones.
    """
    require_roles(current_user, [models.UserRole.admin, models.UserRole.mentor])

    cohort = db.query(models.Cohort).filter(models.Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    # Total de fases en el programa
    total_phases = db.query(func.count(models.Phase.id)).scalar() or 1

    # Proyectos de la cohorte
    projects = (
        db.query(models.Project)
        .filter(models.Project.cohort_id == cohort_id)
        .all()
    )

    project_progress = []
    for project in projects:
        # Fase actual
        current_phase = project.current_phase
        current_phase_name = current_phase.name if current_phase else "Sin fase"
        current_phase_order = current_phase.order if current_phase else 0

        # Porcentaje de avance
        progress_pct = round((current_phase_order / total_phases) * 100, 1) if current_phase else 0

        # Cantidad de miembros
        member_count = (
            db.query(func.count(models.ProjectMember.user_id))
            .filter(models.ProjectMember.project_id == project.id)
            .scalar() or 0
        )

        # Entregables
        deliverable_count = (
            db.query(func.count(models.Deliverable.id))
            .filter(models.Deliverable.project_id == project.id)
            .scalar() or 0
        )

        # Revisiones aprobadas y rechazadas
        approved = (
            db.query(func.count(models.DeliverableReview.id))
            .join(models.Deliverable, models.Deliverable.id == models.DeliverableReview.deliverable_id)
            .filter(
                models.Deliverable.project_id == project.id,
                models.DeliverableReview.status == models.ReviewStatus.aprobado,
            )
            .scalar() or 0
        )

        rejected = (
            db.query(func.count(models.DeliverableReview.id))
            .join(models.Deliverable, models.Deliverable.id == models.DeliverableReview.deliverable_id)
            .filter(
                models.Deliverable.project_id == project.id,
                models.DeliverableReview.status == models.ReviewStatus.rechazado,
            )
            .scalar() or 0
        )

        pending = deliverable_count - approved - rejected
        if pending < 0:
            pending = 0

        project_progress.append(schemas.ProjectProgress(
            project_id=project.id,
            project_name=project.name,
            leader_name=project.leader.full_name if project.leader else None,
            current_phase=current_phase_name,
            progress_percentage=progress_pct,
            member_count=member_count,
            deliverable_count=deliverable_count,
            reviews_approved=approved,
            reviews_rejected=rejected,
            reviews_pending=pending,
        ))

    return schemas.CohortProgressReport(
        cohort_id=cohort.id,
        cohort_name=cohort.name,
        total_projects=len(projects),
        projects=project_progress,
    )