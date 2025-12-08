# SectorView Cleanup Plan

## Overview
Clean up and align the product with the original intent: **"Single view that helps understand which Nifty sectors will perform better over the next quarter, with context from flows, macro, breadth, volatility and sentiment."**

## Current State Analysis

### Endpoints Identified

#### Market Sentiment
- **Endpoint**: `GET /api/v1/forecasts/market-sentiment`
- **Location**: `backend/app/api/v1/forecasts.py`
- **Returns**: VIX, PCR, breadth, news sentiment, regime label
- **Issue**: Returns long rule strings that should be hidden

#### Quarter Outlook Ranking
- **Endpoint**: `GET /api/v1/forecasts/sectors/quarter-outlook`
- **Location**: `backend/app/api/v1/forecasts.py`
- **Returns**: Sectors sorted by quarter_score
- **Issue**: All sectors show "Weak" - likely placeholder logic

#### Breadth & Leadership
- **Endpoint**: `GET /api/v1/sectors/breadth`
- **Location**: `backend/app/api/v1/sectors.py`
- **Returns**: Breadth metrics for all sectors
- **Issue**: Shows many indices (Nifty 100, 200, PSE, etc.) and many 100% values

#### Volatility Heatmap
- **Endpoint**: Likely uses sector features or volatility daily table
- **Issue**: Vol values (e.g. 107%) look wrong for 30-day annualised vol, too many indices

#### Sector Comparison & Correlation
- **Endpoints**: 
  - `GET /api/v1/analytics/correlations` - Correlation matrix
  - `GET /api/v1/analytics/sectors/compare` - Sector comparison
- **Location**: `backend/app/api/v1/analytics.py`
- **Issue**: Full 10×10 matrix is visually heavy, too many selectable indices

#### Earnings Watch
- **Endpoint**: `GET /api/v1/earnings/earnings-watch`
- **Location**: `backend/app/api/v1/earnings.py`
- **Issue**: Shows "No upcoming events" / blank revision heatmap

### Database Tables Identified

- `sector_features` - Computed daily features (includes quarter_score)
- `sector_forecasts` - 3-month forecasts (includes quarter_score, drivers)
- `market_sentiment_daily` - Market sentiment indicators
- `sector_breadth_daily` - Breadth metrics per sector
- `sector_volatility_daily` - Volatility metrics (if exists, or computed from features)
- `sector_valuations_daily` - Valuation metrics
- `earnings_events` - Earnings events and revisions
- `news_headlines` - News with sentiment scores
- `sector_sentiment_daily` - Aggregated sentiment by sector

## Implementation Plan

### STEP 0 - Recon, assumptions & config ✅ COMPLETE
- [x] Inspect backend and frontend code
- [x] Document endpoints and DB tables
- [x] Create canonical sector list in `config/sectors.yaml`
- [x] Create cleanup plan document

### STEP 1 - Fix Market Sentiment banner ✅ COMPLETE
**Backend:**
- ✅ `/api/v1/forecasts/market-sentiment` already returns correct data (no rule text)
- ✅ Returns: date, regime_label, india_vix, put_call_ratio, breadth_nifty500_above_50dma, news_sentiment_score_7d

**Frontend:**
- ✅ Removed long inline rule explanation text
- ✅ Kept regime pill (colored: green/yellow/red)
- ✅ Show 4 key metrics as cards
- ✅ Added tooltips for each metric (1-2 line explanation)

### STEP 2 - Clean up Sector Correlation & Comparison ✅ COMPLETE
**Backend:**
- Add `GET /api/v1/sectors/top-correlations` endpoint
- Returns top positive/negative correlations only
- Ensure comparison endpoint returns 3M and 6M relative returns vs Nifty

**Frontend:**
- Collapse full matrix behind "Show Correlation Matrix (Advanced)" toggle
- Add compact list of top 3 positive/negative correlations
- Limit selectable items to canonical sectors only
- Limit selection to max 3 sectors
- Default metric to 3M return
- Hide 1D/5D in default view

### STEP 3 - Proper QuarterScore & Quarter Outlook Ranking ✅ COMPLETE
**Backend:**
- Create/extend `services/quarter_score.py` with proper computation
- Use 7 pillars: momentum, breadth, flows, earnings, valuation, sentiment, macro
- Normalize each component to -1...+1
- Apply configurable weights from `config/quarter_weights.yaml`
- Store quarter_score in sector_features
- Include QuarterScore and contributions in sector_forecasts.drivers
- Update `/api/v1/forecasts/sectors/quarter-outlook` to return proper labels

**Frontend:**
- Replace "Weak" placeholders with real labels from QuarterScore
- Show numeric score in subtext/badge
- Order sectors descending by QuarterScore
- Driver Card modal: show breakdown of 7 pillars with contributions

### STEP 4 - Simplify Breadth & Leadership ✅ COMPLETE
**Backend:**
- Ensure `GET /api/v1/sectors/breadth` only returns canonical sectors
- Remove Nifty50/100/200/PSE indices from this endpoint
- Add unit tests for breadth calculations

**Frontend:**
- Show only canonical sectors in Breadth & Leadership card
- Remove Nifty50/100/200, PSE, etc. from panel
- Keep "Breadth Comparison" bar chart for canonical sectors only

### STEP 5 - Simplify Volatility Heatmap ✅ COMPLETE
**Backend:**
- Check volatility computation (30-day window, annualised correctly)
- Verify typical vols ~15-40%
- Ensure endpoint returns only canonical sectors
- Map volatility to categories: Low/Medium/High/Very High

**Frontend:**
- Replace tiles with one per canonical sector
- Use corrected values & categories
- Remove Nifty 100/200, PSE, PSU tiles

### STEP 6 - Fix Earnings Watch ✅ COMPLETE
**Backend:**
- Add logic in `earnings_service.py` to aggregate earnings_events
- Compute EPS upgrade/downgrade percentages
- Expose via `GET /api/v1/earnings/earnings-watch`
- Create mock data generator if real data not available

**Frontend:**
- Update "Upcoming results" table
- Show revision heatmap with greens/reds
- Display "No corporate earnings data yet" if truly no data

### STEP 7 - Clean Latest News & sentiment ✅ COMPLETE
**Backend:**
- Ensure `GET /api/v1/news/latest` only returns finance/market/sector headlines
- Attach sector_tags and sentiment_score for each headline

**Frontend:**
- Show only: Headline, Source + time, Sector tag (badge), Sentiment label
- Add filter row ("All sectors / IT / Auto / Pharma / ...")
- Remove generic non-market headlines

### STEP 8 - Tests, docs & visual polish
- Add unit tests for:
  - compute_quarter_score
  - Breadth calculation
  - Volatility calculation
  - Market sentiment regime classification
- Update README.md with:
  - Canonical sector list
  - QuarterScore explanation
  - Market Regime, Breadth, Volatility meanings
- UI polish:
  - Consistent titles and tooltips
  - Clean layout on laptop screens

## Notes
- Do not remove existing endpoints; extend or hide things at UI level where possible
- Where live data is not available, create mock data that passes the same schema
- Keep code style consistent with existing formatting

