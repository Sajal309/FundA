# Quick Run Guide - Copy & Paste Commands

## First Time Setup (One-Time)

### 1. Install Docker Desktop
- Download from: https://www.docker.com/products/docker-desktop
- Install and start Docker Desktop
- Verify: `docker --version` should work

### 2. Create .env file (if needed)
```bash
cd /Users/sajal/Documents/FundA
cat > .env << EOF
DATABASE_URL=postgresql://postgres:password@db:5432/sectorview
SECRET_KEY=supersecret
ALCHEMY_ECHO=false
EOF
```

## Running the Application (Every Time)

### Terminal 1: Start Services
```bash
cd /Users/sajal/Documents/FundA
make dev
```
**Keep this terminal open!** Wait until you see:
- `Application startup complete` (backend)
- `Local: http://localhost:3000` (frontend)

### Terminal 2: Load Data
```bash
cd /Users/sajal/Documents/FundA

# Step 1: Ingest sample data
make ingest-sample

# Step 2: Compute features and forecasts
make compute-features
```

### Open Browser
- Go to: **http://localhost:3000**
- You should see sector tiles with data!

## Verification Commands

```bash
# Check if services are running
docker compose ps

# Check backend health
curl http://localhost:8000/healthz

# Check data in database
docker compose exec db psql -U postgres -d sectorview -c "SELECT COUNT(*) FROM sector_time_series;"

# View logs
docker compose logs -f backend
```

## Stopping

```bash
# Stop services (keeps data)
docker compose down

# Stop and remove all data
make clean
```

## Troubleshooting

```bash
# If ports are busy, check what's using them
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Restart a specific service
docker compose restart backend

# Rebuild if code changes don't work
docker compose up --build
```

## Next Steps After Running

1. ✅ **Explore the dashboard** at http://localhost:3000
2. ✅ **Try the API** at http://localhost:8000/docs
3. ✅ **Add more data** - edit `sample_data/sector_time_series.csv`
4. ✅ **Customize forecasts** - edit `backend/app/services/forecasts.py`
5. ✅ **Modify UI** - edit `frontend/src/components/`

