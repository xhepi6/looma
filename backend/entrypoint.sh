#!/bin/bash
set -e

echo "Running database migrations..."

# Ensure data directory exists
mkdir -p /data

# If the database file exists but has no alembic_version table,
# stamp it at 000_initial so subsequent migrations run as upgrades.
# This handles databases originally created by create_all() without Alembic.
python -c "
import sqlite3, sys, os
db_url = os.environ.get('DATABASE_URL', '')
# Extract file path from sqlite URL like 'sqlite+aiosqlite:////data/app.db'
if 'sqlite' not in db_url:
    sys.exit(0)
db_path = db_url.split(':///')[-1]
if not os.path.isfile(db_path):
    sys.exit(0)
conn = sqlite3.connect(db_path)
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
table_names = [t[0] for t in tables]
if 'alembic_version' not in table_names and len(table_names) > 0:
    print(f'Existing database at {db_path} has no alembic_version table. Stamping...')
    conn.execute('CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)')
    conn.execute(\"INSERT INTO alembic_version VALUES ('000_initial')\")
    conn.commit()
conn.close()
"

alembic upgrade head

echo "Migrations complete."
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
