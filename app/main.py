from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, cohorts, deliverables, enrollments, integrations, phases, posts, profiles, projects, reports


app = FastAPI(title="Pre-incubation Platform API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


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
