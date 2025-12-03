# Kite Connect Permissions Setup

## Current Status

✅ **Connection**: Working
- Access token is valid
- Can authenticate and get user profile
- Can fetch instrument list

⚠️ **Market Data**: Permission Required
- Quote/OHLC calls are failing with "Insufficient permission"
- Need to enable market data permissions in Kite Connect app

## How to Enable Market Data Permissions

1. **Log in to Zerodha Kite Connect Dashboard**
   - Visit: https://kite.trade/app/dashboard/api
   - Log in with your Zerodha credentials

2. **Find Your API Key**
   - Look for API key: `2pl8jdm3kobxu007`
   - Click on it to view settings

3. **Enable Market Data Permissions**
   - Look for "Market Data" or "Data Access" settings
   - Enable permissions for:
     - Quote data
     - OHLC data
     - Historical data (optional)
   - Save the settings

4. **Regenerate Access Token** (if needed)
   - After enabling permissions, you may need to regenerate the access token
   - Follow the steps in `KITE_TOKEN_GUIDE.md`

5. **Test Again**
   ```bash
   docker compose exec backend python -m app.fetch_real_data --options --underlying NIFTY
   ```

## Alternative: Use Sample Data

Until permissions are enabled, the system automatically falls back to:
- CSV sample data for options
- Historical data from database
- Manual data entry

The ETL will continue to work with sample data, and once permissions are enabled, it will automatically switch to live Kite data.

## Verification

To verify permissions are working:

```bash
docker compose exec backend python -c "
from kiteconnect import KiteConnect
import os

kite = KiteConnect(api_key=os.getenv('KITE_API_KEY'))
kite.set_access_token(os.getenv('KITE_ACCESS_TOKEN'))

# Test quote access
instruments = kite.instruments('NFO')
nifty = [i for i in instruments if i['name'] == 'NIFTY'][:1]

if nifty:
    token = nifty[0]['instrument_token']
    try:
        quote = kite.quote([token])
        print('✅ Market data permissions enabled!')
    except Exception as e:
        print(f'❌ Still need permissions: {e}')
"
```

## Current Workaround

The system is designed to gracefully handle this:
- ✅ Connection works
- ✅ Can identify instruments
- ⚠️ Falls back to sample data for market data
- ✅ All other features work normally

Once permissions are enabled, live options data will automatically start flowing!

