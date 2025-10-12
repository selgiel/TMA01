#!/usr/bin/env bash
set -euo pipefail

# activate venv if present
[ -d ".venv" ] && source .venv/bin/activate

# point Flask to the package's app object in init.py
export FLASK_APP="${FLASK_APP:-<pkg>:init.app}"
export FLASK_ENV="${FLASK_ENV:-development}"
export FLASK_RUN_HOST="${FLASK_RUN_HOST:-0.0.0.0}"
export FLASK_RUN_PORT="${FLASK_RUN_PORT:-5000}"

exec flask run
