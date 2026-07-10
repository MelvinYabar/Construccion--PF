"""Conexión a MongoDB (NoSQL) — segunda base de datos del proyecto.

Justificación del uso de MongoDB en Parmenia
--------------------------------------------
Parmenia usa DOS bases de datos, cada una para lo que mejor hace:

1. PostgreSQL (relacional, vía Supabase)
   - Datos estructurados con relaciones fuertes: perfiles, proyectos, fases,
     cohortes, inscripciones, entregables, revisiones, mentorías.
   - Necesitan transacciones ACID, foreign keys, constraints, JOINs.

2. MongoDB (NoSQL, documental)
   - **Audit logs**: registros append-only de acciones sensibles (login, OAuth,
     creación/edición/eliminación de recursos). Cada acción puede tener
     `details` con estructura variable (campos distintos según la acción),
     lo que encaja naturalmente con un documento BSON sin schema rígido.
   - **Notificaciones** (opcional): también encajarían aquí por su naturaleza
     efímera y flexible, pero por ahora se mantienen en PostgreSQL para no
     romper el frontend existente.

¿Por qué MongoDB y no Redis/otro?
   - Redis es KV/in-memory, no permite consultas ricas por campos anidados.
   - Los audit logs necesitan consultas por `user_id`, `action`, `resource`,
     rango de fechas — MongoDB los indexa eficientemente.
   - Atlas free tier (512 MB) es suficiente para años de auditoría.

Configuración
-------------
En .env:
    MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/parmenia
    MONGODB_DB=parmenia

Si MONGODB_URI no está configurado, la app sigue funcionando pero los audit
logs se ignoran (modo degradado) — útil para desarrollo sin MongoDB.
"""
import os
from datetime import datetime, timezone
from typing import Any, Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.synchronous.database import Database

load_dotenv()

_mongo_client: Optional[MongoClient] = None
_mongo_db: Optional[Database] = None


def _is_configured() -> bool:
    return bool(os.getenv("MONGODB_URI"))


def get_mongo_db() -> Optional[Database]:
    """Devuelve la base de datos Mongo. Si no está configurada, devuelve None."""
    global _mongo_client, _mongo_db
    if not _is_configured():
        return None
    if _mongo_db is None:
        uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB", "parmenia")
        _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _mongo_db = _mongo_client[db_name]
        # Crear índices útiles para las consultas más comunes de audit logs
        _mongo_db.audit_logs.create_index([("user_id", 1), ("created_at", -1)])
        _mongo_db.audit_logs.create_index([("action", 1), ("created_at", -1)])
        _mongo_db.audit_logs.create_index([("resource", 1), ("resource_id", 1)])
    return _mongo_db


def log_action(
    user_id: Any,
    user_email: str,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip: Optional[str] = None,
) -> bool:
    """Inserta un documento de auditoría en MongoDB.

    Args:
        user_id:        ID del usuario que ejecutó la acción (UUID como str).
        user_email:     Email del usuario (denormalizado para que los logs
                        sigan siendo legibles si el usuario se elimina).
        action:         Tipo de acción. Ej: 'login.local', 'login.oauth',
                        'project.create', 'deliverable.upload', 'review.create',
                        'mentorship.schedule', 'profile.update'.
        resource:       Recurso afectado. Ej: 'project', 'deliverable',
                        'review', 'mentorship', 'profile', 'session'.
        resource_id:    ID del recurso afectado (str).
        details:        Diccionario libre con detalles variables según la acción.
        ip:             IP del cliente (opcional).

    Returns:
        True si se insertó, False si MongoDB no está configurado o falló.
    """
    db = get_mongo_db()
    if db is None:
        return False  # Modo degradado: no hay MongoDB, se ignora el log.

    doc = {
        "user_id": str(user_id) if user_id else None,
        "user_email": user_email,
        "action": action,
        "resource": resource,
        "resource_id": str(resource_id) if resource_id else None,
        "details": details or {},
        "ip": ip,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        db.audit_logs.insert_one(doc)
        return True
    except Exception:
        # Los audit logs nunca deben romper el flujo principal de la app.
        return False


def query_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
) -> list[dict]:
    """Consulta audit logs con filtros opcionales. Devuelve los más recientes primero."""
    db = get_mongo_db()
    if db is None:
        return []
    query_filter: dict = {}
    if user_id:
        query_filter["user_id"] = str(user_id)
    if action:
        query_filter["action"] = action
    if resource:
        query_filter["resource"] = resource
    cursor = (
        db.audit_logs.find(query_filter)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    # Convertir _id a string para que sea serializable
    docs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc and doc["created_at"]:
            doc["created_at"] = doc["created_at"].isoformat()
        docs.append(doc)
    return docs
