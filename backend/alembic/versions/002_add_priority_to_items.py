"""Add priority column to items

Revision ID: 002_add_priority
Revises: 001_add_labels
Create Date: 2026-01-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_priority'
down_revision: Union[str, None] = '001_add_labels'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add priority column to items table with default 'medium'
    op.add_column('items', sa.Column('priority', sa.String(20), nullable=False, server_default='medium'))


def downgrade() -> None:
    op.drop_column('items', 'priority')
