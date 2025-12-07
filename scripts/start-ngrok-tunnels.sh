#!/bin/bash

# Start ngrok tunnels for both frontend and backend
# This uses ngrok's config file to run multiple tunnels

set -e

echo "🚀 Starting ngrok tunnels for FundA..."
echo ""

# Check if services are running
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "❌ Frontend is not running on port 3000"
    echo "   Start it with: docker compose up frontend"
    exit 1
fi

if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "❌ Backend is not running on port 8000"
    echo "   Start it with: docker compose up backend"
    exit 1
fi

echo "✅ Services are running"
echo ""

# Create ngrok config file
NGROK_CONFIG="/tmp/ngrok-fundA.yml"
cat > "$NGROK_CONFIG" <<EOF
version: "2"
authtoken_from_env: true
tunnels:
  frontend:
    addr: 3000
    proto: http
    inspect: true
  backend:
    addr: 8000
    proto: http
    inspect: true
EOF

echo "📋 Starting ngrok with config..."
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""

# Start ngrok
ngrok start --config "$NGROK_CONFIG" --all > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 4

# Get the public URLs
echo "🔍 Fetching ngrok URLs..."
sleep 2

FRONTEND_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if 'frontend' in tunnel.get('name', '') and 'https' in tunnel.get('public_url', ''):
            print(tunnel.get('public_url', ''))
            break
except:
    pass
" 2>/dev/null || echo "")

BACKEND_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if 'backend' in tunnel.get('name', '') and 'https' in tunnel.get('public_url', ''):
            print(tunnel.get('public_url', ''))
            break
except:
    pass
" 2>/dev/null || echo "")

echo ""
echo "═══════════════════════════════════════════════════════════════"
if [ -n "$FRONTEND_URL" ] && [ -n "$BACKEND_URL" ]; then
    echo "✅ Ngrok tunnels are running!"
    echo ""
    echo "📱 Public URLs:"
    echo "   Frontend: $FRONTEND_URL"
    echo "   Backend:  $BACKEND_URL"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Update frontend/.env:"
    echo "      echo 'VITE_API_URL=$BACKEND_URL' > frontend/.env"
    echo ""
    echo "   2. Restart frontend:"
    echo "      docker compose restart frontend"
    echo ""
    echo "   3. Share this URL with your friend:"
    echo "      $FRONTEND_URL"
    echo ""
else
    echo "⚠️  Could not fetch URLs automatically."
    echo "   Please check: http://localhost:4040"
    echo ""
    echo "   Look for the tunnels named 'frontend' and 'backend'"
    echo ""
fi
echo "🌐 Ngrok web interface: http://localhost:4040"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop ngrok tunnels..."
echo ""

# Save PIDs for cleanup
echo $NGROK_PID > /tmp/ngrok-fundA.pid
echo "$FRONTEND_URL" > /tmp/ngrok-frontend-url.txt
echo "$BACKEND_URL" > /tmp/ngrok-backend-url.txt

# Wait for user interrupt
trap "kill $NGROK_PID 2>/dev/null; rm -f $NGROK_CONFIG /tmp/ngrok-fundA.pid; exit" INT TERM
wait $NGROK_PID

