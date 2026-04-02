"""Add TMDB metadata columns to media_items table.

Revision ID: 009_add_tmdb_metadata_fields
Revises: 008_add_media_board
Create Date: 2026-04-03
"""

import sqlalchemy as sa
from alembic import op

from migration_helpers import column_exists

revision = "009_add_tmdb_metadata_fields"
down_revision = "008_add_media_board"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("media_items") as batch_op:
        if not column_exists("media_items", "year"):
            batch_op.add_column(sa.Column("year", sa.Integer, nullable=True))
        if not column_exists("media_items", "genre"):
            batch_op.add_column(sa.Column("genre", sa.String(500), nullable=True))
        if not column_exists("media_items", "rating"):
            batch_op.add_column(sa.Column("rating", sa.Float, nullable=True))
        if not column_exists("media_items", "synopsis"):
            batch_op.add_column(sa.Column("synopsis", sa.Text, nullable=True))
        if not column_exists("media_items", "seasons"):
            batch_op.add_column(sa.Column("seasons", sa.Integer, nullable=True))
        if not column_exists("media_items", "tmdb_id"):
            batch_op.add_column(sa.Column("tmdb_id", sa.Integer, nullable=True))


def downgrade():
    with op.batch_alter_table("media_items") as batch_op:
        batch_op.drop_column("tmdb_id")
        batch_op.drop_column("seasons")
        batch_op.drop_column("synopsis")
        batch_op.drop_column("rating")
        batch_op.drop_column("genre")
        batch_op.drop_column("year")
