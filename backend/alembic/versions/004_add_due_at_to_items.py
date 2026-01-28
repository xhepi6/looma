"""Add due_at to items

Revision ID: 004_add_due_at
Revises: 003_add_completed_by
Create Date: 2026-01-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_add_due_at'
down_revision: Union[str, None] = '003_add_completed_by'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('items', sa.Column('due_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('items', 'due_at')
