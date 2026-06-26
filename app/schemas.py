from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import EnrollmentStatus, ReviewStatus, UserRole


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class AuthenticatedUser(BaseModel):
    id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


def get_current_user_dep():
    """Lazy import para evitar circular dependency."""
    from app.auth import get_current_user
    return Depends(get_current_user)


# ---------------------------------------------------------------------------
# Auth - Register / Login / Response
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    faculty: Optional[str] = None
    skills: Optional[list[str]] = None
    role: UserRole = UserRole.emprendedor


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleOAuthRequest(BaseModel):
    credential: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "ProfileResponse"


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

class ProfileCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    faculty: Optional[str] = None
    skills: Optional[list[str]] = None
    role: UserRole = UserRole.emprendedor


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    faculty: Optional[str] = None
    skills: Optional[list[str]] = None
    role: Optional[UserRole] = None


class ProfileResponse(BaseModel):
    id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    faculty: Optional[str] = None
    skills: Optional[list[str]] = None
    role: Optional[UserRole] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Cohorts
# ---------------------------------------------------------------------------

class CohortCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CohortUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CohortResponse(BaseModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Enrollments
# ---------------------------------------------------------------------------

class EnrollmentCreate(BaseModel):
    cohort_id: UUID


class EnrollmentStatusUpdate(BaseModel):
    status: EnrollmentStatus


class EnrollmentUpdate(BaseModel):
    status: Optional[EnrollmentStatus] = None


class EnrollmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    cohort_id: UUID
    status: EnrollmentStatus
    enrollment_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

class PhaseCreate(BaseModel):
    name: str
    order: int


class PhaseUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None


class PhaseResponse(BaseModel):
    id: int
    name: Optional[str] = None
    order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cohort_id: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cohort_id: Optional[UUID] = None
    current_phase_id: Optional[int] = None


class ProjectResponse(BaseModel):
    id: UUID
    cohort_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    leader_id: UUID
    current_phase_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PhaseSummary(BaseModel):
    id: int
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    user_id: UUID
    full_name: Optional[str] = None


class ProjectDetailResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    cohort_id: Optional[UUID] = None
    leader_id: UUID
    current_phase: Optional[PhaseSummary] = None
    members: list[UserSummary]
    mentors: list[UserSummary]


class ProjectMemberCreate(BaseModel):
    user_id: UUID


class ProjectMentorCreate(BaseModel):
    mentor_id: UUID


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------

class PostCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    is_published: bool = False


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    is_published: Optional[bool] = None


class PostResponse(BaseModel):
    id: UUID
    author_id: UUID
    title: str
    content: str
    image_url: Optional[str] = None
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Deliverables
# ---------------------------------------------------------------------------

class DeliverableCreate(BaseModel):
    phase_id: int
    file_url: str


class DeliverableUpdate(BaseModel):
    phase_id: Optional[int] = None
    file_url: Optional[str] = None


class DeliverableResponse(BaseModel):
    id: UUID
    project_id: UUID
    phase_id: int
    uploaded_by: UUID
    file_url: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DeliverableWithReviewResponse(DeliverableResponse):
    review: Optional["DeliverableReviewResponse"] = None


# ---------------------------------------------------------------------------
# Deliverable Reviews
# ---------------------------------------------------------------------------

class DeliverableReviewCreate(BaseModel):
    status: ReviewStatus
    feedback: Optional[str] = None


class DeliverableReviewUpdate(BaseModel):
    status: Optional[ReviewStatus] = None
    feedback: Optional[str] = None


class DeliverableReviewResponse(BaseModel):
    id: UUID
    deliverable_id: UUID
    mentor_id: UUID
    status: ReviewStatus
    feedback: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class PhaseCount(BaseModel):
    phase_name: Optional[str] = None
    project_count: int


class DashboardReport(BaseModel):
    total_users: int
    users_by_role: dict[str, int]
    total_enrollments: int
    enrollments_by_status: dict[str, int]
    total_projects: int
    projects_by_phase: list[PhaseCount]
    total_deliverables: int
    reviewed_deliverables: int
    pending_deliverables: int
    active_cohorts: int
    published_posts: int


class ProjectProgress(BaseModel):
    project_id: UUID
    project_name: str
    leader_name: Optional[str] = None
    current_phase: Optional[str] = None
    progress_percentage: float
    member_count: int
    deliverable_count: int
    reviews_approved: int
    reviews_rejected: int
    reviews_pending: int


class CohortProgressReport(BaseModel):
    cohort_id: UUID
    cohort_name: Optional[str] = None
    total_projects: int
    projects: list[ProjectProgress]
