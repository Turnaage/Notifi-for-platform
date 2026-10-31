
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
    )

    reminders_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    reminder_interval_hours: Mapped[int] = mapped_column(
        Integer,
        default=48,
        server_default='48',
        nullable=False,
    )

    reminder_schedule = mapped_column(
        String(20),
        default="after_work",
        server_default="after_work",
        nullable=False,
    )

    timezone = mapped_column(
        String(50),
        default="Europe/Moscow",
        server_default="Europe/Moscow",
        nullable=False,
    )



class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    last_reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


