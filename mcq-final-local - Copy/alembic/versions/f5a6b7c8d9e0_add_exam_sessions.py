"""add exam sessions and batch metadata

Revision ID: f5a6b7c8d9e0
Revises: e4f7a1b2c3d4
Create Date: 2026-09-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, None] = "e4f7a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exam_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("total_marks", sa.Integer(), nullable=False),
        sa.Column("obtained_marks", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exam_sessions_id"), "exam_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_exam_sessions_exam_id"), "exam_sessions", ["exam_id"], unique=False)
    op.create_index(op.f("ix_exam_sessions_student_id"), "exam_sessions", ["student_id"], unique=False)

    op.add_column(
        "exam_attempts",
        sa.Column("session_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "exam_attempts",
        sa.Column("batch_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column("exam_attempts", "batch_number", server_default=None)
    op.create_foreign_key(
        "fk_exam_attempts_session_id",
        "exam_attempts",
        "exam_sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_exam_attempts_session_id"),
        "exam_attempts",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_exam_attempts_session_id"), table_name="exam_attempts")
    op.drop_constraint("fk_exam_attempts_session_id", "exam_attempts", type_="foreignkey")
    op.drop_column("exam_attempts", "batch_number")
    op.drop_column("exam_attempts", "session_id")
    op.drop_index(op.f("ix_exam_sessions_student_id"), table_name="exam_sessions")
    op.drop_index(op.f("ix_exam_sessions_exam_id"), table_name="exam_sessions")
    op.drop_index(op.f("ix_exam_sessions_id"), table_name="exam_sessions")
    op.drop_table("exam_sessions")
