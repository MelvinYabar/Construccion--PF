"""Integrations router — Google Calendar con persistencia de mentorías."""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_roles, is_project_mentor, is_admin
from app.database import get_db
from app.mongo import log_action

import requests

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.post("/google-calendar/mentorships", response_model=schemas.MentorshipResponse)
def create_google_calendar_mentorship(
    payload: schemas.GoogleCalendarMentorshipCreate,
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Agenda una mentoría en Google Calendar y la persiste en la BD."""
    require_roles(current_user, [models.UserRole.admin, models.UserRole.mentor])

    # Validar que el mentor esté asignado al proyecto si se especifica
    if payload.project_id:
        if not is_admin(current_user) and not is_project_mentor(db, payload.project_id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not assigned to this project")

    attendees = [{"email": email} for email in payload.attendee_emails]

    # Convertir datetimes a string ISO para que requests pueda serializar a JSON
    start_str = payload.start_datetime.isoformat() if hasattr(payload.start_datetime, 'isoformat') else str(payload.start_datetime)
    end_str = payload.end_datetime.isoformat() if hasattr(payload.end_datetime, 'isoformat') else str(payload.end_datetime)

    body = {
        "summary": payload.title,
        "description": payload.description or f"Mentoria agendada desde Parmenia por {current_user.email}",
        "start": {"dateTime": start_str, "timeZone": payload.timezone},
        "end": {"dateTime": end_str, "timeZone": payload.timezone},
        "attendees": attendees,
    }

    if payload.create_meet:
        body["conferenceData"] = {
            "createRequest": {"requestId": os.urandom(8).hex(), "conferenceSolutionKey": {"type": "hangoutsMeet"}}
        }

    try:
        response = requests.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {payload.google_access_token}", "Content-Type": "application/json"},
            json=body,
            params={"conferenceDataVersion": "1"} if payload.create_meet else {},
            timeout=15,
        )
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Google Calendar API unreachable")

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Google Calendar error: {response.text}")

    event = response.json()
    meet_link = None
    if event.get("conferenceData", {}).get("entryPoints"):
        for ep in event["conferenceData"]["entryPoints"]:
            if ep.get("entryPointType") == "video":
                meet_link = ep.get("uri")
                break

    # Persistir en BD
    mentorship = models.Mentorship(
        project_id=payload.project_id,
        mentor_id=current_user.id,
        title=payload.title,
        description=payload.description,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        google_event_id=event.get("id"),
        google_html_link=event.get("htmlLink"),
        google_meet_link=meet_link,
        status="agendada",
    )
    db.add(mentorship)
    db.commit()
    db.refresh(mentorship)

    # Notificar a los miembros del proyecto
    if payload.project_id:
        from app.routers.notifications import create_notification
        members = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == payload.project_id).all()
        for m in members:
            create_notification(db, m.user_id, "Nueva mentoría agendada", f"'{payload.title}' — {payload.start_datetime.strftime('%d/%m %H:%M')}", "info", mentorship.id)
        db.commit()

    # Audit log — mentoría agendada en Google Calendar
    log_action(
        user_id=current_user.id,
        user_email=current_user.email,
        action="mentorship.schedule",
        resource="mentorship",
        resource_id=str(mentorship.id),
        details={
            "title": mentorship.title,
            "project_id": str(mentorship.project_id) if mentorship.project_id else None,
            "google_event_id": mentorship.google_event_id,
            "google_meet_link": mentorship.google_meet_link,
            "start_datetime": mentorship.start_datetime.isoformat() if mentorship.start_datetime else None,
        },
    )

    return mentorship


@router.get("/mentorships", response_model=list[schemas.MentorshipResponse])
def list_mentorships(
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista las mentorías del usuario actual."""
    query = db.query(models.Mentorship)
    if current_user.role == models.UserRole.mentor:
        query = query.filter(models.Mentorship.mentor_id == current_user.id)
    elif current_user.role == models.UserRole.emprendedor:
        # Mentorías de proyectos donde es miembro (LEFT JOIN para tolerar project_id NULL)
        query = query.outerjoin(models.ProjectMember, models.ProjectMember.project_id == models.Mentorship.project_id).filter(
            (models.ProjectMember.user_id == current_user.id) | (models.Mentorship.mentor_id == current_user.id)
        )
    return query.order_by(models.Mentorship.start_datetime.desc()).all()
