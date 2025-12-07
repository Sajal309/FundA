# Sector Rotation Feature - Setup Guide

## Overview
The Sector Rotation feature provides comprehensive analysis of sector and industry breadth, momentum scores, delivery statistics, and VWAP metrics.

## Installation

### 1. Install Frontend Dependencies
```bash
cd frontend
npm install react-router-dom @types/react-router-dom
```

### 2. Run Database Migration
```bash
docker compose exec backend alembic upgrade head
```

This will create all the necessary tables:
- `stocks`, `industries`
- `stock_time_series`, `stock_market_caps`, `stock_technical_indicators`, `stock_rolling_stats`
- `sector_breadth_snapshots`, `industry_breadth_snapshots`
- `sector_momentum_scores`, `industry_momentum_scores`
- `sector_delivery_stats`, `industry_delivery_stats`
- `sector_vwap_snapshots`, `industry_vwap_snapshots`

## API Endpoints

All endpoints are under `/api/v1/sector-rotation/`:

- `GET /available-dates?level=sector|industry` - Get available dates
- `GET /breadth?level=sector|industry&date=YYYY-MM-DD&metric_type=mcap|count` - Breadth metrics
- `GET /scores?level=sector|industry&date=YYYY-MM-DD` - Momentum scores
- `GET /deliveries?level=sector|industry&date=YYYY-MM-DD` - Delivery statistics
- `GET /vwap?level=sector|industry&date=YYYY-MM-DD` - VWAP metrics

## Frontend Routes

- `/` - Main Dashboard
- `/sector-rotation` - Sector Rotation page

## Data Requirements

The feature requires precomputed aggregation data in the snapshot tables. To populate data:

1. **Stock Data**: Need individual stock OHLCV data in `stock_time_series`
2. **Market Caps**: Daily market cap data in `stock_market_caps`
3. **Technical Indicators**: SMA, RSI, RS55, returns in `stock_technical_indicators`
4. **Rolling Stats**: 20-day averages in `stock_rolling_stats`
5. **Aggregation**: Run daily ETL to compute and store snapshots

## Features Implemented

### ✅ Breadth Tab
- Shows % of market cap/stocks meeting technical conditions
- Conditions: RS55>0, RSI>50, Price>SMA20/50/100
- Toggle between MCap% and Count%

### ✅ Scores Tab
- Momentum scores (0-100) for 1M, 3M, 6M horizons
- Color-coded: Red (0-40), Yellow (41-60), Green (61-100)
- Market-cap weighted returns converted to scores

### ✅ Deliveries Tab
- Delivery and volume statistics
- MCap changes, traded/delivery values and multiples
- Sortable columns

### ✅ VWAP Tab
- % of market cap where price > VWAP
- Heatmap visualization

## Next Steps

1. **Data Population**: Create ETL scripts to:
   - Fetch stock data from data provider
   - Calculate technical indicators
   - Compute aggregations daily

2. **Paywall Integration**: Add subscription check and overlay component

3. **Testing**: Add unit tests for calculation services

4. **Performance**: Add caching for frequently accessed dates

## Notes

- The feature is fully functional but requires data in aggregation tables
- All calculations are done server-side for performance
- Frontend uses React Query for data fetching and caching
- Dark theme styling consistent with rest of application

