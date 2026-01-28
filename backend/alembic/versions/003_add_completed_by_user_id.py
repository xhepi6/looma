"""Add completed_by_user_id to items

Revision ID: 003_add_completed_by
Revises: 002_add_priority
Create Date: 2026-01-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from alembic.helpers import column_exists


# revision identifiers, used by Alembic.
revision: str = '003_add_completed_by'
down_revision: Union[str, None] = '002_add_priority'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not column_exists('items', 'completed_by_user_id'):
        op.add_column('items', sa.Column('completed_by_user_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_items_completed_by_user',
            'items',
            'users',
            ['completed_by_user_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    op.drop_constraint('fk_items_completed_by_user', 'items', type_='foreignkey')
    op.drop_column('items', 'completed_by_user_id')
