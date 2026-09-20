from sqlalchemy import func, ForeignKey, CheckConstraint, ForeignKeyConstraint
from app.models.base import Base
from sqlalchemy.dialects.postgresql import UUID, TEXT, TIMESTAMP, VARCHAR
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid


class QrCode(Base):
    __tablename__ = "qr_codes"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    folder_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=True)
    slug: Mapped[str] = mapped_column(VARCHAR(25), unique=True, nullable=False)
    destination: Mapped[str] = mapped_column(TEXT, nullable=False)
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
        CheckConstraint("updated_at >= created_at", name="chk_qr_update_create"),
        ForeignKeyConstraint(
            ("folder_id", "user_id"),
            ("folders.id", "folders.user_id"),
            name="fk_user_folder_link",
        ),
        # Alembic Migrations will add this constraint because in SqlAlchemy ForeignKeyConstraint with duplicate source column references are not supported.
        # ForeignKeyConstraint(
        #    ("folder_id"), ("folders.id"), ondelete="SET NULL", name="fk_qr_folder_link"
        # )
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="qrcodes", overlaps="qrcodes"
    )  # Many to One
    folder: Mapped["Folder | None"] = relationship(
        "Folder",
        back_populates="qrcodes",
        primaryjoin="and_(QrCode.folder_id == Folder.id, QrCode.user_id == Folder.user_id)",
        foreign_keys="[QrCode.folder_id, QrCode.user_id]",
        overlaps="qrcodes,user",
    )  # Many to One
