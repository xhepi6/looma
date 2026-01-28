"""Add labels column to items

Revision ID: 001_add_labels
Revises:
Create Date: 2026-01-27

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from migration_helpers import column_exists


# revision identifiers, used by Alembic.
revision: str = '001_add_labels'
down_revision: Union[str, None] = '000_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not column_exists('items', 'labels'):
        op.add_column('items', sa.Column('labels', sa.JSON(), nullable=False, server_default='[]'))


def downgrade() -> None:
    op.drop_column('items', 'labels')
