# SectorView - Indian Market Sector Analysis Dashboard

A single-page web dashboard that displays current NIFTY sector performance and 3-month forecasts for Indian markets.

## Features

- **Real-time Sector Performance**: View current EOD performance for all NIFTY sectors
- **3-Month Forecasts**: Rule-based predictions with probability distributions
- **Sector Drilldown**: Detailed timeseries charts, technical indicators (MA20/MA50/RSI), and top constituents
- **Explainable Forecasts**: Clear drivers behind each forecast

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy + PostgreSQL
- Alembic (migrations)
- Pandas/NumPy

### Frontend
- React + TypeScript
- Vite
- Tailwind CSS
- Recharts

### Infrastructure
- Docker + Docker Compose
- PostgreSQL 15

## Quick Start

### Prerequisites
- **Docker Desktop** (includes Docker and Docker Compose) - [Download here](https://www.docker.com/products/docker-desktop)
- Git (usually pre-installed)

**Verify installation:**
```bash
docker --version
docker compose version
git --version
```

### Quick Setup (5 minutes)

1. **Start all services:**
```bash
make dev
# or
docker-compose up --build
```
Wait for all services to start (first time: 3-5 minutes)

2. **In a NEW terminal, ingest sample data:**
```bash
cd /Users/sajal/Documents/FundA
make ingest-sample
```

3. **Compute features and forecasts:**
```bash
make compute-features
```

4. **Access the application:**
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

**📖 For detailed setup instructions, see [SETUP.md](SETUP.md)**

## Project Structure

```
sectorview/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── api/      # API routes
│   │   ├── db/       # Database models, schemas, CRUD
│   │   ├── services/ # Business logic (ingestion, features, forecasts)
│   │   └── config.py
│   ├── alembic/      # Database migrations
│   └── requirements.txt
├── frontend/         # React frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   ├── components/
│   │   └── api/
│   └── package.json
├── sample_data/      # Sample CSV and JSON data
├── docker-compose.yml
└── Makefile
```

## Environment Variables

See `.env.example` for required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Application secret key
- `ALCHEMY_ECHO`: SQLAlchemy query logging

## Development

### Running Tests
```bash
docker compose exec backend pytest
```

### Database Migrations
```bash
docker compose exec backend alembic upgrade head
```

### Manual Data Ingestion
```bash
docker compose exec backend python -m app.services.ingestion --source /app/sample_data/sector_time_series.csv
```

## API Endpoints

- `GET /api/v1/sectors` - List all sectors with current performance
- `GET /api/v1/sectors/{sector_id}/forecast` - Get 3-month forecast for a sector
- `GET /api/v1/sectors/{sector_id}/timeseries` - Get historical timeseries data
- `GET /api/v1/flows` - Get FII/DII flow data
- `GET /healthz` - Health check endpoint

See http://localhost:8000/docs for interactive API documentation.

## Forecast Logic

The MVP uses a rule-based forecasting system that considers:
- Momentum indicators (1-month returns)
- Moving averages (MA20 vs MA50)
- FII flows
- Macro factors (Brent crude, USD/INR)

See `backend/app/services/features.py` for implementation details.

## Testing

Run the test suite:
```bash
# Backend tests
docker compose exec backend pytest

# Run specific test file
docker compose exec backend pytest tests/test_forecasts.py -v
```

## Monitoring

See `monitoring.md` for recommended Prometheus metrics and Grafana dashboards (not implemented in MVP).

## Troubleshooting

### Database connection issues
- Ensure PostgreSQL container is running: `docker compose ps`
- Check database logs: `docker compose logs db`

### Frontend not loading
- Check if backend is accessible: `curl http://localhost:8000/healthz`
- Verify CORS settings in `backend/app/main.py`

### No data showing
- Ensure data ingestion completed successfully
- Check backend logs: `docker compose logs backend`
- Verify data in database: `docker compose exec db psql -U postgres -d sectorview -c "SELECT COUNT(*) FROM sector_time_series;"`

## Next Steps (Future Enhancements)

- [ ] Add FII/DII daily flows mapping by stock & sector
- [ ] Add option chain ingestion for derivatives signals
- [ ] Replace rule-based forecast with LightGBM classifier + SHAP explanations
- [ ] Add TimescaleDB for faster time-series storage
- [ ] Add Airflow/Prefect for reliable ETL scheduling
- [ ] Add user authentication, watchlists, and alerts

## License

MIT

