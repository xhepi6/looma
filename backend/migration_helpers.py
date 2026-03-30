"""Shared helpers for Alembic migrations."""
import sqlalchemy as sa
from alembic import op


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column already exists in a table (SQLite-compatible)."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(f"PRAGMA table_info('{table_name}')")
    )
    columns = [row[1] for row in result]
    return column_name in columns


def table_exists(table_name: str) -> bool:
    """Check if a table already exists (SQLite-compatible)."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT name FROM sqlite_master "
            f"WHERE type='table' AND name='{table_name}'"
        )
    )
    return result.fetchone() is not None
