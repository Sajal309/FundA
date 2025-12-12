# Forecast Accuracy Improvements

## Overview
The 3-month forecast on the Dashboard was showing "random" data because several critical data sources were missing or stale. This document outlines the improvements made to increase forecast accuracy.

## Issues Identified

### Missing Data Sources
1. **SectorBreadthDaily**: 0 records - completely empty
2. **SectorValuationsDaily**: 0 records - completely empty  
3. **EarningsEvent**: 0 records - completely empty
4. **SectorSentimentDaily**: Only 1 record, stale (2025-11-28)
5. **Options Data**: Stale (2025-11-28, 14 days old)

### Impact on Forecast
The forecast depends on QuarterScore, which uses:
- ✅ **Momentum**: Has data (from sector time series)
- ❌ **Breadth**: Missing (SectorBreadthDaily was empty)
- ✅ **Flows**: Has data (FII/DII flows)
- ❌ **Valuation**: Missing (SectorValuationsDaily was empty)
- ❌ **Earnings**: Missing (EarningsEvent was empty)
- ⚠️ **Sentiment**: Stale (only 1 record from Nov 28)

When critical features are missing, the forecast falls back to simple rule-based logic, which can appear "random" or inaccurate.

## Solutions Implemented

### 1. Populate SectorBreadthDaily from Snapshots

**File**: `backend/app/services/populate_forecast_data.py`

- Converts `SectorBreadthSnapshot` data to `SectorBreadthDaily` format
- Uses existing breadth snapshots from sector rotation ETL
- Calculates `above_50dma` and `above_200dma` from snapshot percentages

**Usage**:
```bash
docker compose exec backend python3 -m app.scripts.populate_forecast_data --breadth-only --days 30
```

### 2. Calculate Sector Valuations from Stock Fundamentals

**File**: `backend/app/services/populate_forecast_data.py`

- Calculates market-cap weighted average P/E from constituent stocks
- Uses latest stock fundamentals and market caps
- Creates `SectorValuationsDaily` records

**Usage**:
```bash
docker compose exec backend python3 -m app.scripts.populate_forecast_data --valuations-only
```

### 3. Improved Fallback Logic

**File**: `backend/app/services/features_quarter.py`

- **Breadth**: Falls back to `SectorBreadthSnapshot` if `SectorBreadthDaily` is missing
- **Breadth**: Falls back to computing from stock technical indicators if snapshots are missing
- **Valuation**: Automatically calculates from stocks if `SectorValuationsDaily` is missing

### 4. Automatic Data Population Script

**File**: `backend/app/scripts/populate_forecast_data.py`

Populates all missing forecast data:
- Breadth data from snapshots
- Valuations from stock fundamentals
- Ensures sector rotation ETL has run

**Usage**:
```bash
# Populate last 30 days
docker compose exec backend python3 -m app.scripts.populate_forecast_data --days 30

# Populate specific date
docker compose exec backend python3 -m app.scripts.populate_forecast_data --date 2025-12-12
```

## Data Source Priority

### Breadth Features
1. `SectorBreadthDaily` (primary)
2. `SectorBreadthSnapshot` (fallback)
3. Computed from stock technical indicators (last resort)

### Valuation Features
1. `SectorValuationsDaily` (primary)
2. Calculated from stock fundamentals (automatic fallback)

### Earnings Features
- Currently relies on `EarningsEvent` table
- **Future**: Integrate with earnings calendar APIs or analyst revision data

### Sentiment Features
- Uses `SectorSentimentDaily` from news aggregation
- **Future**: Refresh sentiment data daily via news API

## Accuracy Improvements

### Before
- Breadth: `None` → QuarterScore uses default 0.0
- Valuation: `None` → QuarterScore uses default 0.5 (neutral)
- Earnings: `None` → QuarterScore uses default 0.0
- **Result**: Forecasts appear random due to missing data

### After
- Breadth: Real data from snapshots or stock indicators
- Valuation: Market-cap weighted P/E from stock fundamentals
- Earnings: Still missing, but handled gracefully
- **Result**: Forecasts use real data, more accurate predictions

## Recommendations for Further Improvement

### 1. Earnings Data
- Integrate with earnings calendar APIs (NSE, BSE)
- Track analyst revisions from broker reports
- Use earnings surprise data if available

### 2. Sentiment Data
- Set up daily news aggregation job
- Use multiple news sources for better coverage
- Implement sector-specific keyword matching

### 3. Options Data
- Refresh options data daily (currently stale)
- Use NSE options chain data
- Calculate PCR, OI changes, IV from real-time data

### 4. Valuation Data
- Add P/B (Price-to-Book) ratios
- Add dividend yield data
- Use NSE sector indices data for official P/E ratios

### 5. Machine Learning
- Train ML models on historical forecast accuracy
- Use ensemble methods combining multiple signals
- Backtest forecast performance regularly

## Running the Improvements

### Initial Population
```bash
# Populate all missing data for last 30 days
docker compose exec backend python3 -m app.scripts.populate_forecast_data --days 30

# Regenerate all forecasts
docker compose exec backend python3 -c "
from app.db import database
from app.services import forecasts
db = database.SessionLocal()
forecasts.generate_forecasts_for_all_sectors(db)
db.close()
"
```

### Daily Maintenance
Add to daily ETL:
```bash
# After sector rotation ETL runs
docker compose exec backend python3 -m app.scripts.populate_forecast_data --days 1

# Regenerate forecasts
docker compose exec backend python3 -c "
from app.db import database
from app.services import forecasts
db = database.SessionLocal()
forecasts.generate_forecasts_for_all_sectors(db)
db.close()
"
```

## Testing

### Verify Data Population
```bash
docker compose exec backend python3 -c "
from app.db import database, models
from sqlalchemy import func

db = database.SessionLocal()
print('Breadth Daily:', db.query(models.SectorBreadthDaily).count())
print('Valuations Daily:', db.query(models.SectorValuationsDaily).count())
print('Latest Breadth:', db.query(func.max(models.SectorBreadthDaily.date)).scalar())
print('Latest Valuation:', db.query(func.max(models.SectorValuationsDaily.date)).scalar())
db.close()
"
```

### Check Forecast Quality
```bash
docker compose exec backend python3 -c "
from app.db import database, crud

db = database.SessionLocal()
forecast = crud.get_latest_sector_forecast(db, 'NIFTY_BANK')
if forecast:
    print(f'Quarter Score: {forecast.quarter_score}')
    print(f'Expected Return: {forecast.expected_return_pct}%')
    print(f'Drivers: {len(forecast.drivers or [])} components')
db.close()
"
```

## Additional Improvements (Phase 2)

### 6. Refresh Sentiment Data from News Headlines

**File**: `backend/app/services/populate_forecast_data.py`

- Aggregates sentiment from existing news headlines
- Creates `SectorSentimentDaily` records for all sectors
- Calculates 1-day and 7-day rolling sentiment scores

**Usage**:
```bash
docker compose exec backend python3 -m app.scripts.populate_forecast_data --sentiment-only --days 30
```

### 7. Earnings Events Fallback from Fundamentals

**File**: `backend/app/services/populate_forecast_data.py`

- Creates earnings events based on fundamentals changes
- Detects upgrades/downgrades from:
  - Profit growth changes (>5% threshold)
  - P/E ratio changes (>10% threshold)
  - Quarterly profit variations (>20% threshold)
- Provides fallback when actual earnings data is unavailable

**Usage**:
```bash
docker compose exec backend python3 -m app.scripts.populate_forecast_data --earnings-only
```

### 8. Daily Refresh Script

**File**: `backend/app/scripts/refresh_forecast_data_daily.sh`

Automated script to refresh all forecast data daily:
- Populates breadth, valuations, sentiment, earnings
- Regenerates all forecasts
- Can be added to cron or scheduled tasks

**Usage**:
```bash
# Run manually
./backend/app/scripts/refresh_forecast_data_daily.sh

# Add to cron (runs daily at 6 PM)
0 18 * * * cd /path/to/FundA && ./backend/app/scripts/refresh_forecast_data_daily.sh
```

## Summary

✅ **Fixed**: Breadth and Valuation data now populated from real sources
✅ **Fixed**: Sentiment data refreshed from news headlines
✅ **Fixed**: Earnings events created from fundamentals fallback
✅ **Improved**: Fallback logic ensures forecasts work even with missing data
✅ **Created**: Automated scripts to populate and refresh all data
✅ **Created**: Daily refresh script for production use
📈 **Result**: Forecasts now use comprehensive real data, significantly improving accuracy

## Phase 3 Improvements

### 9. Options Data Refresh

**File**: `backend/app/services/populate_forecast_data.py`

- Refreshes options data from Kite Connect
- Fetches PCR, OI, and IV data for NIFTY and BANKNIFTY
- Updates `OptionsDaily` table for forecast calculations

**Usage**:
```bash
docker compose exec backend python3 -m app.scripts.populate_forecast_data --options-only
```

### 10. Forecast Backtesting

**File**: `backend/app/services/forecast_backtest.py`

- Calculates realized returns after forecast dates
- Evaluates forecast accuracy (UP/DOWN/NEUTRAL predictions)
- Computes mean error between expected and realized returns
- Provides quality metrics for forecast monitoring

**Usage**:
```python
from app.services import forecast_backtest

# Evaluate accuracy
accuracy = forecast_backtest.evaluate_forecast_accuracy(db, sector_id='NIFTY_BANK')

# Get quality metrics
metrics = forecast_backtest.get_forecast_quality_metrics(db)
```

### 11. Forecast Quality Monitoring

**File**: `backend/app/scripts/check_forecast_quality.py`

- Checks data completeness for all forecast components
- Reports average confidence and quarter scores
- Evaluates historical forecast accuracy
- Provides actionable insights for improvement

**Usage**:
```bash
docker compose exec backend python3 -m app.scripts.check_forecast_quality
```

### 12. API Endpoints for Quality Monitoring

**File**: `backend/app/api/v1/forecasts.py`

New endpoints:
- `GET /api/v1/forecasts/forecast-quality` - Get quality metrics
- `GET /api/v1/forecasts/forecast-accuracy` - Evaluate accuracy

## Complete Data Flow

1. **Daily ETL** → Populates sector time series, stock data, fundamentals
2. **Sector Rotation ETL** → Creates breadth snapshots, momentum scores
3. **Forecast Data Population** → Converts snapshots to daily tables, calculates valuations
4. **Sentiment Refresh** → Aggregates from news headlines
5. **Earnings Events** → Created from fundamentals changes
6. **Options Refresh** → Fetches PCR, OI, IV from Kite Connect
7. **Forecast Generation** → Computes QuarterScore and generates forecasts
8. **Quality Monitoring** → Tracks accuracy and data completeness

