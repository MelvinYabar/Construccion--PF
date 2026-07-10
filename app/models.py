import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    admin = "admin"
    mentor = "mentor"
    emprendedor = "emprendedor"


class EnrollmentStatus(str, enum.Enum):
    pendiente = "pendiente"
    aceptada = "aceptada"
    rechazada = "rechazada"


class ReviewStatus(str, enum.Enum):
    pendiente = "pendiente"
    aprobado = "aprobado"
    rechazado = "rechazado"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False)
    password = Column(Text, nullable=False)
    full_name = Column(Text)
    faculty = Column(Text)
    skills = Column(ARRAY(Text))
    role = Column(SqlEnum(UserRole, name="user_role", create_type=False), default=UserRole.emprendedor)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    posts = relationship("Post", back_populates="author", passive_deletes=True)
    led_projects = relationship("Project", back_populates="leader", foreign_keys="Project.leader_id", passive_deletes=True)
    memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete")
    mentorships = relationship("ProjectMentor", back_populates="mentor", cascade="all, delete")


class Cohort(Base):
    __tablename__ = "cohorts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    enrollments = relationship("Enrollment", back_populates="cohort")
    projects = relationship("Project", back_populates="cohort")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("user_id", "cohort_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    cohort_id = Column(UUID(as_uuid=True), ForeignKey("cohorts.id"))
    status = Column(SqlEnum(EnrollmentStatus, name="enrollment_status", create_type=False), default=EnrollmentStatus.pendiente)
    enrollment_date = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("Profile")
    cohort = relationship("Cohort", back_populates="enrollments")


class Phase(Base):
    __tablename__ = "phases"

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    order = Column("order", Integer, unique=True)

    projects = relationship("Project", back_populates="current_phase")
    deliverables = relationship("Deliverable", back_populates="phase")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cohort_id = Column(UUID(as_uuid=True), ForeignKey("cohorts.id"))
    name = Column(Text)
    description = Column(Text)
    leader_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    current_phase_id = Column(Integer, ForeignKey("phases.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)

    cohort = relationship("Cohort", back_populates="projects")
    leader = relationship("Profile", back_populates="led_projects", foreign_keys=[leader_id])
    current_phase = relationship("Phase", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project")
    mentors = relationship("ProjectMentor", back_populates="project")
    deliverables = relationship("Deliverable", back_populates="project")


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), primary_key=True)
    joined_at = Column(DateTime(timezone=True), default=utc_now)

    project = relationship("Project", back_populates="members")
    user = relationship("Profile", back_populates="memberships")


class ProjectMentor(Base):
    __tablename__ = "project_mentors"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), default=utc_now)

    project = relationship("Project", back_populates="mentors")
    mentor = relationship("Profile", back_populates="mentorships")


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    title = Column(Text)
    content = Column(Text)
    image_url = Column(Text)
    is_published = Column(Boolean)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utc_now)

    author = relationship("Profile", back_populates="posts")


class Deliverable(Base):
    __tablename__ = "deliverables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    phase_id = Column(Integer, ForeignKey("phases.id"))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    file_url = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    project = relationship("Project", back_populates="deliverables")
    phase = relationship("Phase", back_populates="deliverables")
    uploader = relationship("Profile")
    reviews = relationship("DeliverableReview", back_populates="deliverable")
    comments = relationship("DeliverableComment", back_populates="deliverable", cascade="all, delete-orphan")


class DeliverableReview(Base):
    __tablename__ = "deliverable_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deliverable_id = Column(UUID(as_uuid=True), ForeignKey("deliverables.id"))
    mentor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    status = Column(SqlEnum(ReviewStatus, name="review_status", create_type=False))
    feedback = Column(Text)
    reviewed_at = Column(DateTime(timezone=True), default=utc_now)

    deliverable = relationship("Deliverable", back_populates="reviews")
    mentor = relationship("Profile")


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Text, default="info")  # info, success, warning, deliverable, review, enrollment
    is_read = Column(Boolean, default=False)
    related_id = Column(UUID(as_uuid=True), nullable=True)  # ID del recurso relacionado
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("Profile")


# ---------------------------------------------------------------------------
# Deliverable Comments (chat entre emprendedor y mentor)
# ---------------------------------------------------------------------------

class DeliverableComment(Base):
    __tablename__ = "deliverable_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deliverable_id = Column(UUID(as_uuid=True), ForeignKey("deliverables.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    deliverable = relationship("Deliverable", back_populates="comments")
    author = relationship("Profile")


# ---------------------------------------------------------------------------
# Mentorships (Google Calendar events persistidos)
# ---------------------------------------------------------------------------

class Mentorship(Base):
    __tablename__ = "mentorships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    google_event_id = Column(Text)
    google_html_link = Column(Text)
    google_meet_link = Column(Text)
    status = Column(Text, default="agendada")  # agendada, completada, cancelada
    created_at = Column(DateTime(timezone=True), default=utc_now)

    project = relationship("Project")
    mentor = relationship("Profile")
