# Sector Rotation Feature Implementation

## Overview
This document tracks the implementation of the Sector Rotation feature, a comprehensive module for analyzing sector and industry breadth, momentum scores, deliveries, and VWAP metrics.

## Implementation Status

### ✅ Completed
1. Database models added for:
   - Stocks, Industries
   - Stock time series, market caps, technical indicators
   - Sector rotation aggregation tables (breadth, momentum, deliveries, VWAP)

### 🚧 In Progress
2. Alembic migration for new tables
3. Backend services for calculations
4. API endpoints
5. Frontend routing and components

### 📋 Pending
6. Paywall/subscription integration
7. Testing and validation

## Architecture

### Database Schema
- **stocks**: Master stock data with sector/industry mapping
- **industries**: Industry master data
- **stock_time_series**: Daily OHLCV + deliverable volume
- **stock_market_caps**: Daily market cap per stock
- **stock_technical_indicators**: SMA, RSI, RS55, returns, VWAP
- **stock_rolling_stats**: 20-day rolling averages for deliveries
- **sector_breadth_snapshots**: Precomputed breadth metrics
- **industry_breadth_snapshots**: Same for industries
- **sector_momentum_scores**: Precomputed momentum scores (1M, 3M, 6M)
- **industry_momentum_scores**: Same for industries
- **sector_delivery_stats**: Delivery and volume statistics
- **industry_delivery_stats**: Same for industries
- **sector_vwap_snapshots**: VWAP-based metrics
- **industry_vwap_snapshots**: Same for industries

### API Endpoints (Planned)
- `GET /api/v1/sector-rotation/available-dates` - List available dates
- `GET /api/v1/sector-rotation/breadth` - Breadth metrics
- `GET /api/v1/sector-rotation/scores` - Momentum scores
- `GET /api/v1/sector-rotation/deliveries` - Delivery statistics
- `GET /api/v1/sector-rotation/vwap` - VWAP metrics

### Frontend Structure (Planned)
- `/sector-rotation` - Main page route
- Primary tabs: Breadth | Scores | Deliveries | VWAP
- Secondary tabs: Sectors | Industries
- Date picker
- Paywall overlay for non-subscribed users

## Next Steps
1. Complete migration file
2. Create backend service modules
3. Implement API endpoints
4. Add React Router
5. Create frontend components
6. Add paywall logic

