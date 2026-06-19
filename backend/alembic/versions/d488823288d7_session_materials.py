"""session materials

Revision ID: d488823288d7
Revises: 6975c6720347
Create Date: 2026-06-19 14:15:47.473086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd488823288d7'
down_revision: Union[str, None] = '6975c6720347'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent: create only if the table isn't already present (some local DBs
    # may have been created via create_all before this migration existed).
    bind = op.get_bind()
    if sa.inspect(bind).has_table("session_materials"):
        return
    op.create_table(
        "session_materials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("stored_path", sa.String(length=500), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["training_sessions.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("session_materials", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_session_materials_session_id"), ["session_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("session_materials", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_session_materials_session_id"))
    op.drop_table("session_materials")
