## ETL Runbook - SectorView MVP

This document explains how to run and troubleshoot the **daily ETL** pipeline for the MVP.

### 1. One‑time setup

1. Ensure Docker Desktop is running.
2. From the project root:

```bash
cd /Users/sajal/Documents/FundA
make dev
```

Wait until the backend and database containers are healthy.

### 2. Run the daily ETL (local demo)

From the project root:

```bash
./run_etl_local.sh
```

What this does (via `backend/app/run_daily_etl.py`):

- Ingests `sample_data/sector_time_series.csv` into `sector_time_series`.
- Computes features for all sectors into `sector_features`.
- Generates rule‑based forecasts into `sector_forecasts`.
- Writes a JSON summary under `logs/daily_run_YYYYMMDD.json`.

After a successful run you should see:

- Rows in `sector_time_series`, `sector_features`, `sector_forecasts`:

```bash
docker compose exec db psql -U postgres -d sectorview -c "SELECT COUNT(*) FROM sector_time_series;"
docker compose exec db psql -U postgres -d sectorview -c "SELECT COUNT(*) FROM sector_features;"
docker compose exec db psql -U postgres -d sectorview -c "SELECT COUNT(*) FROM sector_forecasts;"
```

- Non‑empty responses from the API:

```bash
curl http://localhost:8000/api/v1/sectors
curl http://localhost:8000/api/v1/sectors/NIFTY_BANK/forecast
```

### 3. Scheduling (MVP)

For now, ETL is triggered manually via `run_etl_local.sh`.
In a real deployment you can:

- Use `cron` on the host to run the script nightly.
- Or wrap `run_daily_etl()` inside a Prefect/ Airflow flow.

### 4. Troubleshooting

- **Backend not running**
  - Ensure `make dev` is running and containers are healthy:

    ```bash
    docker compose ps
    docker compose logs backend
    ```

- **ETL fails early / no summary file**
  - Re‑run with logs:

    ```bash
    docker compose exec backend python -m app.run_daily_etl
    docker compose logs backend | grep "Daily ETL"
    ```

- **No data in frontend**
  - Confirm the ETL finished successfully.
  - Check `GET /api/v1/sectors` and `GET /api/v1/sectors/{sector_id}/timeseries`.
  - Make sure you refreshed the dashboard at `http://localhost:3000`.

### 5. Next steps

Future milestones will extend the ETL to:

- Ingest FII/DII flows, macro data, options chains, and news.
- Compute richer feature sets (flows, macro sensitivities, sentiment).
- Add backtesting and monitoring around the daily run.


