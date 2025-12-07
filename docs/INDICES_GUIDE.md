# Comprehensive Market Indices Guide

This document lists all supported market indices in the SectorView platform and provides guidance on data ingestion.

## Overview

The platform now supports **30+ market indices** covering:
- **Broad Market Indices** (Nifty 50, 100, 200, 500, Midcap, Smallcap)
- **Sectoral Indices** (Banking, IT, Pharma, Auto, Energy, etc.)
- **Thematic Indices** (Quality, Dividend, Growth, Low Volatility, etc.)

## Supported Indices

### 📊 Broad Market Indices

| Sector ID | Display Name | NSE Symbol |
|-----------|--------------|------------|
| `NIFTY_50` | Nifty 50 | NIFTY 50 |
| `NIFTY_NEXT_50` | Nifty Next 50 | NIFTY NEXT 50 |
| `NIFTY_100` | Nifty 100 | NIFTY 100 |
| `NIFTY_200` | Nifty 200 | NIFTY 200 |
| `NIFTY_500` | Nifty 500 | NIFTY 500 |
| `NIFTY_MIDCAP_50` | Nifty Midcap 50 | NIFTY MIDCAP 50 |
| `NIFTY_MIDCAP_100` | Nifty Midcap 100 | NIFTY MIDCAP 100 |
| `NIFTY_MIDCAP_150` | Nifty Midcap 150 | NIFTY MIDCAP 150 |
| `NIFTY_SMALLCAP_50` | Nifty Smallcap 50 | NIFTY SMALLCAP 50 |
| `NIFTY_SMALLCAP_100` | Nifty Smallcap 100 | NIFTY SMALLCAP 100 |
| `NIFTY_SMALLCAP_250` | Nifty Smallcap 250 | NIFTY SMALLCAP 250 |

### 🏭 Sectoral Indices

| Sector ID | Display Name | NSE Symbol |
|-----------|--------------|------------|
| `NIFTY_BANK` | Nifty Bank | NIFTY BANK |
| `NIFTY_IT` | Nifty IT | NIFTY IT |
| `NIFTY_FMCG` | Nifty FMCG | NIFTY FMCG |
| `NIFTY_PHARMA` | Nifty Pharma | NIFTY PHARMA |
| `NIFTY_AUTO` | Nifty Auto | NIFTY AUTO |
| `NIFTY_ENERGY` | Nifty Energy | NIFTY ENERGY |
| `NIFTY_METAL` | Nifty Metal | NIFTY METAL |
| `NIFTY_REALTY` | Nifty Realty | NIFTY REALTY |
| `NIFTY_PSU_BANK` | Nifty PSU Bank | NIFTY PSU BANK |
| `NIFTY_PRIVATE_BANK` | Nifty Private Bank | NIFTY PRIVATE BANK |
| `NIFTY_FIN_SERVICE` | Nifty Financial Services | NIFTY FINANCIAL SERVICES |
| `NIFTY_HEALTHCARE` | Nifty Healthcare | NIFTY HEALTHCARE |
| `NIFTY_CONSUMER_DURABLES` | Nifty Consumer Durables | NIFTY CONSUMER DURABLES |
| `NIFTY_INFRA` | Nifty Infrastructure | NIFTY INFRASTRUCTURE |
| `NIFTY_OIL_GAS` | Nifty Oil & Gas | NIFTY OIL & GAS |
| `NIFTY_PSE` | Nifty PSE | NIFTY PSE |
| `NIFTY_SERVICES` | Nifty Services | NIFTY SERVICES |
| `NIFTY_COMMODITIES` | Nifty Commodities | NIFTY COMMODITIES |

### 🎯 Thematic Indices

| Sector ID | Display Name | NSE Symbol |
|-----------|--------------|------------|
| `NIFTY_GROWTH_SECTORS_15` | Nifty Growth Sectors 15 | NIFTY GROWTH SECTORS 15 |
| `NIFTY_DIVIDEND_OPPORTUNITIES_50` | Nifty Dividend Opportunities 50 | NIFTY DIVIDEND OPPORTUNITIES 50 |
| `NIFTY_QUALITY_30` | Nifty Quality 30 | NIFTY QUALITY 30 |
| `NIFTY_LOW_VOLATILITY_50` | Nifty Low Volatility 50 | NIFTY LOW VOLATILITY 50 |
| `NIFTY_ALPHA_50` | Nifty Alpha 50 | NIFTY ALPHA 50 |
| `NIFTY_HIGH_BETA_50` | Nifty High Beta 50 | NIFTY HIGH BETA 50 |

## Data Ingestion

### Option 1: Using the Helper Script

A helper script is provided to fetch data for all indices:

```bash
# List all supported indices
python -m app.scripts.ingest_all_indices --list

# Fetch data for a specific index
python -m app.scripts.ingest_all_indices --fetch-yfinance --sector NIFTY_50 --days 365

# Fetch data for all indices
python -m app.scripts.ingest_all_indices --fetch-all-yfinance --days 365
```

### Option 2: Manual CSV Ingestion

1. Prepare CSV files with the following format:
   ```csv
   sector_id,ts,open,high,low,close,volume
   NIFTY_50,2024-01-01 09:15:00,21000.0,21100.0,20950.0,21050.0,1000000
   ```

2. Place CSV files in `sample_data/` directory

3. Run ingestion:
   ```bash
   python -m app.services.ingestion ingest_from_csv sample_data/nifty_50_timeseries.csv
   ```

### Option 3: Using yfinance Directly

```python
import yfinance as yf
import pandas as pd

# Fetch Nifty 50 data
ticker = yf.Ticker("^NSEI")
hist = ticker.history(period="1y")

# Format and save
hist.reset_index(inplace=True)
hist['sector_id'] = 'NIFTY_50'
hist['ts'] = hist['Date']
# ... format columns and save to CSV
```

## Options Data Mapping

For derivatives sentiment analysis, indices are mapped to option underlyings:

- **NIFTY-based indices** → `NIFTY` options
- **Banking indices** (Bank, PSU Bank, Private Bank, Financial Services) → `BANKNIFTY` options
- **All other indices** → `NIFTY` options (default)

## Sentiment Keywords

Each index has associated keywords for news sentiment analysis. The system automatically tags news articles to relevant indices based on these keywords.

## API Usage

All indices are automatically available through the standard API endpoints:

```bash
# Get all sectors (includes all indices)
GET /api/v1/sectors

# Get specific index forecast
GET /api/v1/sectors/NIFTY_50/forecast

# Get Quarter Outlook ranking (includes all indices)
GET /api/v1/sectors/quarter-outlook

# Get breadth metrics (includes all indices)
GET /api/v1/breadth
```

## Notes

- Indices are dynamically discovered from the database based on available time series data
- If an index doesn't have data yet, it won't appear in API responses
- The system gracefully handles missing data for breadth, valuations, and other metrics
- All indices support QuarterScore computation once features are computed

## Next Steps

1. **Ingest Historical Data**: Use the helper script or manual CSV ingestion to populate time series data
2. **Run Daily ETL**: Once data is ingested, run the daily ETL to compute features and forecasts
3. **Verify in Frontend**: Check the dashboard to see all indices appear in rankings and comparisons

