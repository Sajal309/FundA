# Kite Connect Access Token Generation Guide

## Current Issue

The access token you're using appears to be invalid or expired. Kite Connect access tokens need to be generated properly using the OAuth flow.

## Step-by-Step Guide

### Step 1: Get Request Token

1. **Visit the Kite Connect login URL:**
   ```
   https://kite.trade/connect/login?api_key=2pl8jdm3kobxu007&v=3
   ```

2. **Login with your Zerodha credentials**

3. **Authorize the application**

4. **You'll be redirected to a URL like:**
   ```
   http://localhost/?request_token=XXXXX&action=login&status=success
   ```

5. **Copy the `request_token` value from the URL**

### Step 2: Generate Access Token

**Option A: Using the helper script (Recommended)**

```bash
# From the project root
docker compose exec backend python -m app.generate_kite_token <request_token>
```

**Option B: Manual Python script**

```python
from kiteconnect import KiteConnect

api_key = "2pl8jdm3kobxu007"
api_secret = "2getzlqolcprjdu9k2820cwxbxystvwj"
request_token = "YOUR_REQUEST_TOKEN_HERE"

kite = KiteConnect(api_key=api_key)
data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data["access_token"]

print(f"Access Token: {access_token}")
```

### Step 3: Update Configuration

Once you have the access token, update it in:

1. **docker-compose.yml** (or .env file):
   ```yaml
   KITE_ACCESS_TOKEN: your_new_access_token_here
   ```

2. **Restart services:**
   ```bash
   docker compose restart backend
   ```

### Step 4: Verify Connection

Test the connection:
```bash
docker compose exec backend python -m app.fetch_real_data --options --underlying NIFTY
```

## Important Notes

1. **Access tokens expire** when:
   - You log out of Kite
   - You change your password
   - The token is revoked

2. **For production**, implement token refresh logic to automatically regenerate tokens

3. **Keep tokens secure** - Never commit them to version control

## Troubleshooting

### "Incorrect api_key or access_token"
- Verify the API key matches your Kite Connect app
- Generate a fresh access token using the steps above
- Ensure the request_token was used immediately (they expire quickly)

### "Invalid request token"
- Request tokens expire very quickly (usually within minutes)
- Generate a new request token by visiting the login URL again
- Use the request token immediately to generate access token

### "Token expired"
- Access tokens can expire if you log out or change password
- Generate a new access token following the steps above

## Quick Test

After updating the access token, test with:

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

