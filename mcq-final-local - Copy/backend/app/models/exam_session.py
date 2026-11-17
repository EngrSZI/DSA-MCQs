from datetime import datetime

from sqlalchemy import Float, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

try:
    from app.database import Base
except ModuleNotFoundError:
    from backend.app.database import Base


class ExamSession(Base):
    __tablename__ = "exam_sessions"

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

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_progress",
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    total_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    obtained_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )
