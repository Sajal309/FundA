#!/bin/bash
# Daily script to refresh forecast data and regenerate forecasts
# Run this as part of your daily ETL pipeline

set -e

echo "🔄 Starting daily forecast data refresh..."

# Populate all forecast data for today
echo "📊 Populating forecast data..."
docker compose exec -T backend python3 -m app.scripts.populate_forecast_data --days 1

# Regenerate all forecasts
echo "🔮 Regenerating forecasts..."
docker compose exec -T backend python3 -c "
from app.db import database
from app.services import forecasts

db = database.SessionLocal()
try:
    count = forecasts.generate_forecasts_for_all_sectors(db)
    print(f'✅ Regenerated {count} forecasts')
finally:
    db.close()
"

echo "✅ Daily forecast refresh complete!"

