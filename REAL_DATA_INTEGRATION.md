# Real Data Integration Guide

This document describes how to integrate real data sources into SectorView.

## Available Integrations

### 1. Macro Data - yfinance (✅ Implemented)

**No API key required** - Free and open source.

**Usage:**
```bash
# Fetch macro data (USD/INR, Brent, Gold, US 10Y)
docker compose exec backend python -m app.fetch_real_data --macro --days 30
```

**What it fetches:**
- USD/INR exchange rate (`INR=X`)
- Brent Crude futures (`CL=F`)
- Gold futures (`GC=F`)
- US 10Y Treasury yield (`^TNX`)

**Installation:**
```bash
pip install yfinance
# Or it's already in requirements.txt
```

### 2. News Data - NewsAPI (✅ Implemented)

**Requires free API key** from https://newsapi.org/

**Usage:**
```bash
# Set API key
export NEWSAPI_KEY=c7e83904e13941eea773235bea1fa29b

# Fetch news
docker compose exec backend python -m app.fetch_real_data --news --days 7
```

**What it fetches:**
- News headlines related to Indian markets
- Automatic sentiment scoring
- Sector tagging

**Get API Key:**
1. Sign up at https://newsapi.org/
2. Free tier: 100 requests/day
3. Set environment variable: `NEWSAPI_KEY=your_key`

### 3. NSE Data - NSE India (🔄 Placeholder)

**Status:** Basic structure implemented, needs NSE API access

**Current Implementation:**
- `backend/app/services/fetch_nse.py` has the structure
- NSE's public APIs have rate limits and may require authentication
- For production, consider:
  - NSE's official data vendors
  - Kite Connect (Zerodha) for authorized access
  - Paid data providers

**What it would fetch:**
- Historical index data (NIFTY sectors)
- FII/DII flow data
- Real-time quotes (with proper API access)

### 4. Options Data - Kite Connect (🔄 Stub)

**Status:** Stub implementation ready

**Requirements:**
- Zerodha Kite Connect API key
- Requires Zerodha trading account

**To implement:**
1. Install: `pip install kiteconnect`
2. Get API key from Zerodha
3. Update `backend/app/services/ingest_options.py` to use Kite API

**What it would fetch:**
- Option chain data
- Open Interest (OI)
- Implied Volatility (IV)
- Put-Call Ratios

## Integration Workflow

### Daily ETL with Real Data

1. **Fetch Macro Data:**
```bash
docker compose exec backend python -m app.fetch_real_data --macro --days 30
```

2. **Fetch News:**
```bash
export NEWSAPI_KEY=your_key
docker compose exec backend python -m app.fetch_real_data --news --days 7
```

3. **Run Full ETL:**
```bash
docker compose exec backend python -m app.run_daily_etl
```

### Environment Variables

Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql://postgres:password@db:5432/sectorview

# API Keys
NEWSAPI_KEY=c7e83904e13941eea773235bea1fa29b
KITE_API_KEY=2pl8jdm3kobxu007  # When implementing Kite
KITE_API_SECRET=your_kite_secret_here

# Optional
ALCHEMY_ECHO=false
```

## Data Source Priority

For production, recommended data sources:

1. **EOD Sector Data:**
   - Primary: NSE official APIs or authorized vendors
   - Fallback: Kite Connect (if you have account)

2. **Macro Data:**
   - Primary: yfinance (free, reliable)
   - Alternative: Alpha Vantage (requires API key)

3. **News:**
   - Primary: NewsAPI (free tier available)
   - Alternative: Google News RSS (scraping, beware TOS)

4. **Options:**
   - Primary: Kite Connect (requires Zerodha account)
   - Alternative: Dhan API or other broker APIs

5. **FII/DII Flows:**
   - Primary: NSE official reports
   - Alternative: NSDL/CDSL reports

## Rate Limits & Best Practices

1. **yfinance:** No official limit, but be respectful (1 request/second)
2. **NewsAPI:** 100 requests/day (free tier)
3. **NSE:** Rate limits apply, use caching
4. **Kite Connect:** Check Zerodha's rate limits

**Best Practices:**
- Cache API responses
- Use exponential backoff for retries
- Store raw data for audit
- Run ETL during off-market hours
- Monitor API usage

## Testing Real Data Integration

```bash
# Test macro data fetch
docker compose exec backend python -m app.fetch_real_data --macro --days 7

# Test news fetch (requires API key)
export NEWSAPI_KEY=test_key
docker compose exec backend python -m app.fetch_real_data --news --days 1

# Verify data
docker compose exec db psql -U postgres -d sectorview -c "SELECT COUNT(*) FROM macro_daily;"
docker compose exec db psql -U postgres -d sectorview -c "SELECT COUNT(*) FROM news_headlines;"
```

## Next Steps

1. ✅ yfinance integration - DONE
2. ✅ NewsAPI integration - DONE
3. 🔄 NSE API - Needs proper API access
4. 🔄 Kite Connect - Needs Zerodha account setup
5. 🔄 Alpha Vantage - Optional for macro data backup

