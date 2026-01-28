"""Shared helpers for Alembic migrations."""
from alembic import op


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column already exists in a table (SQLite-compatible)."""
    conn = op.get_bind()
    result = conn.execute(
        __import__('sqlalchemy').text(f"PRAGMA table_info('{table_name}')")
    )
    columns = [row[1] for row in result]
    return column_name in columns
