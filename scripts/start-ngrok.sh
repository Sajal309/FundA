#!/bin/bash

# Ngrok setup script for FundA
# This script starts ngrok tunnels for both frontend and backend

set -e

echo "🚀 Starting ngrok tunnels for FundA..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed. Please install it first:"
    echo "   brew install ngrok/ngrok/ngrok"
    exit 1
fi

# Check if ngrok is authenticated
if ! ngrok config check &> /dev/null; then
    echo "⚠️  ngrok may not be authenticated."
    echo "   Run: ngrok config add-authtoken YOUR_TOKEN"
    echo "   Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create a temporary directory for ngrok configs
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# Create ngrok config file
NGROK_CONFIG="$TMP_DIR/ngrok.yml"
cat > "$NGROK_CONFIG" <<EOF
version: "2"
authtoken: $(ngrok config check 2>/dev/null | grep -oP 'authtoken: \K[^ ]+' || echo '')
tunnels:
  frontend:
    addr: 3000
    proto: http
    bind_tls: true
  backend:
    addr: 8000
    proto: http
    bind_tls: true
EOF

echo "📋 Starting ngrok tunnels..."
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""

# Start ngrok
ngrok start --config "$NGROK_CONFIG" --all &
NGROK_PID=$!

# Wait a moment for ngrok to start
sleep 3

# Get the public URLs
echo "🔍 Fetching ngrok URLs..."
sleep 2

# Try to get URLs from ngrok API
FRONTEND_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('name') == 'frontend':
            print(tunnel.get('public_url', ''))
            break
except:
    pass
" 2>/dev/null || echo "")

BACKEND_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('name') == 'backend':
            print(tunnel.get('public_url', ''))
            break
except:
    pass
" 2>/dev/null || echo "")

if [ -z "$FRONTEND_URL" ] || [ -z "$BACKEND_URL" ]; then
    echo ""
    echo "⚠️  Could not automatically fetch URLs. Please check:"
    echo "   http://localhost:4040 (ngrok web interface)"
    echo ""
    echo "📝 Manual setup:"
    echo "   1. Open http://localhost:4040 in your browser"
    echo "   2. Copy the HTTPS URL for 'frontend' tunnel"
    echo "   3. Copy the HTTPS URL for 'backend' tunnel"
    echo "   4. Update frontend/.env with: VITE_API_URL=<backend-ngrok-url>"
    echo ""
else
    echo ""
    echo "${GREEN}✅ Ngrok tunnels are running!${NC}"
    echo ""
    echo "${BLUE}📱 Public URLs:${NC}"
    echo "   Frontend: ${GREEN}$FRONTEND_URL${NC}"
    echo "   Backend:  ${GREEN}$BACKEND_URL${NC}"
    echo ""
    echo "${YELLOW}📝 Next steps:${NC}"
    echo "   1. Update frontend/.env with:"
    echo "      VITE_API_URL=$BACKEND_URL"
    echo ""
    echo "   2. Restart the frontend container:"
    echo "      docker compose restart frontend"
    echo ""
    echo "   3. Share the frontend URL with your friend:"
    echo "      $FRONTEND_URL"
    echo ""
fi

echo "🌐 Ngrok web interface: http://localhost:4040"
echo ""
echo "Press Ctrl+C to stop ngrok tunnels..."

# Wait for user interrupt
wait $NGROK_PID

