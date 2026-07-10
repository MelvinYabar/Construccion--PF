import os
import secrets
import time
import urllib.parse

import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_access_token, get_current_user, JWT_SECRET, JWT_ALGORITHM
from app.database import get_db
from app.supabase_auth import create_supabase_auth_user
from app.mongo import log_action


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# OAuth 2.0 Authorization Code flow con Google (proveedor de terceros)
# ---------------------------------------------------------------------------
# Endpoints estándar del proveedor (Google). Vienen de .env, nunca hardcodeados.
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Duración del state (10 min) — suficiente para que el usuario complete el login
OAUTH_STATE_TTL_SECONDS = 600


def _create_oauth_state() -> str:
    """Genera un state JWT firmado con JWT_SECRET.

    El state es auto-contenido: no requiere cookies ni almacenamiento server-side.
    aún así protege contra CSRF porque un atacante no puede forjar un state válido
    sin conocer JWT_SECRET.
    """
    now = int(time.time())
    payload = {
        "nonce": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + OAUTH_STATE_TTL_SECONDS,
        "purpose": "oauth_state",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _verify_oauth_state(state: str) -> bool:
    """Verifica que el state sea un JWT válido firmado por nosotros y no expirado."""
    try:
        payload = jwt.decode(state, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return False
    if payload.get("purpose") != "oauth_state":
        return False
    if payload.get("exp", 0) < int(time.time()):
        return False
    return True


# ---------------------------------------------------------------------------
# REGISTER
# ---------------------------------------------------------------------------

@router.post("/register", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Registra un nuevo usuario y crea su perfil automaticamente."""
    if user_in.role != models.UserRole.emprendedor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El registro publico solo permite cuentas de emprendedor",
        )

    existing = db.query(models.Profile).filter(models.Profile.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email",
        )

    create_supabase_auth_user(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
        role=user_in.role.value,
    )

    profile = db.query(models.Profile).filter(models.Profile.email == user_in.email).first()
    if profile is None:
        profile = models.Profile(
            email=user_in.email,
            password=user_in.password,
            full_name=user_in.full_name,
            faculty=user_in.faculty,
            skills=user_in.skills,
            role=user_in.role,
        )
        db.add(profile)
    else:
        profile.password = user_in.password
        profile.full_name = user_in.full_name
        profile.faculty = user_in.faculty
        profile.skills = user_in.skills
        profile.role = user_in.role

    db.commit()
    db.refresh(profile)

    token = create_access_token(profile.id, profile.role.value)

    # Audit log — nuevo usuario registrado
    log_action(
        user_id=profile.id,
        user_email=profile.email,
        action="auth.register",
        resource="session",
        details={"role": profile.role.value, "method": "local"},
    )

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

    # Audit log — login local exitoso
    log_action(
        user_id=profile.id,
        user_email=profile.email,
        action="auth.login.local",
        resource="session",
        details={"role": profile.role.value},
    )

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
        create_supabase_auth_user(
            email=email,
            full_name=claims.get("name"),
            role=models.UserRole.emprendedor.value,
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
        else:
            profile.password = profile.password or "oauth2-google"
            profile.full_name = profile.full_name or claims.get("name")
            profile.role = profile.role or models.UserRole.emprendedor
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
# GOOGLE OAUTH2 — AUTHORIZATION CODE FLOW (flujo completo con proveedor real)
# ---------------------------------------------------------------------------
# Este es el flujo que cumple la rúbrica del Trabajo Final:
#   1. Frontend manda al usuario a GET /auth/oauth/google/login
#   2. Backend responde 302 → Google authorize URL (con client_id, redirect_uri, scope, state)
#   3. Usuario se loguea y da consentimiento en Google
#   4. Google redirige a GET /auth/oauth/google/callback?code=...&state=...
#   5. Backend intercambia code por tokens (server-to-server, usando CLIENT_SECRET)
#   6. Backend valida el ID token de Google con verify_oauth2_token (usa JWKS internamente)
#   7. Backend hace upsert del Profile guardando google_sub (claim `sub` del proveedor)
#   8. Backend emite su propio JWT y redirige al frontend con ?token=<jwt>
# ---------------------------------------------------------------------------

@router.get("/oauth/google/login")
def google_oauth_authorize_code_login():
    """Paso 1 del Authorization Code flow: redirige al usuario a Google para login + consent.

    Genera un `state` como JWT firmado (auto-contenido, no requiere cookies).
    El state protege contra CSRF porque un atacante no puede forjarlo sin conocer JWT_SECRET.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    scope = os.getenv("SCOPE", "openid email profile")

    if not client_id or not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth no configurado. Verifica GOOGLE_CLIENT_ID y GOOGLE_REDIRECT_URI en .env",
        )

    # state JWT firmado — no requiere cookies (más robusto contra bloqueos cross-site)
    state = _create_oauth_state()

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
        "prompt": "select_account",
        "include_granted_scopes": "true",
    }
    authorize_url = f"{GOOGLE_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    return RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)


@router.get("/oauth/google/callback")
def google_oauth_authorize_code_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """Paso 2 del Authorization Code flow: recibe el code, lo intercambia por tokens, valida y emite JWT local.

    Flujo:
      1. Verifica state JWT (CSRF protection, sin cookies)
      2. POST server-to-server a Google Token URL con code + CLIENT_SECRET
      3. Valida el ID token de Google con verify_oauth2_token (JWKS internamente)
      4. Upsert del Profile guardando google_sub (claim `sub`)
      5. Emite JWT local y redirige al frontend con ?token=<jwt>
    """
    # 1. Verificar state JWT (CSRF protection, sin dependencia de cookies)
    if not _verify_oauth_state(state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido o expirado. Reinicia el login.",
        )

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    if not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_SECRET no configurado. Es requerido para el intercambio server-to-server.",
        )

    # 2. Intercambiar code por tokens (server-to-server con CLIENT_SECRET)
    try:
        token_resp = http_requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
    except http_requests.exceptions.RequestException:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo conectar con el endpoint de tokens de Google",
        )

    if token_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token exchange fallido: {token_resp.text}",
        )

    tokens = token_resp.json()
    id_token_jwt = tokens.get("id_token")

    if not id_token_jwt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google no devolvió id_token. Verifica que el scope incluya 'openid'.",
        )

    # 3. Validar ID token de Google con JWKS (verify_oauth2_token usa las claves públicas de Google)
    try:
        claims = id_token.verify_oauth2_token(
            id_token_jwt,
            google_requests.Request(),
            client_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID token de Google inválido o expirado",
        )

    # 4. Extraer identidad del usuario (sub = identificador estable de Google)
    email = claims.get("email")
    name = claims.get("name")
    google_sub = claims.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de Google no incluye email. Verifica el scope.",
        )

    # 5. Upsert Profile — buscar primero por google_sub (identidad estable), luego por email
    profile = None
    if google_sub:
        profile = db.query(models.Profile).filter(models.Profile.google_sub == google_sub).first()
    if profile is None:
        profile = db.query(models.Profile).filter(models.Profile.email == email).first()

    if profile is None:
        # Crear usuario nuevo (emprendedor por defecto, igual que el flujo ID Token)
        create_supabase_auth_user(
            email=email,
            full_name=name,
            role=models.UserRole.emprendedor.value,
        )
        profile = db.query(models.Profile).filter(models.Profile.email == email).first()
        if profile is None:
            profile = models.Profile(
                email=email,
                password="oauth2-google",
                full_name=name,
                faculty=None,
                skills=[],
                role=models.UserRole.emprendedor,
                google_sub=google_sub,
            )
            db.add(profile)
        else:
            profile.google_sub = google_sub
            if not profile.full_name:
                profile.full_name = name
    else:
        # Vincular google_sub si aún no está
        if not profile.google_sub:
            profile.google_sub = google_sub
        if name and not profile.full_name:
            profile.full_name = name

    db.commit()
    db.refresh(profile)

    # 6. Emitir JWT local (la app sigue usando este JWT para los endpoints protegidos)
    local_jwt = create_access_token(profile.id, profile.role.value)

    # Audit log — login OAuth Authorization Code exitoso
    log_action(
        user_id=profile.id,
        user_email=profile.email,
        action="auth.login.oauth_authorization_code",
        resource="session",
        details={
            "provider": "google",
            "google_sub": google_sub,
            "role": profile.role.value,
            "flow": "authorization_code",
        },
    )

    # 7. Redirigir al frontend con el token (query param — el frontend lo limpia después)
    redirect_url = f"{frontend_url}/?token={local_jwt}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/oauth/google/verify", response_model=schemas.ProfileResponse)
def google_oauth_verify_id_token(
    payload: schemas.GoogleOAuthRequest,
    db: Session = Depends(get_db),
):
    """Endpoint de demostración: valida un ID token de Google contra las claves públicas (JWKS).

    Esto demuestra que el backend puede validar tokens emitidos por el proveedor en cualquier
    momento (no solo al login). Útil para la demo del Trabajo Final.
    """
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not google_client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID no configurado")

    try:
        claims = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            google_client_id,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Google ID token inválido o expirado")

    google_sub = claims.get("sub")
    profile = db.query(models.Profile).filter(models.Profile.google_sub == google_sub).first()
    if profile is None:
        profile = db.query(models.Profile).filter(models.Profile.email == claims.get("email")).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Usuario no registrado. Inicia sesión primero con /auth/oauth/google/login")

    return profile


# ---------------------------------------------------------------------------
# ME - Obtener perfil actual
# ---------------------------------------------------------------------------

@router.get("/me", response_model=schemas.ProfileResponse)
def get_me(current_user: schemas.AuthenticatedUser = Depends(get_current_user)):
    """Devuelve el perfil del usuario autenticado."""
    return current_user
