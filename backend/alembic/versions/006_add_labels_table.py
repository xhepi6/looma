"""Add labels table and item_labels join table, migrate data from JSON column.

Revision ID: 006_add_labels_table
Revises: 005_add_recurrence
Create Date: 2026-03-31
"""

import colorsys
import json

import sqlalchemy as sa
from alembic import op

from migration_helpers import table_exists

revision = "006_add_labels_table"
down_revision = "005_add_recurrence"
branch_labels = None
depends_on = None

# --- Color computation (matches frontend labelColors.ts djb2 hash) ---

LABEL_HUES = [0, 25, 45, 120, 180, 200, 280, 320, 340]


def _djb2_hash(s: str) -> int:
    h = 5381
    for c in s:
        h = ((h << 5) + h) ^ ord(c)
    return abs(h)


def _label_color_hex(name: str) -> str:
    h = _djb2_hash(name.lower().strip())
    hue = LABEL_HUES[h % len(LABEL_HUES)]
    # HSL(hue, 85%, 92%) — match the frontend's getLabelColor bg color
    r, g, b = colorsys.hls_to_rgb(hue / 360, 0.92, 0.85)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def upgrade():
    if not table_exists("labels"):
        op.create_table(
            "labels",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "board_id",
                sa.Integer,
                sa.ForeignKey("boards.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("name_lower", sa.String(100), nullable=False),
            sa.Column("english_name", sa.String(100), nullable=True),
            sa.Column("color", sa.String(7), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint("board_id", "name_lower", name="uq_label_board_name"),
        )

    if not table_exists("item_labels"):
        op.create_table(
            "item_labels",
            sa.Column(
                "item_id",
                sa.Integer,
                sa.ForeignKey("items.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "label_id",
                sa.Integer,
                sa.ForeignKey("labels.id", ondelete="CASCADE"),
                primary_key=True,
            ),
        )

    # --- Data migration: JSON column → labels + item_labels tables ---
    conn = op.get_bind()

    # Check if the old JSON labels column still exists
    result = conn.execute(sa.text("PRAGMA table_info('items')"))
    columns = [row[1] for row in result]
    if "labels" not in columns:
        return  # Already migrated

    items = conn.execute(
        sa.text("SELECT id, board_id, labels FROM items")
    ).fetchall()

    label_map = {}  # (board_id, name_lower) -> label_id

    for item_id, board_id, labels_raw in items:
        if not labels_raw:
            continue
        labels = json.loads(labels_raw) if isinstance(labels_raw, str) else labels_raw
        if not labels:
            continue

        for name in labels:
            key = (board_id, name.lower())
            if key not in label_map:
                color = _label_color_hex(name)
                conn.execute(
                    sa.text(
                        "INSERT INTO labels (board_id, name, name_lower, color) "
                        "VALUES (:bid, :name, :nl, :color)"
                    ),
                    {"bid": board_id, "name": name, "nl": name.lower(), "color": color},
                )
                result = conn.execute(sa.text("SELECT last_insert_rowid()"))
                label_map[key] = result.scalar()

            conn.execute(
                sa.text(
                    "INSERT OR IGNORE INTO item_labels (item_id, label_id) "
                    "VALUES (:iid, :lid)"
                ),
                {"iid": item_id, "lid": label_map[key]},
            )

    # Drop the old JSON labels column (SQLite requires batch mode)
    with op.batch_alter_table("items") as batch_op:
        batch_op.drop_column("labels")


def downgrade():
    # Re-add JSON labels column
    with op.batch_alter_table("items") as batch_op:
        batch_op.add_column(
            sa.Column("labels", sa.JSON, nullable=False, server_default="[]")
        )

    # Repopulate JSON from join table
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT il.item_id, l.name "
            "FROM item_labels il JOIN labels l ON il.label_id = l.id"
        )
    ).fetchall()

    item_labels_map = {}
    for item_id, name in rows:
        item_labels_map.setdefault(item_id, []).append(name)

    for item_id, labels in item_labels_map.items():
        conn.execute(
            sa.text("UPDATE items SET labels = :labels WHERE id = :id"),
            {"labels": json.dumps(labels), "id": item_id},
        )

    op.drop_table("item_labels")
    op.drop_table("labels")
