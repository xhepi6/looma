"""Add chat_messages table for chat history.

Revision ID: 010_add_chat_messages
Revises: 009_add_tmdb_metadata_fields
Create Date: 2026-04-03
"""

import sqlalchemy as sa
from alembic import op

from migration_helpers import table_exists

revision = "010_add_chat_messages"
down_revision = "009_add_tmdb_metadata_fields"
branch_labels = None
depends_on = None


def upgrade():
    if not table_exists("chat_messages"):
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade():
    op.drop_table("chat_messages")
