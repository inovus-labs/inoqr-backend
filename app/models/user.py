from app.models.base import Base
from app.utils.types import AuthProvider
from sqlalchemy.dialects.postgresql import UUID, TEXT, ENUM, TIMESTAMP
from datetime import datetime
from sqlalchemy import func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    provider: Mapped[AuthProvider] = mapped_column(
        ENUM(AuthProvider, name="auth_provider"), nullable=False
    )
    provider_user_id: Mapped[str] = mapped_column(TEXT, nullable=False)
    email: Mapped[str] = mapped_column(TEXT, nullable=False)
    image_url: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider"),
        UniqueConstraint("provider", "email", name="uq_provider_email"),
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )  # One to Many
    folders: Mapped[list["Folder"]] = relationship(
        "Folder", back_populates="user", cascade="all, delete-orphan"
    )  # One to Many
    qrcodes: Mapped[list["QrCode"]] = relationship(
        "QrCode",
        back_populates="user",
        cascade="all, delete-orphan",
    )  # One to Many
