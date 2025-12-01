#!/usr/bin/env bash
set -euo pipefail

# Simple helper to run the daily ETL inside the backend container.
# Usage:
#   ./run_etl_local.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

docker compose exec backend python -m app.run_daily_etl


