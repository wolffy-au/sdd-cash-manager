#!/bin/bash
set -euo pipefail

HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
TRIES=${TRIES:-5}
DELAY=${DELAY:-1}

for i in $(seq 1 "$TRIES"); do
  STATUS=$(curl -fs -o /dev/null -w "%{http_code}" "$HEALTH_URL")
  if [[ "$STATUS" != "200" ]]; then
    echo "Health check failed ($HEALTH_URL) -> $STATUS" >&2
    exit 1
  fi
  echo "[$i/$TRIES] $HEALTH_URL is healthy"
  sleep "$DELAY"
done

echo "Health checks passed against $HEALTH_URL"
