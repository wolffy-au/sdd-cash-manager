#!/bin/bash
set -euo pipefail
BACKUP_FILE="${1:-}"
if [[ -z "$BACKUP_FILE" ]]; then
  echo "Usage: $0 /path/to/backup.db" >&2
  exit 1
fi
if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file missing: $BACKUP_FILE" >&2
  exit 1
fi
DB_PATH="${DB_PATH:-./sdd_cash_manager.db}"
cp "$BACKUP_FILE" "$DB_PATH"
ls -l "$DB_PATH"
