# Generate Kite Connect Access Token - Quick Guide

## Your New Credentials
- **API Key**: `j9cwrgsejy2vodgv`
- **API Secret**: `yh7g1r63r86srfm5ynalh3uoa1fp3dxy`

## Step 1: Get Request Token

1. **Visit this URL in your browser** (replace YOUR_API_KEY with your actual API key):
   ```
   https://kite.trade/connect/login?api_key=j9cwrgsejy2vodgv&v=3
   ```

2. **Login** with your Zerodha credentials

3. **Authorize** the application

4. **After authorization**, you'll be redirected to a URL like:
   ```
   http://localhost:3000/?request_token=XXXXX&action=login&status=success
   ```

5. **Copy the `request_token`** from the URL (the `XXXXX` part)

## Step 2: Generate Access Token

Once you have the request token, run:

```bash
docker compose exec backend python -m app.generate_kite_token <YOUR_REQUEST_TOKEN>
```

Or manually:

```bash
docker compose exec backend python -c "
from kiteconnect import KiteConnect

api_key = 'j9cwrgsejy2vodgv'
api_secret = 'yh7g1r63r86srfm5ynalh3uoa1fp3dxy'
request_token = 'YOUR_REQUEST_TOKEN_HERE'  # Replace with actual token

kite = KiteConnect(api_key=api_key)
data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data['access_token']
print(f'Access Token: {access_token}')
"
```

## Step 3: Update docker-compose.yml

After getting the access token, update `docker-compose.yml`:

```yaml
KITE_ACCESS_TOKEN: YOUR_ACCESS_TOKEN_HERE
```

Then restart the backend:
```bash
docker compose restart backend
```

## Step 4: Test Connection

Test that the connection works:
```bash
docker compose exec backend python -c "
from kiteconnect import KiteConnect
import os

kite = KiteConnect(api_key=os.getenv('KITE_API_KEY'))
kite.set_access_token(os.getenv('KITE_ACCESS_TOKEN'))
profile = kite.profile()
print(f'✅ Connected as: {profile.get(\"user_name\")}')
"
```

## Important Notes

- **Request tokens expire quickly** (usually within a few minutes)
- Generate a new request token each time you need to create an access token
- Access tokens are valid for the trading day (until market close)
- For production, you may want to implement token refresh logic

