import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import SessionLocal
from app.routers import (
    auth, cohorts, deliverables, enrollments, integrations,
    phases, posts, profiles, projects, reports,
    notifications, comments, upload,
)

app = FastAPI(title="Parmenia API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/health/db", tags=["Health"])
def health_db():
    try:
        with SessionLocal() as db:
            db.execute(text("select 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"database": "unavailable", "error": str(exc).split("\n")[0]},
        ) from exc


app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(phases.router)
app.include_router(cohorts.router)
app.include_router(enrollments.router)
app.include_router(posts.router)
app.include_router(projects.router)
app.include_router(deliverables.router)
app.include_router(reports.router)
app.include_router(integrations.router)
app.include_router(notifications.router)
app.include_router(comments.router)
app.include_router(upload.router)
