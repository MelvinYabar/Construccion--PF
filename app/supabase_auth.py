import os
import secrets

import requests
from fastapi import HTTPException, status


def supabase_auth_enabled() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def create_supabase_auth_user(
    *,
    email: str,
    password: str | None = None,
    full_name: str | None = None,
    role: str | None = None,
) -> None:
    """Mirror a local profile into Supabase Authentication > Users.
    If Supabase is not configured, returns silently (does not fail).
    """
    if not supabase_auth_enabled():
        import logging
        logging.getLogger("parmenia.supabase").info("Supabase not configured — skipping Auth sync")
        return None

    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    generated_password = password or secrets.token_urlsafe(24)
    response = requests.post(
        f"{supabase_url.rstrip('/')}/auth/v1/admin/users",
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
        },
        json={
            "email": email,
            "password": generated_password,
            "email_confirm": True,
            "user_metadata": {
                "email": email,
                "full_name": full_name,
                "role": role,
                "source": "parmenia-fastapi",
            },
        },
        timeout=10,
    )

    if response.status_code in (200, 201):
        return

    body = response.text.lower()
    if response.status_code in (400, 422) and (
        "already" in body or "exists" in body or "registered" in body
    ):
        return

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Supabase Auth sync failed: {response.text}",
    )
