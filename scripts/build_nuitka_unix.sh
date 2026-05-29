#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: scripts/build_nuitka_unix.sh"
  echo
  echo "Builds Shardveil with Nuitka into build/nuitka/main.dist/."
  echo "Requires .venv, project requirements, and Nuitka to be installed first."
  exit 0
fi

PYTHON=".venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Missing .venv Python. Create it first:" >&2
  echo "  python3 -m venv .venv" >&2
  exit 1
fi

if ! "$PYTHON" -c "import arcade, pyglet, tcod, numpy" >/dev/null 2>&1; then
  echo "Missing runtime dependencies. Install them first:" >&2
  echo "  .venv/bin/python -m pip install -r requirements.txt" >&2
  exit 1
fi

if ! "$PYTHON" -m nuitka --version >/dev/null 2>&1; then
  echo "Missing Nuitka. Install it first:" >&2
  echo "  .venv/bin/python -m pip install nuitka" >&2
  exit 1
fi

export NUITKA_CACHE_DIR="${NUITKA_CACHE_DIR:-$PWD/.nuitka-cache}"

"$PYTHON" -m nuitka src/main.py \
  --standalone \
  --enable-plugin=numpy \
  --include-data-dir=assets=assets \
  --output-dir=build/nuitka \
  --output-filename=shardveil
