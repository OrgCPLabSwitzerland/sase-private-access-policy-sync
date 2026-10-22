#!/bin/bash

echo "[INFO] Starting Smart-1 Extension: SASE Unified PA Policy..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv
if [ ! -f venv/bin/activate ]; then
    echo "[ERROR] venv not found. Run ./setup.sh first to create it and install dependencies."
    exit 1
fi
source venv/bin/activate

# Start backend
echo "[INFO] Starting service..."
cd backend
exec python3 app.py
