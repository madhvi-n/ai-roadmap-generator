from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UUID,
    func,
    DateTime,
)
from app.settings import settings
from sqlalchemy.orm import relationship
from app.database import Base, engine
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    avatar_url = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Store hashed password
    google_oauth_token = Column(String, unique=True, index=True, nullable=True)
    github_token = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())  # Auto-set on insert
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )  # Auto-update on changes

    roadmaps = relationship(
        "Roadmap", back_populates="user", cascade="all, delete-orphan"
    )


class Roadmap(Base):
    __tablename__ = "roadmaps"
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, index=True)
    title = Column(String, nullable=True)
    content = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())  # Auto-set on insert
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )  # Auto-update on changes
    user = relationship("User", back_populates="roadmaps")
