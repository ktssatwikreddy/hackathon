"""enrollment requests

Revision ID: a541b8b5a161
Revises: d488823288d7
Create Date: 2026-06-19 14:36:00.465839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a541b8b5a161'
down_revision: Union[str, None] = 'd488823288d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("enrollment_requests"):
        return
    op.create_table(
        "enrollment_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("training_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("decided_by", sa.Integer(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["training_id"], ["trainings.id"]),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("enrollment_requests", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_enrollment_requests_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_enrollment_requests_training_id"), ["training_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("enrollment_requests", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_enrollment_requests_training_id"))
        batch_op.drop_index(batch_op.f("ix_enrollment_requests_user_id"))
    op.drop_table("enrollment_requests")
