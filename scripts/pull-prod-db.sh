#!/bin/bash
set -euo pipefail

# Pull the production SQLite database to the local Docker volume.
# Usage: bash scripts/pull-prod-db.sh
#
# Required env vars (set in .env):
#   PROD_SSH_HOST  - VPS IP or hostname
#   PROD_SSH_USER  - SSH username
#
# Optional env vars:
#   PROD_SSH_PORT  - SSH port (default: 22)
#   PROD_SSH_KEY   - Path to SSH private key (uses SSH agent/config if omitted)
#   PROD_APP_DIR   - App directory on server (default: /opt/apps/looma)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env from project root
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

# Validate required vars
if [ -z "${PROD_SSH_HOST:-}" ] || [ -z "${PROD_SSH_USER:-}" ]; then
  echo "Error: PROD_SSH_HOST and PROD_SSH_USER must be set in .env"
  exit 1
fi

SSH_PORT="${PROD_SSH_PORT:-22}"
SSH_KEY="${PROD_SSH_KEY:-}"
APP_DIR="${PROD_APP_DIR:-/opt/apps/looma}"
REMOTE_TEMP="/tmp/looma-export.db"
LOCAL_TEMP="${TMPDIR:-/tmp}/looma-prod-$(date +%s).db"

# Build SSH/SCP options
SSH_OPTS="-o StrictHostKeyChecking=no -o LogLevel=ERROR -p $SSH_PORT"
SCP_OPTS="-o StrictHostKeyChecking=no -o LogLevel=ERROR -P $SSH_PORT"
if [ -n "$SSH_KEY" ] && [ -f "$SSH_KEY" ]; then
  SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
  SCP_OPTS="$SCP_OPTS -i $SSH_KEY"
fi

REMOTE="$PROD_SSH_USER@$PROD_SSH_HOST"

cleanup() {
  rm -f "$LOCAL_TEMP"
  ssh $SSH_OPTS "$REMOTE" "rm -f $REMOTE_TEMP" 2>/dev/null || true
}
trap cleanup EXIT

echo "Pulling production database..."

# 1. Extract DB from production container
echo "  Extracting from production container..."
ssh $SSH_OPTS "$REMOTE" \
  "cd $APP_DIR && docker cp \$(docker compose ps -q api):/data/app.db $REMOTE_TEMP"

# 2. Download to local machine
echo "  Downloading..."
scp $SCP_OPTS "$REMOTE:$REMOTE_TEMP" "$LOCAL_TEMP"

# 3. Import into local Docker volume
echo "  Importing into local volume..."
LOCAL_CONTAINER=$(docker compose -f "$PROJECT_DIR/docker-compose.local.yml" ps -q api 2>/dev/null || true)

if [ -n "$LOCAL_CONTAINER" ]; then
  docker cp "$LOCAL_TEMP" "$LOCAL_CONTAINER:/data/app.db"
else
  # Container not running — use a temp container to write into the volume
  VOLUME_NAME=$(docker volume ls --format '{{.Name}}' | grep -E '(looma|workspace).*sqlite_data' | head -1)
  if [ -z "$VOLUME_NAME" ]; then
    # Volume doesn't exist yet — create it via docker compose
    echo "  Creating local volume..."
    docker compose -f "$PROJECT_DIR/docker-compose.local.yml" create api 2>/dev/null || true
    VOLUME_NAME=$(docker volume ls --format '{{.Name}}' | grep -E '(looma|workspace).*sqlite_data' | head -1)
    if [ -z "$VOLUME_NAME" ]; then
      echo "Error: Could not create sqlite_data volume."
      exit 1
    fi
  fi
  MSYS_NO_PATHCONV=1 docker run --rm \
    -v "$VOLUME_NAME:/data" \
    -v "$(cygpath -w "$LOCAL_TEMP" 2>/dev/null || echo "$LOCAL_TEMP"):/backup/app.db:ro" \
    alpine cp /backup/app.db /data/app.db
fi

# 4. Report
FILE_SIZE=$(stat --printf="%s" "$LOCAL_TEMP" 2>/dev/null || stat -f%z "$LOCAL_TEMP" 2>/dev/null || echo "unknown")
if [ "$FILE_SIZE" != "unknown" ]; then
  FILE_SIZE="$(( FILE_SIZE / 1024 )) KB"
fi

echo ""
echo "Done! Production database pulled successfully ($FILE_SIZE)."
echo "Run 'docker compose -f docker-compose.local.yml up' to use it."
