#!/bin/bash

echo "-------------------------------------------"
echo "Setting up SASE PA Unified Policy Extension"
echo "-------------------------------------------"

pause() {
    echo ""
    read -p "⏸️  Press Enter to continue..." _
}

# Create venv
if [ ! -d venv ]; then
    echo ""
    echo "➡️  Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# Install deps
echo ""
echo "➡️  Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Virtual environment ready and dependencies installed"
pause

# Create config if missing
if [ ! -f config/config.json ]; then
    echo ""
    echo "⚠️  config/config.json not found"
    echo "➡️  Let's configure it interactively:"
    echo ""

    read -p "   SASE API Key: " SASE_API_KEY
    read -p "   Management server IP/hostname: " MGMT_HOST
    read -p "   Management API Key: " MGMT_API_KEY

    SASE_AUTH_URL="https://api.eu.sase.checkpoint.com/api/v1/auth/authorize"
    SASE_BASE_URL="https://api.eu.sase.checkpoint.com/api/rest"
    MGMT_URL="https://${MGMT_HOST}/web_api"
    VERIFY_TLS="false"

    python3 -c "
import json, sys
path, sase_key, auth_url, base_url, mgmt_url, mgmt_key, verify_tls = sys.argv[1:8]
config = {
    'SASE_API_KEY': sase_key,
    'SASE_AUTH_URL': auth_url,
    'SASE_BASE_URL': base_url,
    'MGMT_URL': mgmt_url,
    'MGMT_API_KEY': mgmt_key,
    'VERIFY_TLS': verify_tls == 'true'
}
with open(path, 'w') as f:
    json.dump(config, f, indent=2)
    f.write('\n')
" "config/config.json" "$SASE_API_KEY" "$SASE_AUTH_URL" "$SASE_BASE_URL" "$MGMT_URL" "$MGMT_API_KEY" "$VERIFY_TLS"

    echo ""
    echo "✅ config/config.json created!"
else
    echo ""
    echo "✅ config/config.json already exists"
fi
pause

# Create extension.json if missing
if [ ! -f frontend/extension.json ]; then
    echo ""
    echo "⚠️  frontend/extension.json not found"
    read -p "➡️  Enter the IP or hostname clients (SmartConsole) will use to reach this backend: " SERVER_HOST

    if [ -z "$SERVER_HOST" ]; then
        echo "⚠️  No value provided, creating from template with placeholder <YOUR-SERVER> (edit it manually before use)."
        cp frontend/extension.example.json frontend/extension.json
    else
        sed "s/<YOUR-SERVER>/${SERVER_HOST}/g" frontend/extension.example.json > frontend/extension.json
    fi

    echo ""
    echo "✅ frontend/extension.json created!"
    echo "----------------------------------------"

    cat frontend/extension.json

    echo "----------------------------------------"
fi
pause

# Generate self-signed TLS certificate matching this server
echo ""
if [ -f certs/cert.pem ] && [ -f certs/key.pem ]; then
    echo "✅ certs/cert.pem and certs/key.pem already exist"
    echo "⚠️  If this server's IP/hostname has changed since the certificate was created, clients will reject it (hostname mismatch) and it must be regenerated."
    read -p "➡️  Regenerate self-signed certificate now? [y/N] (N = keep existing certificate) " REGEN_CERT
else
    echo "⚠️  certs/cert.pem / certs/key.pem not found"
    REGEN_CERT="y"
fi

if [[ "$REGEN_CERT" =~ ^[Yy]$ ]]; then
    if ! command -v openssl &> /dev/null; then
        echo "⚠️  openssl not found, skipping certificate generation."
        echo "👉 Generate certs/cert.pem and certs/key.pem manually before starting the app."
    else
        if [ -n "$SERVER_HOST" ]; then
            read -p "➡️  Enter the IP or hostname clients will use to reach this backend [${SERVER_HOST}]: " CERT_HOST
            CERT_HOST="${CERT_HOST:-$SERVER_HOST}"
        else
            read -p "➡️  Enter the IP or hostname clients will use to reach this backend: " CERT_HOST
        fi

        if [ -z "$CERT_HOST" ]; then
            echo "⚠️  No value provided, skipping certificate generation."
        else
            mkdir -p certs

            # SAN type must match how clients will address this server (IP vs DNS name)
            if [[ "$CERT_HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                SAN="IP:${CERT_HOST}"
            else
                SAN="DNS:${CERT_HOST}"
            fi

            openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
                -keyout certs/key.pem -out certs/cert.pem \
                -subj "/CN=${CERT_HOST}" \
                -addext "subjectAltName=${SAN}"

            echo ""
            echo "✅ Self-signed certificate generated for: ${CERT_HOST}"
            echo "⚠️  Self-signed certs aren't trusted by default; clients (browser/SmartConsole) may need to accept/import it."
        fi
    fi
fi
pause

echo ""
echo "----------------------------------------"
echo "⚠️  SmartConsole setup required"
echo ""
echo "Please create the following BEFORE using the tool:"
echo ""
echo "Policy Package: SASE-Private-Access"
echo "Inline Layer:   SASE-Private-Access-Layer"
echo ""
echo "This is similar to the structure used for SASE Internet Access."
echo "----------------------------------------"

echo ""
echo "➡️ Load extension in SmartConsole:"
echo "https://<YOUR-SERVER>:5000/extension.json"
pause

# Create systemd service
chmod +x start.sh

echo ""
read -p "➡️  Install and enable a systemd service to auto-start the backend on boot? [y/N] " INSTALL_SERVICE

if [[ "$INSTALL_SERVICE" =~ ^[Yy]$ ]]; then
    if [ "$EUID" -ne 0 ] && ! command -v sudo &> /dev/null; then
        echo "⚠️  sudo is required to install the systemd service. Skipping."
    else
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        SERVICE_USER="${SUDO_USER:-$(whoami)}"
        SERVICE_FILE="/etc/systemd/system/sase-private-access.service"

        SUDO=""
        [ "$EUID" -ne 0 ] && SUDO="sudo"

        $SUDO tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=SASE Private Access Policy Sync
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/start.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

        $SUDO systemctl daemon-reload
        $SUDO systemctl enable sase-private-access.service
        $SUDO systemctl start sase-private-access.service

        echo ""
        echo "✅ systemd service installed and started: sase-private-access.service"
        echo "👉 Manage it with: sudo systemctl {status|stop|restart} sase-private-access.service"
        SERVICE_INSTALLED=1
    fi
fi

echo ""
echo "✅ Setup complete"
echo ""
if [ "$SERVICE_INSTALLED" = "1" ]; then
    echo "The backend is already running as a systemd service."
else
    echo "To start the app:"
    echo "source venv/bin/activate && ./start.sh"
fi
echo "----------------------------------------"
