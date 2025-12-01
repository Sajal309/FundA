# Quick Start Guide

This guide will help you get SectorView up and running in minutes.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

## Step-by-Step Setup

### 1. Start the Services

```bash
# Build and start all services (database, backend, frontend)
make dev
# or
docker-compose up --build
```

This will:
- Start PostgreSQL database on port 5432
- Start FastAPI backend on port 8000
- Start React frontend on port 3000
- Run database migrations automatically

Wait for all services to be healthy (check logs: `docker compose logs`)

### 2. Ingest Sample Data

In a new terminal:

```bash
# Ingest sample sector time series data
make ingest-sample
# or
docker compose exec backend python -m app.services.ingestion --source /app/sample_data/sector_time_series.csv
```

You should see: `Successfully ingested X records from ...`

### 3. Compute Features and Forecasts

```bash
# Compute technical features and generate forecasts
make compute-features
# or
docker compose exec backend python -m app.services.compute_all
```

You should see logs indicating features and forecasts were computed for each sector.

### 4. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Verify Everything Works

1. Open http://localhost:3000 in your browser
2. You should see sector tiles with performance metrics
3. Click on a sector tile to see detailed forecast and chart
4. Check the forecast ribbon table for 3-month predictions

## Troubleshooting

### Services won't start
- Check if ports 3000, 8000, 5432 are available
- View logs: `docker compose logs`

### No data showing
- Verify ingestion completed: `docker compose logs backend | grep ingested`
- Check database: `docker compose exec db psql -U postgres -d sectorview -c "SELECT COUNT(*) FROM sector_time_series;"`
- Re-run ingestion if needed

### Frontend shows errors
- Check backend is running: `curl http://localhost:8000/healthz`
- Check browser console for errors
- Verify CORS settings in `backend/app/main.py`

### Features/Forecasts not computing
- Ensure you have at least 20 days of data per sector
- Check logs: `docker compose logs backend | grep -i feature`
- Re-run: `make compute-features`

## Next Steps

- Add more sample data to `sample_data/sector_time_series.csv`
- Explore the API at http://localhost:8000/docs
- Customize forecast rules in `backend/app/services/forecasts.py`
- Modify UI components in `frontend/src/components/`

## Development Commands

```bash
# Run tests
make test

# View backend logs
docker compose logs -f backend

# View frontend logs
docker compose logs -f frontend

# Access database
docker compose exec db psql -U postgres -d sectorview

# Stop all services
docker compose down

# Clean everything (including volumes)
make clean
```

