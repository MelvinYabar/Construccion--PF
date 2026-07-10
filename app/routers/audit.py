"""Audit router — expone los logs guardados en MongoDB.

Solo los administradores pueden ver todos los logs. Los usuarios normales solo
pueden ver sus propias acciones (ownership check por user_id).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.mongo import query_audit_logs, log_action, get_mongo_db

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/status")
def audit_status():
    """Indica si MongoDB está configurado y disponible. Útil para la demo."""
    db = get_mongo_db()
    if db is None:
        return {"configured": False, "available": False, "message": "MONGODB_URI no configurado"}
    try:
        db.command("ping")
        count = db.audit_logs.count_documents({})
        return {"configured": True, "available": True, "audit_logs_count": count}
    except Exception as e:
        return {"configured": True, "available": False, "error": str(e)}


@router.get("/logs")
def list_audit_logs(
    user_id: str | None = Query(None, description="Filtrar por user_id (solo admin)"),
    action: str | None = Query(None, description="Filtrar por acción (ej: 'login.oauth')"),
    resource: str | None = Query(None, description="Filtrar por recurso (ej: 'project')"),
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Lista audit logs.

    - admin: puede ver todos los logs y filtrar por user_id.
    - emprendedor/mentor: solo ven sus propios logs (user_id se fuerza al suyo).
    """
    if current_user.role == models.UserRole.admin:
        target_user_id = user_id  # admin puede filtrar por cualquiera
    else:
        target_user_id = str(current_user.id)  # los demás solo se ven a sí mismos
        if user_id and user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="No puedes ver logs de otro usuario")

    logs = query_audit_logs(
        user_id=target_user_id,
        action=action,
        resource=resource,
        limit=limit,
        skip=skip,
    )
    return {"logs": logs, "count": len(logs)}


@router.get("/me")
def list_my_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Atajo: lista los audit logs del usuario autenticado."""
    logs = query_audit_logs(
        user_id=str(current_user.id),
        limit=limit,
        skip=skip,
    )
    return {"logs": logs, "count": len(logs)}


@router.post("/test")
def create_test_log(
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Endpoint de prueba: inserta un log de demostración. Útil para verificar la conexión."""
    ok = log_action(
        user_id=current_user.id,
        user_email=current_user.email,
        action="audit.test",
        resource="audit",
        resource_id=None,
        details={"message": "Log de prueba creado desde /audit/test"},
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo escribir en MongoDB. Verifica MONGODB_URI.",
        )
    return {"message": "Log de prueba insertado correctamente"}
