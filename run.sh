#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3.11 >/dev/null 2>&1; then
    echo "Python 3.11 is required. Install it, then run this script again." >&2
    exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
    python3.11 -m venv .venv
fi

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Created .env from .env.example. Add your webhook URL and credentials to .env." >&2
fi

.venv/bin/python -m pip install -r requirements.lock
exec .venv/bin/python -m streamlit run app.py
