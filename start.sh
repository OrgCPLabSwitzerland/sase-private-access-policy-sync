#!/bin/bash

echo "[INFO] Starting Smart-1 Extension: SASE Unified PA Policy..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv
source venv/bin/activate

# Start backend
echo "[INFO] Starting service..."
cd backend
exec python3 app.py
