# Stock Screener Live Data Integration

## Overview
The stock screener now uses live data sources (NSE, Zerodha Kite Connect) to fill missing fields, especially CMP (Current Market Price) and market capitalization.

## Implementation

### CMP (Current Market Price)

**Data Source Priority:**
1. **StockTimeSeries** (database) - If data is less than 1 day old
2. **NSE (nsepython)** - Live quote if database data is stale
3. **Zerodha Kite Connect** - Fallback if NSE unavailable

**How it works:**
- Checks if latest StockTimeSeries data is less than 1 day old
- If stale or missing, fetches live quote from NSE or Kite
- Updates CMP with live price

### Market Capitalization

**Data Source Priority:**
1. **Live Quote (NSE)** - Market cap directly from quote
2. **StockFundamentals** - Stored market cap value
3. **Calculated** - Live price × shares outstanding

**How it works:**
- First tries to get market cap from NSE live quote
- Falls back to fundamentals table
- Last resort: calculates from live price × shares outstanding

### Other Fields from Live Quotes

**Available from NSE quotes:**
- `lastPrice` / `lastTradedPrice` → CMP
- `marketCap` / `totalTradedValue` → Market Cap
- `totalTradedVolume` → Volume

**Available from Kite quotes:**
- `last_price` → CMP
- `volume` → Volume

## Code Changes

### `backend/app/services/sector_screener.py`

**Added:**
- Live quote fetching for stocks with stale/missing data
- Market cap extraction from live quotes
- Automatic fallback chain: NSE → Kite → Database

**Key Functions:**
```python
# Fetches live quotes for stocks needing fresh data
tickers_needing_live_quotes = []

# Checks if StockTimeSeries data is stale (>1 day old)
if days_old <= 1:
    # Use database data
else:
    # Fetch live quote

# Extracts market cap from NSE quote
market_cap = price_info.get('marketCap') or price_info.get('totalTradedValue')
```

## Benefits

1. **Always Fresh CMP**: Stock prices are current, not stale
2. **Accurate Market Cap**: Uses live quotes when available
3. **Better Data Quality**: Fills gaps in database data
4. **Automatic Fallback**: Works even if one data source fails

## Performance

- **Batch Processing**: Fetches live quotes only for stocks with stale data
- **Caching**: Uses database data if recent (<1 day old)
- **Rate Limiting**: Small delays between API calls to respect limits

## Testing

```bash
# Test screener with live data
docker compose exec backend python3 -c "
from app.services.sector_screener import screen_stocks
from app.db import database

db = database.SessionLocal()
results = screen_stocks(db, 'it', limit=5)
for stock in results:
    print(f'{stock[\"ticker\"]}: CMP=₹{stock.get(\"cmp\")}, MCap={stock.get(\"market_cap\")} Cr')
db.close()
"
```

## Future Enhancements

1. **Batch Quote Fetching**: Fetch multiple quotes in one API call
2. **Caching**: Cache live quotes for a few minutes to reduce API calls
3. **More Fields**: Extract P/E, dividend yield, etc. from live quotes
4. **WebSocket Updates**: Real-time price updates during market hours

## Notes

- Live quotes are only fetched if database data is stale (>1 day old)
- NSE has rate limits (3 requests/second) - delays are added
- Kite Connect requires valid access token
- Market cap calculation requires `shares_outstanding` in Stock table

