"""Add title_en and notes_en columns to items table for translation layer.

Revision ID: 007_add_translation_fields
Revises: 006_add_labels_table
Create Date: 2026-04-02
"""

import sqlalchemy as sa
from alembic import op

from migration_helpers import column_exists

revision = "007_add_translation_fields"
down_revision = "006_add_labels_table"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("items") as batch_op:
        if not column_exists("items", "title_en"):
            batch_op.add_column(sa.Column("title_en", sa.String(500), nullable=True))
        if not column_exists("items", "notes_en"):
            batch_op.add_column(sa.Column("notes_en", sa.Text, nullable=True))


def downgrade():
    with op.batch_alter_table("items") as batch_op:
        batch_op.drop_column("notes_en")
        batch_op.drop_column("title_en")
