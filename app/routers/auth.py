import os

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_access_token
from app.database import get_db


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# REGISTER
# ---------------------------------------------------------------------------

@router.post("/register", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Registra un nuevo usuario y crea su perfil automaticamente."""
    existing = db.query(models.Profile).filter(models.Profile.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email",
        )

    profile = models.Profile(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
        faculty=user_in.faculty,
        skills=user_in.skills,
        role=user_in.role,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    token = create_access_token(profile.id, profile.role.value)

    return schemas.AuthResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.ProfileResponse.model_validate(profile),
    )


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------

@router.post("/login", response_model=schemas.AuthResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Inicia sesion y devuelve un JWT."""
    profile = db.query(models.Profile).filter(models.Profile.email == credentials.email).first()
    if not profile or profile.password != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contrasena incorrectos",
        )

    token = create_access_token(profile.id, profile.role.value)

    return schemas.AuthResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.ProfileResponse.model_validate(profile),
    )


# ---------------------------------------------------------------------------
# GOOGLE OAUTH2 / OIDC
# ---------------------------------------------------------------------------

@router.post("/oauth/google", response_model=schemas.AuthResponse)
def login_with_google(payload: schemas.GoogleOAuthRequest, db: Session = Depends(get_db)):
    """Valida el ID token de Google y devuelve el JWT local de la API."""
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID is not configured",
        )

    try:
        claims = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            google_client_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token invalido o expirado",
        ) from None

    email = claims.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token does not include email",
        )

    profile = db.query(models.Profile).filter(models.Profile.email == email).first()
    if profile is None:
        profile = models.Profile(
            email=email,
            password="oauth2-google",
            full_name=claims.get("name"),
            faculty=None,
            skills=[],
            role=models.UserRole.emprendedor,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    else:
        updated = False
        if claims.get("name") and not profile.full_name:
            profile.full_name = claims["name"]
            updated = True
        if updated:
            db.commit()
            db.refresh(profile)

    token = create_access_token(profile.id, profile.role.value)

    return schemas.AuthResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.ProfileResponse.model_validate(profile),
    )


# ---------------------------------------------------------------------------
# ME - Obtener perfil actual
# ---------------------------------------------------------------------------

@router.get("/me", response_model=schemas.ProfileResponse)
def get_me(current_user: schemas.AuthenticatedUser = Depends(schemas.get_current_user_dep)):
    """Devuelve el perfil del usuario autenticado."""
    return current_user
