# Stock Screener Feature

## Overview

The Stock Screener feature allows users to screen stocks by sector using predefined fundamental criteria, similar to Screener.in. Each sector has tailored filters and metrics that are relevant to that industry.

## Features

- **27 Sector Screeners**: Banks, NBFC, Insurance, IT, Software, FMCG, Pharma, Hospitals, Diagnostics, Real Estate, Cement, Metals, Capital Goods, Defence, Infrastructure, Telecom, Chemicals, Agrochemicals, Auto OEM, Auto Ancillary, Textiles, Retail, Oil & Gas, Renewables, Logistics, Consumer Durables, Media
- **Sector-Specific Filters**: Each sector has tailored criteria (e.g., Banks: ROA > 1%, NIM > 3%, GNPA < 3%)
- **Smart Sorting**: Primary and secondary sort fields per sector
- **Sortable Table**: Click column headers to sort client-side
- **Ranking**: Visual rank column (1, 2, 3...) based on current sort
- **Extensible**: Easy to add new sectors by updating config files

## Architecture

### Backend

1. **Database Model** (`backend/app/db/models.py`):
   - `StockFundamentals` table stores fundamental metrics for stocks
   - Fields include: ROE, ROCE, ROA, margins, growth rates, leverage ratios, sector-specific metrics

2. **Configuration** (`backend/app/config/sector_screeners.py`):
   - Defines all 27 sector screener configurations
   - Each config includes: filter criteria, sort fields, column definitions
   - Sector name mapping for filtering stocks

3. **Service** (`backend/app/services/sector_screener.py`):
   - `screen_stocks()`: Main function to apply filters and sorting
   - `apply_sector_filters()`: Applies sector-specific filter criteria
   - `map_field_name()`: Maps frontend field names to database columns

4. **API Endpoints** (`backend/app/api/v1/screener.py`):
   - `GET /api/v1/sector-screener?sector=<key>&limit=<n>`: Get screened stocks
   - `GET /api/v1/sector-screener/list`: List available screeners

### Frontend

1. **Configuration** (`frontend/src/config/sectorScreeners.ts`):
   - TypeScript types and all 27 sector configurations
   - Matches backend config structure

2. **API Client** (`frontend/src/api/client.ts`):
   - `getSectorScreener()`: Fetch screened stocks
   - `listSectorScreeners()`: List available screeners

3. **Page Component** (`frontend/src/pages/StockScreenerPage.tsx`):
   - Sector dropdown selector
   - Screening criteria display
   - Sortable data table with sector-specific columns
   - Rank column and value formatting

## Usage

### Accessing the Screener

Navigate to `/stock-screener` in the application, or click "Stock Screener" in the navigation menu.

### Using the Screener

1. **Select a Sector**: Choose from the dropdown (e.g., "Banks", "IT Services", "Pharma")
2. **View Criteria**: The screening criteria are displayed below the dropdown
3. **Review Results**: Stocks matching the criteria are displayed in a sortable table
4. **Sort**: Click any column header to sort by that field
5. **Ranking**: The rank column shows the position based on current sort order

### Example: Banks Screener

**Criteria:**
- ROA > 1%
- Net Interest Margin > 3%
- Gross NPA < 3%
- Net NPA < 1%
- Provision Coverage Ratio > 70%
- CASA Ratio > 35%
- Capital Adequacy Ratio > 15%
- Profit Growth 5Y > 12%

**Columns:**
- Name, Ticker, Market Cap
- ROA %, NIM %, GNPA %, NNPA %
- PCR %, CASA %, CAR %
- Profit CAGR 5Y %

**Sorting:**
- Primary: ROA (descending)
- Secondary: NIM (descending)

## Data Requirements

The screener requires fundamental data in the `stock_fundamentals` table. Each stock should have:
- Latest fundamental metrics (ROE, ROCE, margins, growth rates, etc.)
- Sector assignment in the `stocks` table

### Populating Fundamentals Data

To use the screener, you need to populate the `stock_fundamentals` table. Options:

1. **ETL Script**: Create a script to fetch fundamentals from a data source (e.g., Screener.in, NSE, BSE)
2. **Manual Import**: Import CSV/JSON data with fundamental metrics
3. **API Integration**: Integrate with a fundamentals data provider

Example structure for a fundamentals record:
```python
{
    "ticker": "HDFCBANK",
    "date": "2024-01-31",
    "roe": 18.5,
    "roce": 20.2,
    "roa": 2.1,
    "net_interest_margin": 4.2,
    "gross_npa": 1.8,
    "net_npa": 0.5,
    "provision_coverage": 75.0,
    "casa_ratio": 42.0,
    "capital_adequacy": 18.5,
    "profit_growth_5y": 15.2,
    # ... other fields
}
```

## Adding a New Sector Screener

1. **Update Backend Config** (`backend/app/config/sector_screeners.py`):
   ```python
   "new_sector": SectorScreenerConfig(
       key="new_sector",
       label="New Sector",
       filter_query="Sector = 'New Sector' AND ROCE > 15 AND ...",
       primary_sort=SortConfig(field="roce", direction="desc"),
       secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
       columns=[
           ColumnConfig("name", "Name"),
           ColumnConfig("ticker", "Ticker"),
           # ... other columns
       ]
   )
   ```

2. **Update Frontend Config** (`frontend/src/config/sectorScreeners.ts`):
   ```typescript
   new_sector: {
     key: "new_sector",
     label: "New Sector",
     filterQuery: "Sector = 'New Sector' AND ROCE > 15 AND ...",
     primarySort: { field: "roce", direction: "desc" },
     secondarySort: { field: "salesGrowth5Y", direction: "desc" },
     columns: [
       { field: "name", label: "Name" },
       { field: "ticker", label: "Ticker" },
       // ... other columns
     ]
   }
   ```

3. **Add Sector Mapping** (`backend/app/config/sector_screeners.py`):
   ```python
   "new_sector": ["New Sector", "NIFTY_NEW_SECTOR"]
   ```

4. **Add Filter Logic** (`backend/app/services/sector_screener.py`):
   ```python
   elif sector_key == "new_sector":
       query = query.filter(
           models.StockFundamentals.roce > 15.0,
           models.StockFundamentals.sales_growth_5y > 10.0,
           # ... other filters
       )
   ```

## Field Name Mapping

The frontend uses camelCase field names (e.g., `netInterestMargin`), while the database uses snake_case (e.g., `net_interest_margin`). The mapping is handled by `FIELD_MAP` in `backend/app/config/sector_screeners.py`.

## Future Enhancements

- [ ] Export to CSV functionality
- [ ] Save custom screens
- [ ] Compare multiple sectors
- [ ] Advanced filters (user-defined criteria)
- [ ] Historical screening (backtest screens)
- [ ] Watchlist integration
- [ ] Alerts for new matches

