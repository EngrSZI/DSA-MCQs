from datetime import datetime

from sqlalchemy import Float, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

try:
    from app.database import Base
except ModuleNotFoundError:
    from backend.app.database import Base


class AttemptQuestion(Base):
    __tablename__ = "attempt_questions"

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
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    question_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    correct_option: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_attempt_question_snapshot",
        ),
    )
