# Complete Setup Guide

## Prerequisites - What You Need to Install

### Required Software

1. **Docker Desktop** (includes Docker and Docker Compose)
   - **macOS**: Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
   - **Linux**: 
     ```bash
     # Install Docker
     curl -fsSL https://get.docker.com -o get-docker.sh
     sh get-docker.sh
     
     # Install Docker Compose
     sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
     sudo chmod +x /usr/local/bin/docker-compose
     ```
   - **Windows**: Download Docker Desktop from docker.com

2. **Git** (usually pre-installed)
   - Check if installed: `git --version`
   - If not: [git-scm.com/downloads](https://git-scm.com/downloads)

### Verify Installation

```bash
# Check Docker
docker --version
# Should show: Docker version 20.x.x or higher

# Check Docker Compose
docker compose version
# Should show: Docker Compose version v2.x.x or higher

# Check Git
git --version
```

## Step-by-Step: Running the Application

### Step 1: Navigate to Project Directory

```bash
cd /Users/sajal/Documents/FundA
```

### Step 2: Create Environment File (if not exists)

```bash
# Check if .env exists
ls -la .env

# If it doesn't exist, create it from example
cat > .env << EOF
DATABASE_URL=postgresql://postgres:password@db:5432/sectorview
SECRET_KEY=supersecret
ALCHEMY_ECHO=false
EOF
```

### Step 3: Start All Services

```bash
# Option 1: Using Make (recommended)
make dev

# Option 2: Using Docker Compose directly
docker-compose up --build
```

**What happens:**
- Builds Docker images for backend, frontend, and database
- Starts PostgreSQL database (port 5432)
- Starts FastAPI backend (port 8000)
- Starts React frontend (port 3000)
- Runs database migrations automatically

**Wait for:** You should see logs indicating all services are running. Look for:
- `Application startup complete` (backend)
- `Local: http://localhost:3000` (frontend)
- `database system is ready to accept connections` (database)

**Time:** First build takes 3-5 minutes. Subsequent starts are faster (30 seconds).

### Step 4: Ingest Sample Data

**Open a NEW terminal window** (keep the first one running with `docker-compose up`):

```bash
cd /Users/sajal/Documents/FundA

# Ingest the sample data
make ingest-sample
```

**Expected output:**
```
Successfully ingested 50 records from /app/sample_data/sector_time_series.csv
```

### Step 5: Compute Features and Forecasts

In the same new terminal:

```bash
make compute-features
```

**Expected output:**
```
INFO - Computed features for NIFTY_BANK on 2025-11-28
INFO - Computed features for NIFTY_IT on 2025-11-28
...
INFO - Generated forecast for NIFTY_BANK: UP
...
INFO - Computed features for 5 sectors
INFO - Generated forecasts for 5 sectors
```

### Step 6: Access the Application

Open your web browser and go to:

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Step 7: Verify It's Working

1. **Check Frontend**: 
   - You should see sector tiles (NIFTY_BANK, NIFTY_IT, etc.)
   - Each tile shows a sparkline chart and performance metrics
   - Click any tile to see detailed forecast

2. **Check Backend API**:
   ```bash
   curl http://localhost:8000/healthz
   # Should return: {"status":"healthy","database":"connected"}
   
   curl http://localhost:8000/api/v1/sectors
   # Should return JSON array of sectors
   ```

3. **Check Database**:
   ```bash
   docker compose exec db psql -U postgres -d sectorview -c "SELECT COUNT(*) FROM sector_time_series;"
   # Should show: count = 50
   ```

## Common Issues & Solutions

### Issue: Port Already in Use

**Error:** `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution:**
```bash
# Find what's using the port
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Stop the conflicting service or change ports in docker-compose.yml
```

### Issue: Docker Not Running

**Error:** `Cannot connect to the Docker daemon`

**Solution:**
- Start Docker Desktop application
- Wait for it to fully start (whale icon in system tray)

### Issue: No Data Showing

**Check:**
```bash
# 1. Verify data was ingested
docker compose logs backend | grep "ingested"

# 2. Check database
docker compose exec db psql -U postgres -d sectorview -c "SELECT sector_id, COUNT(*) FROM sector_time_series GROUP BY sector_id;"

# 3. Re-run ingestion if needed
make ingest-sample
make compute-features
```

### Issue: Frontend Shows "Cannot connect to API"

**Solution:**
```bash
# 1. Check backend is running
curl http://localhost:8000/healthz

# 2. Check backend logs
docker compose logs backend

# 3. Restart backend
docker compose restart backend
```

## Development Workflow

### Daily Development

```bash
# Start services (in one terminal)
make dev

# Run tests (in another terminal)
make test

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```

### Making Changes

1. **Backend changes**: Edit files in `backend/app/` - changes auto-reload
2. **Frontend changes**: Edit files in `frontend/src/` - Vite hot-reloads
3. **Database changes**: Create new migration:
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "description"
   docker compose exec backend alembic upgrade head
   ```

### Stopping Services

```bash
# Stop (keeps data)
docker compose down

# Stop and remove all data
make clean
```

## Next Steps for Development

### Immediate Next Steps

1. **Add More Sample Data**
   - Edit `sample_data/sector_time_series.csv`
   - Add more dates or sectors
   - Re-run: `make ingest-sample && make compute-features`

2. **Explore the API**
   - Visit http://localhost:8000/docs
   - Try the interactive API explorer
   - Test different endpoints

3. **Customize Forecast Rules**
   - Edit `backend/app/services/forecasts.py`
   - Modify the scoring logic
   - Test with: `make compute-features`

### Short-term Enhancements

1. **Add Real Data Source**
   - Implement `fetch_eod_from_nse()` in `backend/app/services/ingestion.py`
   - Set up scheduled ingestion (cron or Prefect)

2. **Improve UI**
   - Add more charts in `frontend/src/components/SectorDetail.tsx`
   - Enhance styling in `frontend/src/`
   - Add loading states and error handling

3. **Add More Features**
   - Implement FII/DII flow data integration
   - Add macro indicators (Brent, USD/INR)
   - Add sector constituents data

### Long-term Enhancements

1. **Machine Learning**
   - Replace rule-based forecast with LightGBM
   - Add SHAP explanations
   - Implement model training pipeline

2. **Infrastructure**
   - Set up TimescaleDB for better time-series performance
   - Add Airflow/Prefect for ETL scheduling
   - Implement caching with Redis

3. **Features**
   - User authentication
   - Watchlists and alerts
   - Historical forecast accuracy tracking
   - Export functionality (PDF reports)

## Useful Commands Reference

```bash
# Start services
make dev

# Stop services
docker compose down

# View logs
docker compose logs -f [service_name]

# Run tests
make test

# Access database shell
docker compose exec db psql -U postgres -d sectorview

# Run backend shell
docker compose exec backend bash

# Run frontend shell
docker compose exec frontend sh

# Rebuild specific service
docker compose build backend
docker compose up backend

# Check service status
docker compose ps

# View resource usage
docker stats
```

## Getting Help

- Check logs: `docker compose logs [service]`
- Review API docs: http://localhost:8000/docs
- Check health: `curl http://localhost:8000/healthz`
- Database queries: `docker compose exec db psql -U postgres -d sectorview`

