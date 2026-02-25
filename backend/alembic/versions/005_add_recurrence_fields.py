"""Add recurrence fields to items

Revision ID: 005_add_recurrence
Revises: 004_add_due_at
Create Date: 2026-02-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from migration_helpers import column_exists


# revision identifiers, used by Alembic.
revision: str = '005_add_recurrence'
down_revision: Union[str, None] = '004_add_due_at'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not column_exists('items', 'recurrence_type'):
        op.add_column('items', sa.Column('recurrence_type', sa.String(20), nullable=True))
    if not column_exists('items', 'recurrence_days'):
        op.add_column('items', sa.Column('recurrence_days', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('items', 'recurrence_days')
    op.drop_column('items', 'recurrence_type')
