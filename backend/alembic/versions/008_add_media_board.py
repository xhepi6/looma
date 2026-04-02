"""Add board_type to boards and create media_items table.

Revision ID: 008_add_media_board
Revises: 007_add_translation_fields
Create Date: 2026-04-02
"""

import sqlalchemy as sa
from alembic import op

from migration_helpers import column_exists, table_exists

revision = "008_add_media_board"
down_revision = "007_add_translation_fields"
branch_labels = None
depends_on = None


def upgrade():
    # Add board_type to boards
    if not column_exists("boards", "board_type"):
        with op.batch_alter_table("boards") as batch_op:
            batch_op.add_column(
                sa.Column("board_type", sa.String(20), nullable=False, server_default="task")
            )

    # Create media_items table
    if not table_exists("media_items"):
        op.create_table(
            "media_items",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("board_id", sa.Integer, sa.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("title_en", sa.String(500), nullable=True),
            sa.Column("media_type", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="want_to_watch"),
            sa.Column("position", sa.Float, nullable=False, default=0.0),
            sa.Column("added_by_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        )


def downgrade():
    op.drop_table("media_items")
    with op.batch_alter_table("boards") as batch_op:
        batch_op.drop_column("board_type")
