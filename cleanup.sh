#!/bin/bash

echo "-------------------------------------------"
echo "Cleaning up SASE PA Unified Policy Extension"
echo "-------------------------------------------"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SERVICE_FILE="/etc/systemd/system/sase-private-access.service"

SUDO=""
[ "$EUID" -ne 0 ] && SUDO="sudo"

# Stop and remove systemd service
if [ -f "$SERVICE_FILE" ]; then
    echo ""
    echo "➡️  Removing systemd service..."
    $SUDO systemctl stop sase-private-access.service 2>/dev/null
    $SUDO systemctl disable sase-private-access.service 2>/dev/null
    $SUDO rm -f "$SERVICE_FILE"
    $SUDO systemctl daemon-reload
    echo "✅ systemd service removed"
else
    echo ""
    echo "✅ No systemd service found"
fi

# Remove virtual environment
if [ -d venv ]; then
    echo ""
    echo "➡️  Removing Python virtual environment..."
    rm -rf venv
    echo "✅ venv removed"
fi

# Remove generated config (contains API keys, confirm first)
if [ -f config/config.json ]; then
    echo ""
    read -p "➡️  Remove config/config.json (contains API keys/URLs)? [y/N] " REMOVE_CONFIG
    if [[ "$REMOVE_CONFIG" =~ ^[Yy]$ ]]; then
        rm -f config/config.json
        echo "✅ config/config.json removed"
    fi
fi

# Remove generated extension.json
if [ -f frontend/extension.json ]; then
    echo ""
    read -p "➡️  Remove frontend/extension.json? [y/N] " REMOVE_EXT
    if [[ "$REMOVE_EXT" =~ ^[Yy]$ ]]; then
        rm -f frontend/extension.json
        echo "✅ frontend/extension.json removed"
    fi
fi

# Remove generated TLS certificate
if [ -f certs/cert.pem ] || [ -f certs/key.pem ]; then
    echo ""
    read -p "➡️  Remove certs/cert.pem and certs/key.pem? [y/N] " REMOVE_CERTS
    if [[ "$REMOVE_CERTS" =~ ^[Yy]$ ]]; then
        rm -f certs/cert.pem certs/key.pem
        echo "✅ certs removed"
    fi
fi

echo ""
echo "✅ Cleanup complete"
echo "----------------------------------------"
