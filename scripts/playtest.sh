#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Run scripts/setup.sh first." >&2
  exit 1
fi

export PYTHONPATH="$ROOT"
exec .venv/bin/python -m watt_the_hack.playtest "$@"
