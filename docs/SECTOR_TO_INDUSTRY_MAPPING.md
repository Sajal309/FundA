# Sector to Industry Mapping

## Overview

The Sector Rotation feature now supports both **Sectors** and **Industries** as separate views. Industries use a **1:1 mapping** with sectors, where each sector becomes its own industry for maximum visibility and consistency.

## Mapping Strategy

### 1:1 Sector-to-Industry Mapping

Each sector defined in `SECTOR_NAMES` (35 sectors) is mapped to its own industry:

- **Sector ID** = **Industry ID** (direct 1:1 mapping)
- **Sector Name** = **Industry Name** (from `SECTOR_NAMES`)

### Example Mappings

| Sector ID | Industry ID | Display Name |
|-----------|-------------|--------------|
| `NIFTY_BANK` | `NIFTY_BANK` | Nifty Bank |
| `NIFTY_IT` | `NIFTY_IT` | Nifty IT |
| `NIFTY_PHARMA` | `NIFTY_PHARMA` | Nifty Pharma |
| `NIFTY_AUTO` | `NIFTY_AUTO` | Nifty Auto |
| `NIFTY_FMCG` | `NIFTY_FMCG` | Nifty FMCG |
| `NIFTY_ENERGY` | `NIFTY_ENERGY` | Nifty Energy |
| `NIFTY_METAL` | `NIFTY_METAL` | Nifty Metal |
| `NIFTY_REALTY` | `NIFTY_REALTY` | Nifty Realty |
| `NIFTY_50` | `NIFTY_50` | Nifty 50 |

## Implementation

### Database Schema

**Stocks Table:**
- `sector_id`: Foreign key to sector
- `industry_id`: Foreign key to industry (same as `sector_id` for 1:1 mapping)

**Industries Table:**
- `industry_id`: Primary key (matches sector_id)
- `name`: Display name (from `SECTOR_NAMES`)

### Stock Assignment

All stocks are assigned `industry_id = sector_id`:

```python
# From assign_industries_to_all_stocks.py
for stock in stocks:
    if stock.sector_id:
        stock.industry_id = stock.sector_id  # 1:1 mapping
```

### Industry Creation

Industries are created from all sectors in `SECTOR_NAMES`:

```python
# From assign_industries_to_all_stocks.py
for sector_id, sector_name in SECTOR_NAMES.items():
    industry = Industry(
        industry_id=sector_id,  # Same as sector_id
        name=sector_name
    )
```

## Current Status

### Industries with Data

As of the latest ETL run, **9 industries** have complete data:

1. **Nifty Bank** (10 stocks)
2. **Nifty Auto** (10 stocks)
3. **Nifty IT** (10 stocks)
4. **Nifty Pharma** (10 stocks)
5. **Nifty FMCG** (10 stocks)
6. **Nifty Realty** (10 stocks)
7. **Nifty Energy** (10 stocks)
8. **Nifty Metal** (10 stocks)
9. **Nifty 50** (1 stock)

### Expansion Potential

- **Total sectors defined**: 35
- **Sectors with stock data**: 9
- **Sectors without stock data**: 26

When stocks are added for other sectors, they will automatically appear in the industry rotation view.

## API Endpoints

All sector rotation endpoints support both `level=sector` and `level=industry`:

### Available Dates
```
GET /api/v1/sector-rotation/available-dates?level=industry
```

### Breadth Metrics
```
GET /api/v1/sector-rotation/breadth?level=industry&date=YYYY-MM-DD&metric_type=mcap
```

### Momentum Scores
```
GET /api/v1/sector-rotation/scores?level=industry&date=YYYY-MM-DD
```

### Delivery Stats
```
GET /api/v1/sector-rotation/deliveries?level=industry&date=YYYY-MM-DD
```

### VWAP Metrics
```
GET /api/v1/sector-rotation/vwap?level=industry&date=YYYY-MM-DD
```

## Frontend Usage

The Sector Rotation page supports switching between Sectors and Industries:

1. Navigate to `/sector-rotation`
2. Click **"Industries"** button (secondary tab)
3. Select a date from the dropdown
4. View any of the 4 tabs:
   - **Breadth**: RS55, RSI, SMA percentages
   - **Scores**: 1M, 3M, 6M momentum scores
   - **Deliveries**: Volume, delivery, MCap statistics
   - **VWAP**: Percentage of market cap above VWAP

## Data Flow

### ETL Process

1. **Stock Assignment**: Stocks are assigned `industry_id = sector_id`
2. **Aggregation**: ETL aggregates stock-level data to industry-level snapshots
3. **Normalization**: Momentum scores are normalized across all industries
4. **Storage**: Snapshots stored in industry-specific tables:
   - `industry_breadth_snapshots`
   - `industry_momentum_scores`
   - `industry_delivery_stats`
   - `industry_vwap_snapshots`

### API Response

Industry names are resolved using `SECTOR_NAMES` for consistency:

```python
# From sector_rotation.py
from app.api.v1.sectors import SECTOR_NAMES

industry_name = SECTOR_NAMES.get(industry_id, industry_id.replace("NIFTY_", "").replace("_", " ").title())
```

## Maintenance

### Adding New Sectors

When new sectors are added to `SECTOR_NAMES`:

1. Run `assign_industries_to_all_stocks.py --create-industries` to create the industry
2. Assign stocks to the new sector
3. Run ETL to populate industry snapshots

### Updating Stock Assignments

To update industry assignments:

```bash
docker compose exec backend python -m app.scripts.assign_industries_to_all_stocks
```

### Running ETL

To populate industry data:

```bash
docker compose exec backend python -m app.scripts.fetch_real_sector_rotation_data --skip-fetch --skip-indicators
```

## Benefits of 1:1 Mapping

1. **Consistency**: Sector and Industry views show the same data structure
2. **Simplicity**: No complex mapping logic needed
3. **Flexibility**: Easy to add new sectors/industries
4. **Clarity**: Users see familiar sector names in industry view
5. **Maintainability**: Single source of truth (`SECTOR_NAMES`)

## Future Enhancements

Potential improvements:

1. **True Industry Classification**: Map stocks to actual industry classifications (e.g., GICS, ICB)
2. **Multi-Level Hierarchy**: Support sector → industry → sub-industry
3. **Custom Groupings**: Allow users to create custom industry groups
4. **Cross-Sector Industries**: Industries that span multiple sectors

For now, the 1:1 mapping provides a clean, consistent experience while maintaining the flexibility to evolve.

