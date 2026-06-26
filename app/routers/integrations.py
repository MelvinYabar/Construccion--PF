from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException, status

from app import schemas
from app.auth import get_current_user


router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.post(
    "/google-calendar/mentorships",
    response_model=schemas.GoogleCalendarMentorshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_google_calendar_mentorship(
    payload: schemas.GoogleCalendarMentorshipCreate,
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Crea una mentoria en el calendario Google del usuario autenticado."""
    if payload.end_datetime <= payload.start_datetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio",
        )

    attendees = [{"email": email} for email in payload.attendee_emails]
    event_body = {
        "summary": payload.title,
        "description": payload.description or f"Mentoria agendada desde Parmenia por {current_user.email}",
        "start": {
            "dateTime": payload.start_datetime.isoformat(),
            "timeZone": payload.timezone,
        },
        "end": {
            "dateTime": payload.end_datetime.isoformat(),
            "timeZone": payload.timezone,
        },
        "attendees": attendees,
    }

    params = {"sendUpdates": "all"}
    if payload.create_meet:
        params["conferenceDataVersion"] = "1"
        event_body["conferenceData"] = {
            "createRequest": {
                "requestId": f"parmenia-{uuid4()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }

    response = requests.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        params=params,
        headers={
            "Authorization": f"Bearer {payload.google_access_token}",
            "Content-Type": "application/json",
        },
        json=event_body,
        timeout=15,
    )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google Calendar API error: {response.text}",
        )

    data = response.json()
    return schemas.GoogleCalendarMentorshipResponse(
        event_id=data["id"],
        title=data.get("summary", payload.title),
        start=payload.start_datetime,
        end=payload.end_datetime,
        html_link=data.get("htmlLink"),
        meet_link=data.get("hangoutLink"),
        attendees=[attendee["email"] for attendee in attendees],
    )
