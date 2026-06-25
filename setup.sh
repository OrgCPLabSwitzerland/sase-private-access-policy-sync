#!/bin/bash

echo "-------------------------------------------"
echo "Setting up SASE PA Unified Policy Extension"
echo "-------------------------------------------"

# Create venv
#python3 -m venv venv
#source venv/bin/activate

# Install deps
#pip install --upgrade pip
#pip install -r requirements.txt

# Create config if missing
if [ ! -f config/config.json ]; then
    echo ""
    echo "⚠️  config/config.json not found"
    echo "➡️  Creating from template..."

    cp config/config.example.json config/config.json

    echo ""
    echo "✅ config/config.json created!"
    echo ""
    echo "👉 Please update it with your API keys and URLs:"
    echo "----------------------------------------"

    cat config/config.json

    echo "----------------------------------------"
    echo ""
    echo "⚠️  IMPORTANT:"
    echo "Edit config/config.json before running the application!"
else
    echo ""
    echo "✅ config/config.json already exists"
fi

# Create extension.json if missing
if [ ! -f frontend/extension.json ]; then
    echo ""
    echo "⚠️  frontend/extension.json not found"
    echo "➡️  Creating from template..."

    cp frontend/extension.example.json frontend/extension.json

    echo ""
    echo "✅ frontend/extension.json created!"
    echo ""
    echo "👉 Please update the server URL/IP:"
    echo "----------------------------------------"

    cat frontend/extension.json

    echo "----------------------------------------"
    echo ""
    echo "⚠️  IMPORTANT:"
    echo "Replace <YOUR-SERVER> with your actual IP or hostname!"
fi

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

echo ""
echo "✅ Setup complete"
echo ""
echo "To start the app:"
echo "source venv/bin/activate && ./start.sh"
echo "----------------------------------------"
