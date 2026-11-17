"""use decimal-style float marks for exam scoring"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "9f2a1b3c4d5e"
down_revision: Union[str, None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on = None


def upgrade() -> None:
    for table, column in [
        ("questions", "marks"),
        ("exams", "total_marks"),
        ("exams", "passing_marks"),
        ("exam_questions", "marks"),
        ("exam_attempts", "obtained_marks"),
        ("exam_attempts", "total_marks"),
        ("exam_attempts", "passing_marks"),
        ("attempt_questions", "marks"),
        ("answer_submissions", "marks_awarded"),
        ("exam_sessions", "total_marks"),
        ("exam_sessions", "obtained_marks"),
    ]:
        op.alter_column(table, column, existing_type=sa.Integer(), type_=sa.Float(), postgresql_using=f"{column}::double precision")


def downgrade() -> None:
    for table, column in [
        ("exam_sessions", "obtained_marks"),
        ("exam_sessions", "total_marks"),
        ("answer_submissions", "marks_awarded"),
        ("attempt_questions", "marks"),
        ("exam_attempts", "passing_marks"),
        ("exam_attempts", "total_marks"),
        ("exam_attempts", "obtained_marks"),
        ("exam_questions", "marks"),
        ("exams", "passing_marks"),
        ("exams", "total_marks"),
        ("questions", "marks"),
    ]:
        op.alter_column(table, column, existing_type=sa.Float(), type_=sa.Integer(), postgresql_using=f"round({column})::integer")
