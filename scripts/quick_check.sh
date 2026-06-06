#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Smoke test: duck_curve (48 steps)"
"$ROOT/scripts/playtest.sh" controllers/baseline.py --scenario duck_curve --steps 48 --quiet

echo "Smoke test: agentic_demo (full run)"
"$ROOT/scripts/playtest.sh" controllers/strategy.py --scenario agentic_demo --quiet

echo "All smoke tests passed."
