# Zerodha Kite Connect Setup Guide

This guide explains how to set up and use Zerodha Kite Connect for fetching real-time options data.

## Prerequisites

1. **Zerodha Trading Account**: You need an active Zerodha trading account
2. **Kite Connect API Key**: Already configured: `2pl8jdm3kobxu007`
3. **Kite Connect API Secret**: You'll need to get this from Zerodha Kite Connect dashboard

## Step 1: Get API Secret

1. Log in to [Zerodha Kite Connect](https://kite.trade/)
2. Go to [API Management](https://kite.trade/app/dashboard/api)
3. Find your API key `2pl8jdm3kobxu007`
4. Copy the **API Secret** associated with this key
5. Add it to `docker-compose.yml`:
   ```yaml
   KITE_API_SECRET: your_api_secret_here
   ```

## Step 2: Get Access Token

The access token is required for authenticated API calls. You need to authenticate once:

1. **Generate Login URL:**
   ```bash
   # The login URL format is:
   https://kite.trade/connect/login?api_key=2pl8jdm3kobxu007&v=3
   ```

2. **Authenticate:**
   - Visit the login URL in your browser
   - Log in with your Zerodha credentials
   - Authorize the application
   - You'll be redirected to a URL like:
     ```
     http://localhost/?request_token=xxxxx&action=login&status=success
     ```

3. **Extract Request Token:**
   - Copy the `request_token` from the redirect URL

4. **Generate Access Token:**
   ```python
   from kiteconnect import KiteConnect
   
   api_key = "2pl8jdm3kobxu007"
   api_secret = "your_api_secret"
   request_token = "request_token_from_redirect_url"
   
   kite = KiteConnect(api_key=api_key)
   data = kite.generate_session(request_token, api_secret=api_secret)
   access_token = data["access_token"]
   
   print(f"Access Token: {access_token}")
   ```

5. **Set Access Token:**
   ```bash
   # Add to docker-compose.yml or set as environment variable
   export KITE_ACCESS_TOKEN=your_access_token_here
   ```

## Step 3: Use Kite Connect

### Option 1: Fetch Options Data Directly

```bash
# Fetch options for specific underlying
docker compose exec backend python -m app.services.fetch_kite_options \
  --underlying NIFTY \
  --access-token your_access_token

# Fetch options for all underlyings (NIFTY, BANKNIFTY)
docker compose exec backend python -m app.services.fetch_kite_options \
  --access-token your_access_token
```

### Option 2: Use fetch_real_data Script

```bash
# Fetch options along with other data
docker compose exec backend python -m app.fetch_real_data \
  --options \
  --underlying NIFTY \
  --kite-access-token your_access_token
```

### Option 3: Automatic in Daily ETL

If `KITE_ACCESS_TOKEN` is set in environment, the daily ETL will automatically use Kite:

```bash
export KITE_ACCESS_TOKEN=your_access_token
./run_etl_local.sh
```

## Access Token Validity

- Access tokens are valid until you log out or change your password
- For production, implement token refresh logic
- Store tokens securely (not in git!)

## What Data is Fetched

- **Open Interest (OI)**: Total call and put OI
- **Volume**: Total call and put volume
- **Put-Call Ratio (PCR)**: Calculated from OI and volume
- **Implied Volatility (IV)**: Average IV from option prices
- **OI Changes**: 1-day and 3-day changes

## Troubleshooting

### "Access token required"
- Make sure you've authenticated and set `KITE_ACCESS_TOKEN`
- Access tokens expire on logout/password change

### "Invalid API key"
- Verify API key is correct: `2pl8jdm3kobxu007`
- Check API secret is correct

### "No option instruments found"
- Verify the underlying symbol (NIFTY, BANKNIFTY)
- Check if market is open (options data only available during trading hours)

### Rate Limits
- Kite Connect has rate limits
- Don't make too many requests in quick succession
- Use caching for historical data

## Security Notes

⚠️ **Important**: 
- Never commit API secrets or access tokens to git
- Use environment variables or secure vaults
- Rotate access tokens regularly
- The API key is already in docker-compose.yml (consider moving to .env file)

## Next Steps

1. Get API secret from Zerodha dashboard
2. Authenticate and get access token
3. Set `KITE_ACCESS_TOKEN` environment variable
4. Test with: `python -m app.services.fetch_kite_options --underlying NIFTY`
5. Integrate into daily ETL workflow

