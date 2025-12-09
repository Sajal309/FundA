# Sector Screener Table Implementation

## Overview
The Sector Screener Table component displays stocks in a standardized format matching Screener.in-style layout with 20 exact columns in a specific order.

## Files Created

### 1. `src/components/SectorScreenerTable.tsx`
Main table component that:
- Fetches data from `/api/v1/sector-screener?sector=<key>`
- Maps incoming field names to standardized UI keys using `columnMapper`
- Displays 20 columns in exact order: Rank, Name, Ticker, CMP Rs., Mar Cap Rs.Cr., P/E, Div Yld %, Qtr Profit Var %, Qtr Sales Var %, ROCE %, Free Cash Flow Rs.Cr., Debt / Eq, ROE %, ROE 3Yr %, Pledged %, Prom. Hold. %, Public Hold %, M.Cap / Sales, 52w %, ROE 5Yr %
- Supports sorting on all columns (except Rank and Name)
- Computes Rank (1..N) based on current sort order
- Exports current view to CSV
- Shows "-" for missing/null values
- Saves last selected sector in localStorage

### 2. `src/utils/columnMapper.ts`
Utility functions for field name normalization and mapping:
- `normalizeHeader()` - Normalizes header strings (lowercase, remove spaces/punctuation)
- `mapRowToUiKeys()` - Maps a row object to standardized UI field keys
- `getUiFieldKey()` - Gets UI field key from a header string
- `UI_COLUMNS` - Constant array defining the 20 columns in exact order

### 3. `src/utils/__tests__/columnMapper.test.ts`
Unit tests for:
- `normalizeHeader` with 5-8 header variants
- `mapRowToUiKeys` with various input formats
- `getUiFieldKey` mapping function

### 4. Updated `src/pages/StockScreenerPage.tsx`
Simplified to use the new `SectorScreenerTable` component instead of custom table implementation.

## Backend Requirements

The backend API endpoint `/api/v1/sector-screener?sector=<key>` should return rows with these exact field names:

### Required Fields:
- `name` - Company name
- `ticker` - Stock ticker symbol  
- `cmp` - Current Market Price (in Rs)
- `market_cap` - Market Capitalization (in Rs Crores)
- `pe` - Price to Earnings ratio
- `dividend_yield` - Dividend Yield percentage
- `qtr_profit_var_pct` - Quarterly Profit Variation percentage
- `qtr_sales_var_pct` - Quarterly Sales Variation percentage
- `roce` - Return on Capital Employed percentage
- `free_cash_flow` - Free Cash Flow (in Rs Crores)
- `debt_to_equity` - Debt to Equity ratio
- `roe` - Return on Equity percentage
- `roe_3y` - ROE 3 Year average percentage
- `pledged_percent` - Pledged percentage
- `promoter_holding` - Promoter Holding percentage
- `public_holding` - Public Holding percentage
- `mcap_to_sales` - Market Cap to Sales ratio
- `percent_change_52w` - 52 Week percentage change
- `roe_5y` - ROE 5 Year average percentage

### Optional Fields:
- `url` - Link to company page (rendered as clickable link in Name column)

### Data Format Notes:
1. **Market Cap & Free Cash Flow**: Should be in Rs Crores. If stored in absolute Rs, divide by 10,000,000 before returning.
2. **Percentages**: All percentage fields should be numeric values (e.g., 15.5 for 15.5%, not 0.155).
3. **Missing Values**: Use `null` or omit the field entirely. The UI displays "-" for null values.
4. **Sorting**: The `primarySort` field should match one of the field names above. Default direction should be "desc" for most metrics.

## Field Mapping

The `columnMapper` utility can handle field name variations from different sources (Screener.in CSV, database, etc.). It maps common variations like:
- "CMP Rs." → `cmp`
- "Mar Cap Rs.Cr." → `market_cap`
- "P/E" → `pe`
- "Div Yld %" → `dividend_yield`
- "Qtr Profit Var %" → `qtr_profit_var_pct`
- etc.

## Features

✅ **Exact Column Layout**: 20 columns in the exact order specified
✅ **Sorting**: Click any column header to sort (except Rank/Name)
✅ **Ranking**: Rank column (1..N) updates based on current sort order
✅ **CSV Export**: Export current view with UI column headers
✅ **Missing Data Handling**: Shows "-" for null/missing values
✅ **Responsive**: Horizontal scroll for wide tables, sticky Rank/Name columns
✅ **Loading States**: Spinner while fetching data
✅ **Error Handling**: Graceful error messages
✅ **Empty State**: Helpful message when no stocks found
✅ **Persistence**: Saves last selected sector in localStorage

## Usage

```tsx
import SectorScreenerTable from '../components/SectorScreenerTable';

<SectorScreenerTable sectorKey="banks" />
```

The component automatically:
- Fetches data on mount and when `sectorKey` changes
- Applies default sort from API `primarySort` field
- Maps field names to UI keys
- Renders the table with all 20 columns

## Testing

Run unit tests:
```bash
# If using Jest/Vitest
npm test columnMapper.test.ts
```

The tests verify:
- Header normalization with various formats
- Row mapping with different field name variations
- Field key lookup functionality

