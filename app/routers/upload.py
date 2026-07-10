"""Upload router — sube archivos a Supabase Storage y devuelve URL pública."""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: schemas.AuthenticatedUser = Depends(get_current_user),
):
    """Sube un archivo a Supabase Storage y devuelve la URL pública."""
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    bucket = os.getenv("SUPABASE_BUCKET", "parmenia-files")

    if not supabase_url or not service_key:
        # Fallback: devolver el archivo como base64 data URL (solo para dev)
        import base64
        content = await file.read()
        b64 = base64.b64encode(content).decode()
        mime = file.content_type or "application/octet-stream"
        return {"url": f"data:{mime};base64,{b64}", "filename": file.filename}

    import requests

    # Generar nombre único
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = f"uploads/{unique_name}"

    content = await file.read()

    # Subir a Supabase Storage
    response = requests.post(
        f"{supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{file_path}",
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": file.content_type or "application/octet-stream",
            "x-upsert": "false",
        },
        data=content,
        timeout=30,
    )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {response.text}",
        )

    # Construir URL pública
    public_url = f"{supabase_url.rstrip('/')}/storage/v1/object/public/{bucket}/{file_path}"

    return {"url": public_url, "filename": file.filename, "path": file_path}
