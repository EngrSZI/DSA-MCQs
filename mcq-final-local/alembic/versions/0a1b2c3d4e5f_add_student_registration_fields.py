"""Add student registration fields

Revision ID: 0a1b2c3d4e5f
Revises: ac44909101f5
"""
from alembic import op
import sqlalchemy as sa

revision = "0a1b2c3d4e5f"
down_revision = "9f2a1b3c4d5e"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("student_id", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("program", sa.String(length=150), nullable=True))
    op.create_index("ix_users_student_id", "users", ["student_id"], unique=True)

def downgrade():
    op.drop_index("ix_users_student_id", table_name="users")
    op.drop_column("users", "program")
    op.drop_column("users", "student_id")
