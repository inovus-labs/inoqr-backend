from sqlalchemy import (
    func,
    ForeignKey,
    CheckConstraint,
)
from app.models.base import Base
from sqlalchemy.dialects.postgresql import UUID, TEXT, TIMESTAMP
from datetime import datetime
from sqlalchemy import func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid


class Folder(Base):
    __tablename__ = "folders"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    __table_args__ = (
        CheckConstraint("updated_at >= created_at", name="chk_folder_update_create"),
        UniqueConstraint("id", "user_id", name="uq_folder_user"),
        UniqueConstraint("user_id", "name", name="uq_user_folder_name"),
    )

    user: Mapped["User"] = relationship("User", back_populates="folders")  # Many to One
    qrcodes: Mapped[list["QrCode"]] = relationship(
        "QrCode",
        back_populates="folder",
        primaryjoin="and_(QrCode.folder_id == Folder.id, QrCode.user_id == Folder.user_id)",
    )  # One to Many
