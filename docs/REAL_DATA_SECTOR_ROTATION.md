# Real Data Integration for Sector Rotation

## Overview
The Sector Rotation feature now uses **real market data** from live APIs to provide accurate analytics and insights.

## Data Sources

### 1. Stock Price Data - yfinance ✅
- **Source**: Yahoo Finance (yfinance library)
- **Coverage**: Major NSE stocks across all sectors
- **Data Points**: OHLCV (Open, High, Low, Close, Volume)
- **History**: Up to 365 days of historical data
- **Update Frequency**: Daily

### 2. Technical Indicators - Calculated ✅
- **SMA20/50/100**: Simple Moving Averages
- **RSI14**: Relative Strength Index (14-period)
- **RS55**: 55-day Relative Strength vs Nifty 50
- **Returns**: 1M, 3M, 6M returns
- **VWAP**: Volume Weighted Average Price

### 3. Market Data - Kite Connect (Optional) 🔄
- **Source**: Zerodha Kite Connect API
- **Coverage**: Options data, OI, IV
- **Status**: Available when access token is configured

## How to Fetch Real Data

### Quick Start
```bash
# Fetch real data for all sectors (180 days history)
docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --days 180

# Fetch for specific sector
docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --sector NIFTY_BANK --days 180

# Skip data fetch, only calculate indicators
docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --skip-fetch

# Only run ETL aggregation
docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --skip-fetch --skip-indicators
```

### Step-by-Step Process

1. **Fetch Stock Data**
   ```bash
   docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --days 180 --skip-indicators --skip-etl
   ```
   - Fetches OHLCV data from yfinance
   - Stores in `stock_time_series` table
   - Creates stock records if they don't exist

2. **Calculate Market Caps**
   - Automatically calculated from price × shares outstanding
   - Stored in `stock_market_caps` table

3. **Calculate Technical Indicators**
   ```bash
   docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --skip-fetch --skip-etl
   ```
   - Calculates SMA, RSI, RS55, returns, VWAP
   - Stores in `stock_technical_indicators` table

4. **Calculate Rolling Statistics**
   - 20-day averages for traded value and delivery value
   - Stored in `stock_rolling_stats` table

5. **Run ETL Aggregation**
   ```bash
   docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --skip-fetch --skip-indicators
   ```
   - Aggregates stock-level data to sector/industry level
   - Creates breadth snapshots, momentum scores, delivery stats, VWAP snapshots

## Supported Sectors

The system fetches data for major stocks in:

- **NIFTY_BANK**: HDFCBANK, ICICIBANK, SBIN, KOTAKBANK, AXISBANK, etc.
- **NIFTY_IT**: TCS, INFY, WIPRO, HCLTECH, TECHM, etc.
- **NIFTY_PHARMA**: SUNPHARMA, DRREDDY, CIPLA, LUPIN, etc.
- **NIFTY_FMCG**: HINDUNILVR, ITC, NESTLEIND, BRITANNIA, etc.
- **NIFTY_AUTO**: MARUTI, M&M, TATAMOTORS, BAJAJ-AUTO, etc.
- **NIFTY_ENERGY**: RELIANCE, ONGC, IOC, BPCL, etc.
- **NIFTY_METAL**: TATASTEEL, JSWSTEEL, SAIL, VEDL, etc.
- **NIFTY_REALTY**: DLF, GODREJPROP, OBEROIRLTY, etc.
- **NIFTY_50**: Top 10 stocks from Nifty 50

## Data Quality

### Handling Missing Data
- Stocks that are delisted or unavailable are skipped with a warning
- Missing dates are handled gracefully
- Indicators are only calculated when sufficient data is available (minimum 100 days)

### Data Validation
- Duplicate records are automatically skipped
- Existing data is preserved (won't overwrite)
- Market caps are recalculated from latest prices

## Analytics Features

With real data, the Sector Rotation feature provides:

1. **Breadth Analysis**
   - Real percentage of stocks meeting technical conditions
   - Market-cap weighted and count-based metrics
   - RS55, RSI, SMA20/50/100 filters

2. **Momentum Scores**
   - Actual 1M, 3M, 6M returns
   - Normalized to 0-100 scale
   - Color-coded for quick identification

3. **Delivery Statistics**
   - Real traded and delivery values
   - 20-day averages and multiples
   - Market cap changes

4. **VWAP Analysis**
   - Actual VWAP calculations
   - Price vs VWAP percentages
   - Market-cap weighted metrics

## Daily Updates

To keep data fresh, run daily:

```bash
# Add to cron or scheduled task
docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --days 1
```

This will:
1. Fetch latest day's data for all stocks
2. Recalculate indicators
3. Update aggregations

## Troubleshooting

### No Data Returned
- Check internet connection
- Verify yfinance is installed: `pip install yfinance`
- Some stocks may be delisted (check logs)

### Missing Indicators
- Ensure at least 100 days of price data exists
- Check that Nifty 50 data is available for RS55 calculation
- Verify database has sufficient data

### ETL Errors
- Ensure stock data exists before running ETL
- Check that technical indicators are calculated
- Verify market caps are populated

## Performance

- **Fetch Speed**: ~1-2 seconds per stock
- **Indicator Calculation**: ~0.5 seconds per stock per date
- **ETL Aggregation**: ~1 second per sector
- **Total Time**: ~5-10 minutes for full pipeline (all sectors, 180 days)

## Next Steps

1. **Expand Coverage**: Add more stocks per sector
2. **Real-time Updates**: Integrate with Kite Connect for live data
3. **Advanced Indicators**: Add more technical indicators (MACD, Bollinger Bands, etc.)
4. **Industry Level**: Extend to industry-level aggregations
5. **Historical Backtesting**: Use historical data for strategy validation

