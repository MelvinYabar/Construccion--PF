from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import EnrollmentStatus, ReviewStatus, UserRole


class AuthenticatedUser(BaseModel):
    id: UUID
    full_name: Optional[str] = None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    is_published: bool = False


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


class CohortResponse(BaseModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EnrollmentCreate(BaseModel):
    cohort_id: UUID


class EnrollmentStatusUpdate(BaseModel):
    status: EnrollmentStatus


class EnrollmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    cohort_id: UUID
    status: EnrollmentStatus
    enrollment_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cohort_id: Optional[UUID] = None


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


class DeliverableCreate(BaseModel):
    phase_id: int
    file_url: str


class DeliverableReviewCreate(BaseModel):
    status: ReviewStatus
    feedback: Optional[str] = None


class DeliverableReviewResponse(BaseModel):
    id: UUID
    deliverable_id: UUID
    mentor_id: UUID
    status: ReviewStatus
    feedback: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DeliverableResponse(BaseModel):
    id: UUID
    project_id: UUID
    phase_id: int
    uploaded_by: UUID
    file_url: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DeliverableWithReviewResponse(DeliverableResponse):
    review: Optional[DeliverableReviewResponse] = None
