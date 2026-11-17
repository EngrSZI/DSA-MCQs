from datetime import datetime

from sqlalchemy import Float, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

try:
    from app.database import Base
except ModuleNotFoundError:
    from backend.app.database import Base


class AnswerSubmission(Base):
    __tablename__ = "answer_submissions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    selected_option: Mapped[str | None] = mapped_column(
        String(1),
        nullable=True,
    )

    correct_option: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
    )

    marks_awarded: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    is_correct: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    answered_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_attempt_question",
        ),
    )