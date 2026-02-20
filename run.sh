#!/usr/bin/env bash
# Single command to run the app (from project root: ./run.sh)
set -e
cd "$(dirname "$0")"
source python/.venv/bin/activate
exec npm run dev
