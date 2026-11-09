#!/usr/bin/env bash
# macOS / Linux wrapper:  bash install.sh [--demo ~/my-series | --starter ~/my-series] [--target both] [--remotion-skills] [--yes]
exec python3 "$(cd "$(dirname "$0")" && pwd)/install.py" "$@"
