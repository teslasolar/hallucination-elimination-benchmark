#!/usr/bin/env bash
# Sync root benchmark directories into docs/benchmark/ for GitHub Pages.
# Run: bash scripts/sync_docs_benchmark.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/docs/benchmark"

sync_dir() {
  local src="$1" dst="$2"
  # Remove old contents (except PLAN.md)
  find "$dst" -maxdepth 1 -type f ! -name 'PLAN.md' -delete 2>/dev/null || true
  # Copy new contents (excluding PLAN.md, __pycache__, *.pyc)
  find "$src" -maxdepth 1 -type f ! -name 'PLAN.md' ! -name '*.pyc' -exec cp {} "$dst/" \;
  # Sync subdirectories
  for subdir in "$src"/*/; do
    [ -d "$subdir" ] || continue
    local name=$(basename "$subdir")
    [ "$name" = "__pycache__" ] && continue
    mkdir -p "$dst/$name"
    sync_dir "$subdir" "$dst/$name"
  done
}

dirs=(data evaluation figures questions results runners tools)

for d in "${dirs[@]}"; do
  if [ -d "$ROOT/$d" ]; then
    mkdir -p "$DEST/$d"
    sync_dir "$ROOT/$d" "$DEST/$d"
  fi
done

if [ -d "$ROOT/chaining" ]; then
  mkdir -p "$DEST/chaining"
  sync_dir "$ROOT/chaining" "$DEST/chaining"
fi

echo "docs/benchmark/ synced from root directories"
