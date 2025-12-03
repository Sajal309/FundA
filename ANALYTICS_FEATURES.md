# Analytics & Visualization Features

## Overview

The SectorView platform now includes comprehensive analytics and data visualization capabilities, providing deep insights into sector performance, correlations, flows, options, and sentiment.

## Dashboard Features

### 1. Market Summary Widget
- **Location**: Top of dashboard
- **Features**:
  - FII/DII flows summary (7-day)
  - Average sector correlation
  - Real-time market overview
- **Updates**: Every 5 minutes

### 2. Correlation Matrix
- **Location**: Dashboard analytics section
- **Features**:
  - Visual correlation matrix between all sectors
  - Color-coded correlation values
  - 30-day lookback period
  - Interactive table view
- **Color Coding**:
  - Green (>0.8): High positive correlation
  - Blue (0.5-0.8): Moderate positive correlation
  - Gray (0-0.5): Low positive correlation
  - Orange/Red (<0): Negative correlation

### 3. Sector Comparison Tool
- **Location**: Dashboard analytics section
- **Features**:
  - Compare up to 5 sectors simultaneously
  - Two comparison modes:
    - **Returns**: 1D, 5D, 1M returns comparison
    - **Sentiment**: 1D and 7D sentiment scores
  - Interactive sector selection
  - Bar/Line charts based on metric

### 4. Sector Performance Tiles
- **Location**: Main dashboard section
- **Features**:
  - Real-time sector prices
  - Sparkline charts
  - Forecast indicators
  - Click to view detailed analytics

### 5. Forecast Table
- **Location**: Dashboard bottom section
- **Features**:
  - 3-month forecasts for all sectors
  - Probability distributions
  - Expected returns
  - Color-coded forecast labels

## Sector Detail Modal

### Tabbed Interface

#### 1. Overview Tab
- **Forecast Section**:
  - 3-month forecast label
  - Expected return percentage
  - Probability breakdown (UP/NEUTRAL/DOWN)
  - Top drivers with impact indicators

- **Trend Analysis**:
  - Trend direction (uptrend/downtrend/sideways)
  - Volatility regime (high/normal/low)
  - Price change percentage
  - Current vs average volatility

- **Price & Volume Chart**:
  - Combined area/line/bar chart
  - Close price with MA20 and MA50
  - Volume bars
  - Interactive tooltips

#### 2. Analytics Tab
- **FII/DII Flows Analysis**:
  - Total FII net flows
  - Total DII net flows
  - Average daily flows
  - Daily flows bar chart (FII vs DII)

#### 3. Options Tab
- **Options Metrics**:
  - Current PCR (Put-Call Ratio)
  - Average PCR
  - OI Change 1D
  - IV Index (current and average)

- **Options Charts**:
  - PCR line chart
  - OI Change bar chart
  - IV Index line chart
  - Historical trends

#### 4. Sentiment Tab
- **Sentiment Metrics**:
  - Current sentiment (1D and 7D)
  - Average sentiment scores
  - Sentiment trend (improving/declining)
  - Headline counts

- **Sentiment Charts**:
  - Dual-line sentiment trends (1D and 7D)
  - Headline volume bars
  - Historical sentiment analysis

## API Endpoints

### Analytics Endpoints

1. **GET `/api/v1/analytics/correlations`**
   - Get sector correlation matrix
   - Parameters: `lookback_days` (default: 30)
   - Returns: Correlation coefficients for sector pairs

2. **GET `/api/v1/analytics/sectors/{sector_id}/trends`**
   - Analyze sector trends
   - Parameters: `lookback_days` (default: 30)
   - Returns: Trend direction, volatility, price changes

3. **GET `/api/v1/analytics/flows`**
   - Analyze FII/DII flows
   - Parameters: `sector_id` (optional), `lookback_days` (default: 30)
   - Returns: Flow statistics and daily breakdown

4. **GET `/api/v1/analytics/options/{underlying}`**
   - Analyze options data
   - Parameters: `lookback_days` (default: 30)
   - Returns: PCR, OI changes, IV index

5. **GET `/api/v1/analytics/sectors/{sector_id}/sentiment`**
   - Analyze sentiment trends
   - Parameters: `lookback_days` (default: 30)
   - Returns: Sentiment scores and trends

6. **GET `/api/v1/analytics/sectors/compare`**
   - Compare multiple sectors
   - Parameters: `sector_ids` (comma-separated), `metric` (returns/sentiment)
   - Returns: Comparison data for selected sectors

## Data Sources

### Real-Time Data
- **NewsAPI**: News headlines with sentiment scoring
- **Kite Connect**: Options chain data (PCR, OI, IV)
- **yfinance**: Macro economic indicators

### Historical Data
- Sector time series (EOD prices)
- FII/DII flows
- Options data
- News sentiment

## Visualization Libraries

- **Recharts**: Primary charting library
  - LineChart, BarChart, AreaChart, ComposedChart
  - Responsive containers
  - Interactive tooltips and legends

- **React Query**: Data fetching and caching
  - Automatic refetching
  - Background updates
  - Error handling

## Performance Optimizations

1. **Data Caching**: React Query caches API responses
2. **Lazy Loading**: Components load data on demand
3. **Debounced Updates**: Prevents excessive API calls
4. **Responsive Design**: Optimized for all screen sizes

## Future Enhancements

1. **Real-time WebSocket Updates**: Live data streaming
2. **Advanced Filters**: Date range, sector filters
3. **Export Functionality**: PDF/CSV export
4. **Custom Dashboards**: User-configurable layouts
5. **Alerts & Notifications**: Threshold-based alerts
6. **Backtesting UI**: Visual backtest results
7. **Portfolio Analysis**: Multi-sector portfolio views

## Usage Tips

1. **Correlation Matrix**: Use to identify sector relationships and diversification opportunities
2. **Sector Comparison**: Compare similar sectors to find relative strength
3. **Options Tab**: Monitor PCR and IV for market sentiment
4. **Sentiment Tab**: Track news sentiment trends over time
5. **Flows Analysis**: Understand institutional money flow patterns

## Technical Notes

- All charts are responsive and mobile-friendly
- Data refreshes automatically every 5 minutes
- Error states are handled gracefully
- Loading states provide user feedback
- Color coding follows consistent patterns (green=positive, red=negative)

