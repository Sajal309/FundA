# Data Source Accuracy Analysis

This document analyzes each section/page of the application and recommends the most accurate data source for each use case.

## Data Sources Available

1. **NSE (via nsepython)** - Official National Stock Exchange data
   - ✅ Most accurate for Indian markets
   - ✅ Official exchange data
   - ✅ Free and reliable
   - ⚠️ Rate limited (3 requests/second)
   - ⚠️ May require session management

2. **Zerodha Kite Connect** - Broker API
   - ✅ Real-time data during market hours
   - ✅ High accuracy
   - ✅ WebSocket support for live updates
   - ⚠️ Requires trading account
   - ⚠️ May have slight delays (broker data, not exchange)

3. **yfinance** - Yahoo Finance
   - ✅ Easy to use
   - ✅ Good for international markets
   - ⚠️ Less accurate for Indian markets
   - ⚠️ May have data delays
   - ⚠️ Not official exchange data

---

## Section-by-Section Analysis

### 1. Stock Screener Page

**Data Required:**
- Stock fundamentals (P/E, P/B, ROE, ROCE, Debt/Equity)
- Current market price (CMP)
- Market capitalization
- Financial ratios
- Quarterly results
- Promoter holding, public holding
- Pledged percentage

**Current Source:** Database (from yfinance/mock data)

**Recommended Source:** **NSE (via nsepython)** ✅

**Reasoning:**
- Fundamentals data should come from official exchange filings
- NSE provides accurate company fundamentals
- More reliable than broker data for fundamentals
- Zerodha may not have all fundamental ratios
- yfinance is less accurate for Indian stocks

**Implementation:**
```python
# Use nsepython for:
- Stock quotes (current price)
- Company fundamentals (from NSE filings)
- Market cap calculations
```

**Priority:** HIGH - Fundamentals accuracy is critical for screening

---

### 2. Dashboard - Sector Performance

**Data Required:**
- Sector index prices (NIFTY 50, NIFTY BANK, etc.)
- Sector returns (1D, 1W, 1M)
- Sector valuations (PE ratios)
- Sector sentiment scores
- Sparkline charts

**Current Source:** Database (from yfinance/NSE)

**Recommended Source:** **NSE (via nsepython)** ✅

**Reasoning:**
- Sector indices are NSE official indices
- NSE is the authoritative source for index data
- Zerodha may have slight delays for index data
- yfinance may not have all NSE indices

**Implementation:**
```python
# Use nsepython for:
- Sector index data (fetch_sector_data)
- Index constituents
- Index historical data
```

**Priority:** HIGH - Index data must be accurate

---

### 3. Sector Rotation Page

#### 3.1 Breadth Tab

**Data Required:**
- Stock prices
- Moving averages (50DMA, 200DMA)
- % of stocks above/below moving averages
- 3-month highs/lows

**Recommended Source:** **NSE (via nsepython)** ✅

**Reasoning:**
- Need accurate stock prices for breadth calculations
- NSE provides official EOD prices
- More reliable than broker data for historical calculations

#### 3.2 Scores Tab (Momentum)

**Data Required:**
- Stock returns (1M, 3M, 6M)
- Market cap weighted returns
- Momentum scores

**Recommended Source:** **NSE (via nsepython)** ✅

**Reasoning:**
- Historical price data needed for returns
- NSE provides accurate historical data
- Market cap data from NSE is official

#### 3.3 Deliveries Tab

**Data Required:**
- Delivery volume
- Traded volume
- Delivery percentage
- Market cap

**Recommended Source:** **NSE (via nsepython)** ✅ **PRIMARY**

**Reasoning:**
- **NSE is the ONLY official source for delivery data**
- Delivery data is exchange-specific
- Zerodha may not provide delivery data
- yfinance doesn't have delivery data
- Critical: Delivery data must be from NSE

**Implementation:**
```python
# Use nsepython fetch_stock_delivery_data() for:
- Delivery volume
- Tradable volume
- Delivery percentage
```

**Priority:** CRITICAL - Delivery data only available from NSE

#### 3.4 VWAP Tab

**Data Required:**
- Volume-weighted average price (VWAP)
- Current price vs VWAP
- Market cap weighted metrics

**Recommended Source:** **NSE (via nsepython)** ✅

**Reasoning:**
- VWAP calculations need accurate volume data
- NSE provides official volume data
- More accurate than broker data

---

### 4. Market Sentiment

**Data Required:**
- India VIX
- Index PCR (Put-Call Ratio)
- Breadth (Nifty 500 above 50DMA)
- News sentiment

**Recommended Source:** **Mixed**

**Breakdown:**
- **India VIX:** yfinance ✅ (^INDIAVIX ticker works well)
- **Index PCR:** NSE (via nsepython) ✅ (from options data)
- **Breadth:** NSE (via nsepython) ✅ (from stock data)
- **News Sentiment:** NewsAPI ✅ (already implemented)

**Reasoning:**
- VIX: yfinance has reliable India VIX data
- PCR: Must come from NSE options data
- Breadth: Needs NSE stock data for accurate calculation

**Priority:** MEDIUM - Mixed sources work well

---

### 5. FII/DII Data

**Data Required:**
- FII buy/sell values
- DII buy/sell values
- Net flows
- Sector-wise flows

**Recommended Source:** **NSE (via nsepython)** ✅ **PRIMARY**

**Reasoning:**
- **NSE is the official source for FII/DII data**
- Published daily on NSE website
- Most accurate and authoritative
- Zerodha doesn't provide this data
- yfinance doesn't have this data

**Implementation:**
```python
# Use nsepython fetch_fii_dii_data() for:
- Daily FII/DII flows
- Aggregate and sector-wise flows
```

**Priority:** CRITICAL - Only NSE has official FII/DII data

---

### 6. Options Data

**Data Required:**
- Option chain
- Open Interest (OI)
- PCR (Put-Call Ratio)
- Implied Volatility (IV)

**Recommended Source:** **Zerodha Kite Connect** ✅ **PRIMARY**

**Reasoning:**
- Zerodha provides comprehensive options data
- Real-time OI updates
- Better API for options than NSE
- NSE options data may be limited via nsepython

**Fallback:** NSE (via nsepython) for basic option chain

**Priority:** HIGH - Options data critical for derivatives analysis

---

### 7. Live Stock Quotes

**Data Required:**
- Real-time stock prices
- Volume
- Bid/Ask
- Last traded price

**Recommended Source:** **Zerodha Kite Connect** ✅ **PRIMARY** (during market hours)

**Reasoning:**
- Real-time data during market hours
- WebSocket support for live updates
- Lower latency than NSE API
- Better for live trading scenarios

**Fallback:** NSE (via nsepython) for EOD data

**Priority:** MEDIUM - Real-time needed for live quotes

---

### 8. Historical Stock Data

**Data Required:**
- OHLCV data
- Historical prices
- Volume data

**Recommended Source:** **NSE (via nsepython)** ✅ **PRIMARY**

**Reasoning:**
- Official exchange data
- Most accurate historical records
- Complete data set
- Better than broker data for historical analysis

**Fallback:** Zerodha Kite Connect (if NSE unavailable)

**Priority:** HIGH - Historical accuracy important

---

## Summary Table

| Section | Primary Source | Secondary Source | Reason |
|---------|---------------|------------------|--------|
| **Stock Screener** | NSE (nsepython) | Zerodha | Official fundamentals |
| **Sector Performance** | NSE (nsepython) | yfinance | Official index data |
| **Sector Rotation - Breadth** | NSE (nsepython) | Zerodha | Accurate stock prices |
| **Sector Rotation - Scores** | NSE (nsepython) | Zerodha | Historical returns |
| **Sector Rotation - Deliveries** | NSE (nsepython) | ❌ None | ONLY NSE has this |
| **Sector Rotation - VWAP** | NSE (nsepython) | Zerodha | Official volume data |
| **Market Sentiment - VIX** | yfinance | NSE | Works well |
| **Market Sentiment - PCR** | NSE (nsepython) | Zerodha | From options |
| **Market Sentiment - Breadth** | NSE (nsepython) | Zerodha | Stock data |
| **FII/DII Data** | NSE (nsepython) | ❌ None | ONLY NSE has this |
| **Options Data** | Zerodha Kite | NSE | Better API |
| **Live Quotes** | Zerodha Kite | NSE | Real-time |
| **Historical Data** | NSE (nsepython) | Zerodha | Official records |

---

## Implementation Priority

### Phase 1: Critical (NSE-only data)
1. ✅ **FII/DII Data** - Switch to nsepython
2. ✅ **Delivery Data** - Switch to nsepython
3. ✅ **Sector Index Data** - Switch to nsepython

### Phase 2: High Priority (Accuracy improvements)
4. **Stock Fundamentals** - Switch to NSE
5. **Historical Stock Data** - Switch to NSE
6. **Sector Rotation Calculations** - Use NSE data

### Phase 3: Medium Priority (Real-time features)
7. **Live Quotes** - Use Zerodha for real-time
8. **Options Data** - Use Zerodha for comprehensive data

### Phase 4: Low Priority (Already working)
9. **Market Sentiment VIX** - Keep yfinance
10. **News Sentiment** - Keep NewsAPI

---

## Migration Strategy

### Step 1: Update FII/DII Data Fetching
```python
# In fetch_fresh_market_data.py
from app.services import nsepython_service

def fetch_fii_dii_from_nse(target_date: date) -> dict:
    data = nsepython_service.fetch_fii_dii_data(target_date)
    # Parse and store
```

### Step 2: Update Delivery Data Fetching
```python
# In fetch_real_stocks.py or sector_rotation_etl.py
from app.services import nsepython_service

def fetch_delivery_data(ticker: str, from_date: date, to_date: date):
    df = nsepython_service.fetch_stock_delivery_data(ticker, from_date, to_date)
    # Process and store
```

### Step 3: Update Sector Data Fetching
```python
# In fetch_real_sector_rotation_data.py
from app.services import nsepython_service

def fetch_sector_index_data(sector_id: str):
    data = nsepython_service.fetch_sector_data(sector_id)
    # Process and store
```

### Step 4: Update Stock Fundamentals
```python
# In fetch_stock_fundamentals.py
from app.services import nsepython_service

def fetch_fundamentals_from_nse(ticker: str):
    quote = nsepython_service.fetch_stock_quote(ticker)
    # Extract fundamentals from quote data
```

---

## Notes

1. **Rate Limiting:** NSE has a 3 requests/second limit. Implement delays between requests.

2. **Fallback Strategy:** Always have Zerodha/yfinance as fallback if NSE fails.

3. **Data Validation:** Cross-check critical data points between sources when possible.

4. **Caching:** Cache NSE data to reduce API calls and improve performance.

5. **Error Handling:** Implement robust error handling for each data source.

---

## Conclusion

**NSE (via nsepython) should be the PRIMARY source for:**
- ✅ Stock fundamentals
- ✅ Sector/index data
- ✅ Delivery data (CRITICAL - only NSE has this)
- ✅ FII/DII data (CRITICAL - only NSE has this)
- ✅ Historical stock data
- ✅ VWAP calculations

**Zerodha Kite Connect should be used for:**
- ✅ Real-time quotes (during market hours)
- ✅ Options data (better API)
- ✅ WebSocket live updates

**yfinance should be used for:**
- ✅ India VIX (works well)
- ✅ International market data

This strategy ensures maximum accuracy while leveraging the strengths of each data source.

