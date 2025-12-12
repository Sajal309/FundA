# Kite Connect Live Data Setup Guide

This guide explains how to set up Zerodha Kite Connect for **live/intraday** stock market data.

## Overview

With Kite Connect configured, the system will:
- ✅ Fetch **live quotes** (real-time prices)
- ✅ Fetch **intraday data** (minute-level OHLCV)
- ✅ Fetch **historical data** (daily OHLCV)
- ✅ Automatically prefer Kite over yfinance when available
- ✅ Fall back to yfinance if Kite is unavailable

## Prerequisites

1. **Zerodha Trading Account** - Active account required
2. **Kite Connect API Key** - Already configured: `2pl8jdm3kobxu007`
3. **Kite Connect API Secret** - Get from Zerodha dashboard
4. **Access Token** - Generated after authentication

## Step 1: Get API Secret

1. Log in to [Zerodha Kite Connect Dashboard](https://kite.trade/app/dashboard/api)
2. Find your API key `2pl8jdm3kobxu007`
3. Copy the **API Secret**
4. Add to `docker-compose.yml`:
   ```yaml
   environment:
     KITE_API_KEY: "2pl8jdm3kobxu007"
     KITE_API_SECRET: "your_api_secret_here"
   ```

## Step 2: Generate Access Token

### Option A: Using the Helper Script

1. **Get Request Token:**
   - Visit: https://kite.trade/connect/login?api_key=2pl8jdm3kobxu007&v=3
   - Log in with Zerodha credentials
   - Authorize the application
   - Copy the `request_token` from the redirect URL

2. **Generate Access Token:**
   ```bash
   docker compose exec backend python -m app.generate_kite_token <request_token>
   ```

3. **Set Access Token:**
   ```bash
   export KITE_ACCESS_TOKEN=your_access_token_here
   # Or add to docker-compose.yml:
   KITE_ACCESS_TOKEN: "your_access_token_here"
   ```

### Option B: Manual Python Script

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

## Step 3: Verify Setup

```bash
# Test live quote
curl http://localhost:8000/api/v1/live-quote/RELIANCE

# Test intraday data
curl http://localhost:8000/api/v1/intraday/TCS?interval=5minute&days=1
```

## Step 4: Fetch Live Data

### Using the Script

```bash
# Fetch stock data (will use Kite if available, yfinance otherwise)
docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --days 180

# The system automatically prefers Kite Connect when:
# - KITE_API_KEY is set
# - KITE_ACCESS_TOKEN is set
# - Kite Connect is accessible
```

### Using the API

```bash
# Get live quote for a stock
GET /api/v1/live-quote/{ticker}

# Get live quotes for multiple stocks
GET /api/v1/live-quotes?tickers=RELIANCE,TCS,HDFCBANK

# Get intraday data
GET /api/v1/intraday/{ticker}?interval=5minute&days=1
```

## Data Types

### 1. Live Quotes (Real-Time)
- **Endpoint**: `/api/v1/live-quote/{ticker}`
- **Data**: Current price, OHLC, volume, timestamp
- **Update**: Real-time (when market is open)
- **Use Case**: Live price monitoring, real-time dashboards

### 2. Intraday Data
- **Endpoint**: `/api/v1/intraday/{ticker}`
- **Intervals**: minute, 3minute, 5minute, 15minute, 30minute, 60minute
- **History**: Up to 60 days
- **Use Case**: Intraday charts, minute-level analysis

### 3. Historical Data (Daily)
- **Automatic**: Used in ETL when fetching stock data
- **Source**: Kite Connect (if available) or yfinance (fallback)
- **Use Case**: Daily EOD data, historical analysis

## Features

### Automatic Fallback
- If Kite Connect is not configured → Uses yfinance (EOD data)
- If Kite Connect fails → Falls back to yfinance
- If Kite Connect is available → Uses live/intraday data

### Instrument Token Caching
- First call loads all NSE instruments into cache
- Subsequent calls use cached tokens (faster)
- Cache persists for the session

### Data Freshness
- **Live Quotes**: Real-time (when market is open)
- **Intraday**: Updated every minute during market hours
- **Historical**: End-of-day snapshots

## Rate Limits

Kite Connect has rate limits:
- **Quote API**: 3 requests/second
- **Historical Data**: 3 requests/second
- **WebSocket**: Unlimited (for subscribed instruments)

**Best Practices:**
- Cache instrument tokens
- Batch requests when possible
- Use WebSocket for real-time updates (if needed)

## Troubleshooting

### "Kite Connect credentials not available"
- Check `KITE_API_KEY` and `KITE_ACCESS_TOKEN` are set
- Verify access token is valid (not expired)

### "Instrument token not found"
- Stock ticker might be incorrect
- Check if stock is listed on NSE
- Try with different ticker format

### "Access token expired"
- Access tokens expire after some time
- Regenerate using the steps above

### "Rate limit exceeded"
- Reduce request frequency
- Implement caching
- Use WebSocket for real-time data

## WebSocket Support (Optional)

For real-time streaming quotes, use the WebSocket service:

```python
from app.services.kite_websocket import get_websocket_manager

ws_manager = get_websocket_manager()
if ws_manager:
    # Subscribe to real-time ticks
    ws_manager.subscribe(instrument_token, callback_function)
```

## Next Steps

1. ✅ Set up API credentials
2. ✅ Generate access token
3. ✅ Test live quote endpoint
4. ✅ Update ETL to use Kite Connect
5. ✅ Monitor data freshness in UI

## Notes

- **Access tokens expire** - You may need to regenerate periodically
- **Market hours** - Live data is only available during market hours (9:15 AM - 3:30 PM IST)
- **Data availability** - Some stocks may not have intraday data available
- **Cost** - Kite Connect is free for Zerodha account holders

