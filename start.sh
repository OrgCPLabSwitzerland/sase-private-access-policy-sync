#!/bin/bash

echo "[INFO] Starting Smart-1 Extension: SASE Unified PA Policy..."

cd /home/admin/sase-unified-pa-policy

# Activate venv
source venv/bin/activate

# Start backend
echo "[INFO] Starting service..."
cd backend
exec python3 app.py
