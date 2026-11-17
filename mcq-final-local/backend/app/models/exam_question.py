from datetime import datetime

from sqlalchemy import Float, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

try:
    from app.database import Base
except ModuleNotFoundError:
    from backend.app.database import Base


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

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

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "exam_id",
            "question_id",
            name="uq_exam_question",
        ),
    )