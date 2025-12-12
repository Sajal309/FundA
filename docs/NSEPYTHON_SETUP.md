# NSEPython Setup Guide

This guide explains how to use the nsepython library to fetch data from the National Stock Exchange (NSE) of India.

## Installation

The `nsepythonserver` package is already installed in the Docker container. For local development:

```bash
pip install nsepythonserver  # For server environments (Docker, AWS, etc.)
# OR
pip install nsepython  # For local Windows/Mac development
```

## Available Functions

The `nsepython_service.py` module provides the following functions:

### 1. Sector/Index Data

```python
from app.services import nsepython_service

# Fetch sector data
sector_data = nsepython_service.fetch_sector_data('NIFTY 50')
# Returns: Dictionary with sector constituents and their data

# Fetch index constituents
constituents = nsepython_service.fetch_index_constituents('NIFTY BANK')
# Returns: List of dictionaries with constituent data
```

### 2. Stock Data

```python
# Fetch live stock quote
quote = nsepython_service.fetch_stock_quote('RELIANCE')
# Returns: Dictionary with price, volume, market info, etc.

# Fetch stock delivery data
delivery_df = nsepython_service.fetch_stock_delivery_data(
    'RELIANCE',
    from_date=date(2025, 12, 1),
    to_date=date(2025, 12, 12)
)
# Returns: DataFrame with OHLCV and delivery data
```

### 3. FII/DII Data

```python
# Fetch FII/DII trading data
fii_dii = nsepython_service.fetch_fii_dii_data()
# Returns: Dictionary with FII/DII buy/sell data
```

### 4. Options Data

```python
# Fetch option chain
option_chain = nsepython_service.fetch_option_chain('NIFTY')
# Returns: Dictionary with option chain data

# Fetch option chain for specific expiry
option_chain = nsepython_service.fetch_option_chain(
    'NIFTY',
    expiry_date='12-DEC-2025'
)
```

### 5. Bulk/Block Deals

```python
# Fetch bulk deals
bulk_deals = nsepython_service.fetch_bulk_deals()
# Returns: DataFrame with bulk deals data

# Fetch block deals
block_deals = nsepython_service.fetch_block_deals()
# Returns: DataFrame with block deals data
```

### 6. Market Status

```python
# Fetch market status
status = nsepython_service.fetch_market_status()
# Returns: Dictionary with market open/closed status
```

## Usage Examples

### Example 1: Fetch Sector Data

```python
from app.services import nsepython_service
from app.db import database

db = database.SessionLocal()

# Fetch NIFTY 50 data
sector_data = nsepython_service.fetch_sector_data('NIFTY 50')

if sector_data and 'data' in sector_data:
    for stock in sector_data['data']:
        print(f"{stock['symbol']}: ₹{stock['lastPrice']}")
```

### Example 2: Fetch Stock Delivery Data

```python
from app.services import nsepython_service
from datetime import date, timedelta

# Fetch last 30 days delivery data
to_date = date.today()
from_date = to_date - timedelta(days=30)

delivery_df = nsepython_service.fetch_stock_delivery_data(
    'RELIANCE',
    from_date=from_date,
    to_date=to_date
)

if delivery_df is not None:
    print(f"Fetched {len(delivery_df)} records")
    print(delivery_df.head())
```

### Example 3: Fetch FII/DII Data

```python
from app.services import nsepython_service
from datetime import date

# Fetch today's FII/DII data
fii_dii = nsepython_service.fetch_fii_dii_data(date.today())

if fii_dii:
    print(f"FII/DII data: {fii_dii}")
```

## Integration with Existing Services

The nsepython service can be integrated with existing data fetching services:

### Update FII/DII Data Fetching

```python
# In fetch_fresh_market_data.py
from app.services import nsepython_service

def fetch_fii_dii_from_nse(target_date: date) -> dict:
    """Fetch FII/DII data using nsepython."""
    data = nsepython_service.fetch_fii_dii_data(target_date)
    if data:
        # Parse and return in expected format
        return {
            'fii_buy': data.get('fii_buy_value', 0),
            'fii_sell': data.get('fii_sell_value', 0),
            'dii_buy': data.get('dii_buy_value', 0),
            'dii_sell': data.get('dii_sell_value', 0),
        }
    return None
```

### Update Stock Data Fetching

```python
# In fetch_real_stocks.py
from app.services import nsepython_service

def fetch_stock_data_from_nse(ticker: str, from_date: date, to_date: date):
    """Fetch stock data using nsepython."""
    df = nsepython_service.fetch_stock_delivery_data(
        ticker, from_date, to_date
    )
    if df is not None:
        # Process and store in database
        return df
    return None
```

## Rate Limiting

NSE imposes rate limits on API requests. To avoid being blocked:

- **Maximum 3 requests per second**
- Add delays between requests (0.5-1 second)
- Use batch processing for multiple stocks
- Cache frequently accessed data

Example with rate limiting:

```python
import time
from app.services import nsepython_service

tickers = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY']

for ticker in tickers:
    quote = nsepython_service.fetch_stock_quote(ticker)
    time.sleep(0.5)  # Wait 0.5 seconds between requests
```

## Error Handling

Always wrap nsepython calls in try-except blocks:

```python
from app.services import nsepython_service
from app.utils import logger

try:
    data = nsepython_service.fetch_sector_data('NIFTY 50')
    if data:
        # Process data
        pass
except Exception as e:
    logger.error(f"Error fetching sector data: {e}")
    # Fallback to alternative data source
```

## Testing

Test the nsepython service:

```bash
docker compose exec backend python -m app.scripts.test_nsepython
```

## Troubleshooting

### Issue: "curl: not found"

**Solution:** curl is required by nsepython. It's already installed in the Docker container. If you see this error, restart the container:

```bash
docker compose restart backend
```

### Issue: "nsepython not available"

**Solution:** Install nsepythonserver:

```bash
docker compose exec backend pip install nsepythonserver
```

### Issue: Rate limiting / 403 errors

**Solution:** 
- Add delays between requests
- Reduce request frequency
- Use caching for frequently accessed data

### Issue: Data format mismatch

**Solution:** nsepython may return data in different formats. Always check the data structure:

```python
data = nsepython_service.fetch_stock_quote('RELIANCE')
if isinstance(data, dict):
    print(f"Keys: {list(data.keys())}")
```

## Next Steps

1. **Integrate with existing ETL scripts**: Update `fetch_fresh_market_data.py` to use nsepython for FII/DII data
2. **Add delivery data fetching**: Use `fetch_stock_delivery_data` in stock data ETL
3. **Add bulk/block deals**: Fetch and store bulk/block deals data
4. **Add options data**: Use `fetch_option_chain` for derivatives data

## References

- [nsepython Documentation](https://unofficed.com/nse-python/documentation/)
- [GitHub Repository](https://github.com/BennyThadikaran/NseIndiaApi)
- [NSE Official Website](https://www.nseindia.com/)

