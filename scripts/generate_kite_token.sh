#!/bin/bash
# Quick script to generate Kite Connect access token

API_KEY="j9cwrgsejy2vodgv"
API_SECRET="yh7g1r63r86srfm5ynalh3uoa1fp3dxy"

if [ -z "$1" ]; then
    echo "❌ Error: Request token required"
    echo ""
    echo "Usage: ./scripts/generate_kite_token.sh <request_token>"
    echo ""
    echo "To get request token:"
    echo "1. Visit: https://kite.trade/connect/login?api_key=${API_KEY}&v=3"
    echo "2. Login and authorize"
    echo "3. Copy the request_token from the redirect URL"
    echo "4. Run: ./scripts/generate_kite_token.sh <request_token>"
    exit 1
fi

REQUEST_TOKEN=$1

echo "🔄 Generating access token..."
echo ""

docker compose exec backend python -c "
from kiteconnect import KiteConnect
import sys

api_key = '${API_KEY}'
api_secret = '${API_SECRET}'
request_token = '${REQUEST_TOKEN}'

try:
    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token, api_secret=api_secret)
    access_token = data['access_token']
    
    print('✅ Access token generated successfully!')
    print('')
    print(f'Access Token: {access_token}')
    print('')
    print('📝 Add this to docker-compose.yml:')
    print(f'   KITE_ACCESS_TOKEN: {access_token}')
    print('')
    
    # Test the token
    kite.set_access_token(access_token)
    profile = kite.profile()
    print(f'✅ Token verified! Connected as: {profile.get(\"user_name\", \"N/A\")}')
    print(f'   User ID: {profile.get(\"user_id\", \"N/A\")}')
    print('')
    print('🔄 Next step: Update docker-compose.yml and restart backend:')
    print('   docker compose restart backend')
    
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {str(e)}')
    if 'invalid' in str(e).lower() or 'expired' in str(e).lower():
        print('')
        print('⚠️  The request token may be invalid or expired.')
        print('   Please generate a new request token by visiting:')
        print(f'   https://kite.trade/connect/login?api_key=${API_KEY}&v=3')
    sys.exit(1)
"

