# Stock Fundamentals ETL Guide

## Overview

This guide explains how to populate the `stock_fundamentals` table with data for the Stock Screener feature.

## Script: `fetch_stock_fundamentals.py`

Located at: `backend/app/scripts/fetch_stock_fundamentals.py`

### Features

- Fetches fundamentals from yfinance (limited data for Indian stocks)
- Generates mock data for testing
- Supports single ticker, sector, or all stocks
- Handles missing data gracefully

### Usage

#### 1. Fetch for All Stocks (Mock Data - Recommended for Testing)

```bash
# Using Docker
docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --all --mock

# Or locally
cd backend
python -m app.scripts.fetch_stock_fundamentals --all --mock
```

This will:
- Generate realistic mock fundamentals for all stocks in the database
- Sector-specific values (e.g., banks get NPA metrics, IT gets FCF)
- Store data with today's date

#### 2. Fetch for Specific Sector

```bash
# Mock data for banks sector
docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --sector NIFTY_BANK --mock

# Real data from yfinance (limited)
docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --sector NIFTY_IT
```

#### 3. Fetch for Single Stock

```bash
# Mock data
docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --ticker HDFCBANK --mock

# Real data from yfinance
docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --ticker TCS
```

#### 4. Limit Number of Stocks

```bash
# Process only first 10 stocks
docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --all --mock --limit 10
```

#### 5. Specify Date

```bash
# Use specific date
docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --all --mock --date 2024-01-31
```

### Options

- `--ticker <TICKER>`: Fetch for specific stock ticker
- `--sector <SECTOR_ID>`: Fetch for all stocks in sector (e.g., NIFTY_BANK)
- `--all`: Fetch for all stocks in database
- `--mock`: Use mock data instead of real API calls
- `--limit <N>`: Limit number of stocks to process
- `--date <YYYY-MM-DD>`: As of date (defaults to today)

### Data Sources

#### 1. yfinance (Limited)

**Pros:**
- Free, no API key needed
- Basic metrics available (market cap, P/E, margins)

**Cons:**
- Limited fundamental data for Indian stocks
- Many fields missing (NPA, CASA, etc.)
- Rate limiting

**Usage:**
```bash
# Without --mock flag, tries yfinance first
docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --ticker TCS
```

#### 2. Mock Data (Recommended for Testing)

**Pros:**
- Complete data for all fields
- Sector-specific realistic values
- Fast, no API calls
- Good for development/testing

**Cons:**
- Not real data
- Values are randomly generated within ranges

**Usage:**
```bash
# Always use --mock flag
docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --all --mock
```

#### 3. Screener.in (Future)

For production, you may want to integrate with Screener.in or other data providers:

1. **Web Scraping** (check ToS first):
   - Scrape Screener.in company pages
   - Extract fundamental metrics
   - Store in database

2. **API Integration**:
   - Use paid fundamentals APIs
   - Set up scheduled ETL jobs
   - Update data daily/weekly

### Mock Data Ranges

The script generates realistic values based on sector:

**Banks:**
- ROA: 1.0 - 2.5%
- NIM: 3.0 - 5.0%
- GNPA: 0.5 - 3.0%
- NNPA: 0.2 - 1.0%
- PCR: 70 - 90%
- CASA: 35 - 50%
- CAR: 15 - 20%

**IT:**
- ROE: 18 - 30%
- ROCE: 20 - 35%
- EBIT Margin: 18 - 25%
- Profit Growth 5Y: 12 - 20%
- FCF: 1000 - 10000 Cr
- D/E: 0.1 - 0.3

**Pharma:**
- ROCE: 15 - 25%
- ROE: 15 - 25%
- R&D to Sales: 5 - 12%
- Sales Growth 5Y: 10 - 20%
- Export Share: 40 - 70%
- D/E: 0.2 - 0.4

**Generic:**
- ROE: 15 - 25%
- ROCE: 15 - 25%
- Operating Margin: 12 - 20%
- Sales Growth 5Y: 8 - 18%
- D/E: 0.3 - 0.8

### Testing the Screener

After populating data:

1. **Start the application:**
   ```bash
   docker compose up
   ```

2. **Navigate to Stock Screener:**
   - Go to http://localhost:3000/stock-screener
   - Select a sector (e.g., "Banks")
   - View screened stocks

3. **Test Export:**
   - Click "Export CSV" button
   - Verify CSV download

4. **Test Comparison:**
   - Go to http://localhost:3000/sector-comparison
   - Select multiple sectors
   - Compare top stocks

### Troubleshooting

**No stocks found:**
- Check if stocks exist in `stocks` table
- Verify `sector_id` is set correctly
- Run: `SELECT * FROM stocks LIMIT 10;`

**No fundamentals data:**
- Run the ETL script: `--all --mock`
- Check `stock_fundamentals` table: `SELECT COUNT(*) FROM stock_fundamentals;`
- Verify date matches: `SELECT DISTINCT date FROM stock_fundamentals ORDER BY date DESC;`

**Import errors:**
- Ensure you're in the correct directory
- Check Python path: `python -c "import app; print(app.__file__)"`
- Use Docker if local setup fails

### Next Steps

1. **Populate Data:**
   ```bash
   docker compose exec backend python -m app.scripts.fetch_stock_fundamentals --all --mock
   ```

2. **Verify Data:**
   ```bash
   docker compose exec backend python -c "from app.db import database, models; db = next(database.get_db()); print(f'Fundamentals records: {db.query(models.StockFundamentals).count()}')"
   ```

3. **Test Screener:**
   - Open http://localhost:3000/stock-screener
   - Select a sector and verify results

4. **Production Data:**
   - Integrate with Screener.in or paid API
   - Set up scheduled ETL jobs
   - Update data daily/weekly

