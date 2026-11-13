from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    text,
    Numeric,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
    )

    settings: Mapped["UserSettings"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all,delete-orphan",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
        cascade="all,delete-orphan",
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
       ForeignKey("users.id", ondelete="CASCADE"),
       unique=True,
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

    user: Mapped[User] = relationship(
        back_populates="notifications"
    )


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    reminders_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )

    reminder_interval_hours: Mapped[int] = mapped_column(
        Integer,
        default=48,
        server_default='48',
        nullable=False,
    )

    reminder_schedule: Mapped[str] = mapped_column(
        String(20),
        default="after_work",
        server_default="after_work",
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Europe/Moscow",
        server_default="Europe/Moscow",
        nullable=False,
    )

    user: Mapped[User] = relationship(
        back_populates="settings"
    )


class Curator(Base):
    __tablename__ = "curators"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    reviews: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    avg_rate: Mapped[float] = mapped_column(
        Numeric(2, 1),
        default=0.0,
        nullable=False
    )

class Survey(Base):
    __tablename__ = "surveys"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    curator_id: Mapped[int] = mapped_column(
        ForeignKey("curatorы.id", ondelete="RESTRICT"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )

    question_1: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    question_2: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    question_3: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    avg_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(2, 1),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
