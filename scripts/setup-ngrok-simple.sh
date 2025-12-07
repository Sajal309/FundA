#!/bin/bash

# Simple ngrok setup - exposes frontend only
# The frontend will make API calls to the backend ngrok URL

set -e

echo "🚀 Starting ngrok for FundA Frontend..."
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed."
    echo "   Install: brew install ngrok/ngrok/ngrok"
    echo "   Or download from: https://ngrok.com/download"
    exit 1
fi

# Check if services are running
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "⚠️  Frontend is not running on port 3000"
    echo "   Start it with: docker compose up frontend"
    exit 1
fi

if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "⚠️  Backend is not running on port 8000"
    echo "   Start it with: docker compose up backend"
    exit 1
fi

echo "✅ Services are running"
echo ""

# Start ngrok for frontend
echo "📱 Starting ngrok tunnel for frontend (port 3000)..."
echo "   This will expose your app publicly"
echo ""

# Start ngrok in background and capture output
ngrok http 3000 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get the public URL from ngrok API
echo "🔍 Fetching public URL..."
sleep 2

PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if 'https' in tunnel.get('public_url', ''):
            print(tunnel.get('public_url', ''))
            break
except Exception as e:
    pass
" 2>/dev/null || echo "")

if [ -z "$PUBLIC_URL" ]; then
    echo ""
    echo "⚠️  Could not fetch URL automatically."
    echo "   Please check: http://localhost:4040"
    echo "   Copy the HTTPS URL shown there"
    echo ""
    echo "📝 To configure backend access:"
    echo "   1. Start another ngrok tunnel for backend:"
    echo "      ngrok http 8000"
    echo "   2. Update frontend/.env with backend ngrok URL:"
    echo "      VITE_API_URL=<backend-ngrok-url>"
    echo "   3. Restart frontend: docker compose restart frontend"
    echo ""
else
    echo ""
    echo "✅ Ngrok is running!"
    echo ""
    echo "🌐 Public URL: $PUBLIC_URL"
    echo ""
    echo "📝 IMPORTANT: Update backend URL for API calls"
    echo "   1. Start backend ngrok in another terminal:"
    echo "      ngrok http 8000"
    echo "   2. Copy the backend ngrok HTTPS URL"
    echo "   3. Create/update frontend/.env:"
    echo "      echo 'VITE_API_URL=<backend-ngrok-url>' > frontend/.env"
    echo "   4. Restart frontend: docker compose restart frontend"
    echo ""
    echo "   Then share this URL: $PUBLIC_URL"
    echo ""
fi

echo "🌐 Ngrok web interface: http://localhost:4040"
echo ""
echo "Press Ctrl+C to stop ngrok..."

# Wait for interrupt
trap "kill $NGROK_PID 2>/dev/null; exit" INT TERM
wait $NGROK_PID

