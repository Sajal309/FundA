# Quarter Outlook + Sentiment Platform - Implementation Roadmap

## Overview
This document tracks the step-by-step implementation of the Quarter Outlook + Sentiment platform extension to SectorView.

## Current State
- ✅ Basic sector time series, features, and forecasts
- ✅ FII/DII flows, macro indicators, options data
- ✅ News headlines and sentiment scoring
- ✅ Basic rule-based forecasts
- ✅ Frontend dashboard with market summary, correlations, sector tiles

## Implementation Steps

### STEP 0 - Understanding & Planning ✅
- [x] Inspected repo structure
- [x] Identified existing models and endpoints
- [x] Created this roadmap document

### STEP 1 - Extend DB & Models ✅
- [x] Add new columns to `sector_features`:
  - `ret_3m`, `ret_6m`
  - `rel_1m_vs_nifty`, `rel_3m_vs_nifty`
  - `breadth_above_50dma`, `breadth_3m_highs`
  - `fii_net_inr_20d`, `fii_net_inr_percentile`
  - `valuation_pe`, `valuation_pe_percentile`
  - `earnings_upgrades_pct_60d`, `earnings_downgrades_pct_60d`
  - `quarter_score`
- [x] Create `sector_breadth_daily` table
- [x] Create `earnings_events` table
- [x] Create `sector_valuations_daily` table
- [x] Create `market_sentiment_daily` table
- [x] Create Alembic migration (006_add_quarter_outlook)
- [x] Update SQLAlchemy models
- [x] Update Pydantic schemas

### STEP 2 - Feature Computation for QuarterScore ✅
- [x] Create `features_quarter.py` module
- [x] Implement price & momentum features (ret_3m, ret_6m, relative returns)
- [x] Implement breadth features computation
- [x] Implement flow features (20d rolling, percentile)
- [x] Implement valuation features (P/E, percentile)
- [x] Implement earnings features (upgrades/downgrades %)
- [x] Create QuarterScore formula with weights
- [x] Add macro overlay logic
- [x] Integrate into existing `features.py`
- [x] Add CRUD functions for new tables
- [ ] Unit tests for QuarterScore computation (pending)

### STEP 3 - Integrate QuarterScore into Forecasts
- [ ] Update forecast computation to use QuarterScore
- [ ] Store contributions_dict in forecasts
- [ ] Extend forecast API response with drivers
- [ ] Create `/api/v1/sectors/quarter-outlook` endpoint
- [ ] Update existing forecast endpoint

### STEP 4 - Frontend: Quarter Outlook & Driver Card
- [ ] Create QuarterOutlookRanking component
- [ ] Create DriverCard component/modal
- [ ] Integrate into dashboard
- [ ] Add visualizations (bar charts, score displays)

### STEP 5 - Breadth & Leadership Panel
- [ ] Create `/api/v1/breadth` endpoint
- [ ] Create BreadthLeadership component
- [ ] Add visualizations (horizontal bars, badges)

### STEP 6 - Market Sentiment Dashboard
- [ ] Create `sentiment_market.py` service
- [ ] Implement market regime computation
- [ ] Create `/api/v1/market-sentiment` endpoint
- [ ] Create MarketSentimentDashboard component
- [ ] Add gauges and regime indicator

### STEP 7 - Valuation & Sentiment Tags
- [ ] Extend sector list endpoint with valuation/sentiment
- [ ] Update SectorTile component with tags
- [ ] Add color coding and indicators

### STEP 8 - Earnings Watch Panel
- [ ] Create `/api/v1/earnings-watch` endpoint
- [ ] Create EarningsWatch component
- [ ] Add heatmap visualization

### STEP 9 - Derivatives Sentiment (Optional)
- [ ] Extend options data processing
- [ ] Add derivatives sentiment to forecast response
- [ ] Update Driver Card to show derivatives info

### STEP 10 - Backtesting & Validation
- [ ] Create `quarter_outlook_backtest.py` module
- [ ] Implement historical validation
- [ ] Generate backtest reports
- [ ] Create summary metrics

### STEP 11 - Tests, Docs & UX Polish
- [ ] Unit tests for all new functions
- [ ] API endpoint tests
- [ ] Update README.md
- [ ] Create feature documentation
- [ ] Add tooltips and help text
- [ ] Mobile responsiveness check

## Notes
- All changes are additive - no breaking changes to existing functionality
- Mock data generators will be used where external data isn't available
- Sector sensitivity to macro will be documented in config files

