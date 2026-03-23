#!/bin/bash
set -euo pipefail
DB_PATH="${DB_PATH:-./sdd_cash_manager.db}"
BACKUP_DIR="${BACKUP_DIR:-./build/backups}"
TIMESTAMP=$(date +%Y%m%dT%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/sdd_cash_manager-${TIMESTAMP}.db"
mkdir -p "$BACKUP_DIR"
if [[ ! -f "$DB_PATH" ]]; then
  echo "Database file not found at $DB_PATH" >&2
  exit 1
fi
cp "$DB_PATH" "$BACKUP_FILE"
echo "$BACKUP_FILE"
