from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column

try:
    from app.database import Base
except ModuleNotFoundError:
    from backend.app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    option_a: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    option_b: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    option_c: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    option_d: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    correct_option: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    difficulty: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )

    marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )