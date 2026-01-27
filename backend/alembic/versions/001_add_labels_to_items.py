"""Add labels column to items

Revision ID: 001_add_labels
Revises:
Create Date: 2026-01-27

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_labels'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add labels column to items table
    op.add_column('items', sa.Column('labels', sa.JSON(), nullable=False, server_default='[]'))


def downgrade() -> None:
    op.drop_column('items', 'labels')
