from datetime import datetime

from sqlalchemy import Float, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

try:
    from app.database import Base
except ModuleNotFoundError:
    from backend.app.database import Base


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("exam_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    batch_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_progress",
    )

    obtained_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    total_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    passing_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    percentage: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0,
    )

    result_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )