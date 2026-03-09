#!/usr/bin/env bash
# Sync root benchmark directories into docs/benchmark/ for GitHub Pages.
# Run: bash scripts/sync_docs_benchmark.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/docs/benchmark"

dirs=(data evaluation figures questions results runners tools)

for d in "${dirs[@]}"; do
  if [ -d "$ROOT/$d" ]; then
    mkdir -p "$DEST/$d"
    rsync -a --delete \
      --exclude='PLAN.md' \
      --exclude='__pycache__' \
      --exclude='*.pyc' \
      "$ROOT/$d/" "$DEST/$d/"
  fi
done

# Also sync chaining/ (only exists at root level as chaining/)
if [ -d "$ROOT/chaining" ]; then
  mkdir -p "$DEST/chaining"
  rsync -a --delete \
    --exclude='PLAN.md' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    "$ROOT/chaining/" "$DEST/chaining/"
fi

echo "docs/benchmark/ synced from root directories"
