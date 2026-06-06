#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTROLLER="${1:-controllers/strategy.py}"

echo "Available scenarios:"
"$ROOT/scripts/playtest.sh" --list-scenarios
echo

while IFS= read -r scenario; do
  [[ -z "$scenario" ]] && continue
  echo "=== $scenario ==="
  "$ROOT/scripts/playtest.sh" "$CONTROLLER" --scenario "$scenario" --quiet
  echo
done < <("$ROOT/scripts/playtest.sh" --list-scenarios | awk 'NF && $1 !~ /^No/ {print $1}')
