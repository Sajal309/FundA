# Sector-Wise Ranking Engine

## Overview

The ranking engine computes a weighted score for stocks within a sector based on multiple financial metrics. Stocks are ranked from best to worst based on their computed score.

## Architecture

### Components

1. **`backend/app/config/ranking_config.py`**: Sector-specific weight configurations
2. **`backend/app/services/ranking_service.py`**: Core ranking logic
3. **`backend/app/api/v1/screener.py`**: API endpoint for ranked stocks

## Scoring Model

The score combines normalized positive metrics (higher is better) and negative metrics (lower is better):

```
score = Σ (w_pos_i * norm_pos_i) - Σ (w_neg_j * norm_neg_j)
```

### Normalization Process

1. **Winsorization**: Values are clamped to 1st and 99th percentiles to reduce outlier effects
2. **Min-Max Normalization**: Values are normalized to [0, 1] range
3. **Inversion for Negative Metrics**: For metrics where lower is better (e.g., debt_to_equity), the normalized value is inverted: `1 - norm`
4. **Missing Value Handling**: NULL values are imputed with the sector median before normalization

### Score Calculation

- Positive metrics contribute to the score (higher = better)
- Negative metrics are inverted and subtracted (lower = better)
- Final score is mapped to 0-100 range
- Stocks are sorted by score (descending) and assigned ranks

## Configuration

### Adjusting Sector Weights

Edit `backend/app/config/ranking_config.py` to modify weights for any sector:

```python
"it": SectorRankingConfig(
    key="it",
    label="IT",
    metrics={
        "positive": [
            MetricWeight("roce", 35.0),      # Increase weight for ROCE
            MetricWeight("roe", 20.0),
            # ... add more metrics
        ],
        "negative": [
            MetricWeight("debt_to_equity", 20.0),
            # ... add more negative metrics
        ]
    },
    # ...
)
```

### Available Metrics

- **Profitability**: `roce`, `roe`, `opm`, `npm`, `roe_3y`, `roce_3y`
- **Growth**: `sales_growth_5y`, `profit_growth_5y`, `qtr_profit_var_pct`, `qtr_sales_var_pct`
- **Valuation**: `pe`, `pb`, `mcap_to_sales`
- **Risk**: `debt_to_equity`, `pledged_percent`
- **Ownership**: `promoter_holding`
- **Performance**: `percent_change_52w`
- **Cash Flow**: `free_cash_flow`

### Adding a New Sector

1. Add configuration to `SECTOR_RANKING_CONFIGS` in `ranking_config.py`:

```python
"new_sector": SectorRankingConfig(
    key="new_sector",
    label="New Sector",
    metrics={
        "positive": [
            MetricWeight("roce", 30.0),
            MetricWeight("roe", 25.0),
            # ...
        ],
        "negative": [
            MetricWeight("debt_to_equity", 20.0),
            # ...
        ]
    },
    primary_sort={"field": "score", "direction": "desc"},
    columns=[...]
)
```

2. Update `sector_id_patterns` in `ranking_service.py` to map sector key to database sector IDs.

## API Usage

### Endpoint

```
GET /api/v1/screener/sector-screener?sector=<sectorKey>&limit=<n>&sortBy=<field>
```

### Parameters

- `sector` (required): Sector key (e.g., 'it', 'fmcg', 'pharma')
- `limit` (optional): Maximum number of stocks to return (default: 100)
- `sortBy` (optional): Field to sort by instead of score (e.g., 'roce', 'roe')

### Response

```json
{
  "status": "ok",
  "sector": "it",
  "label": "IT",
  "columns": [
    {"field": "ticker", "label": "Ticker"},
    {"field": "score", "label": "Score"},
    ...
  ],
  "rows": [
    {
      "ticker": "TCS",
      "company_name": "Tata Consultancy Services",
      "score": 87.34,
      "rank": 1,
      "roce": 30.5,
      "roe": 25.3,
      ...
    },
    ...
  ],
  "meta": {
    "count": 50,
    "computed_at": "2025-12-12T12:00:00"
  }
}
```

### Example Requests

```bash
# Get top 20 IT stocks ranked by score
curl "http://localhost:8000/api/v1/screener/sector-screener?sector=it&limit=20"

# Get FMCG stocks sorted by ROCE instead of score
curl "http://localhost:8000/api/v1/screener/sector-screener?sector=fmcg&sortBy=roce"
```

## Testing

Run unit tests:

```bash
cd backend
pytest tests/test_ranking_service.py -v
```

## Performance Considerations

- For large datasets (10k+ stocks), consider:
  - Pre-computing normalized metrics nightly
  - Using PostgreSQL `percentile_disc` for percentile calculations
  - Caching results for frequently accessed sectors

## Future Enhancements

- Add support for custom user-defined weights
- Implement percentile-based scoring (e.g., top 10% get bonus points)
- Add sector-relative scoring (score relative to sector average)
- Support for time-weighted metrics (recent performance weighted higher)

