"""add per-attempt question snapshots

Revision ID: e4f7a1b2c3d4
Revises: d262638dd035
Create Date: 2026-09-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f7a1b2c3d4"
down_revision: Union[str, None] = "d262638dd035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exam_attempts",
        sa.Column(
            "passing_marks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.alter_column("exam_attempts", "passing_marks", server_default=None)

    op.create_table(
        "attempt_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("question_order", sa.Integer(), nullable=False),
        sa.Column("marks", sa.Integer(), nullable=False),
        sa.Column("correct_option", sa.String(length=1), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["exam_attempts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_attempt_question_snapshot",
        ),
    )
    op.create_index(
        op.f("ix_attempt_questions_id"),
        "attempt_questions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attempt_questions_attempt_id"),
        "attempt_questions",
        ["attempt_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attempt_questions_question_id"),
        "attempt_questions",
        ["question_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_attempt_questions_question_id"),
        table_name="attempt_questions",
    )
    op.drop_index(
        op.f("ix_attempt_questions_attempt_id"),
        table_name="attempt_questions",
    )
    op.drop_index(
        op.f("ix_attempt_questions_id"),
        table_name="attempt_questions",
    )
    op.drop_table("attempt_questions")
    op.drop_column("exam_attempts", "passing_marks")
